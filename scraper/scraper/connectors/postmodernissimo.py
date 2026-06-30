"""PostModernissimo connector: parses RSC (Next.js) payload for film schedules."""
from __future__ import annotations

import html
import json
import logging
import re
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
import requests

from scraper.config import (
    DEFAULT_USER_AGENT,
    POSTMOD_CINEMA_NAME,
    POSTMOD_CINEMA_SLUG,
    POSTMOD_CINEMA_URL,
)
from scraper.connectors.base import BaseConnector
from scraper.errors import make_error
from scraper.http import retry_request
from scraper.models import CinemaError, Film, ScrapeResult, Showing
from scraper.normalizer import normalize_title

logger = logging.getLogger(__name__)


def _decode_html_entities(text: str) -> str:
    # Prima decodifica escape Unicode JSON (es. \u0026 -> &) poi entità HTML
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
    return html.unescape(text)


def _normalize(label: str | None) -> str | None:
    """Return the direct image URL if *label* is a Next.js image proxy link, else passthrough."""
    if not label:
        return None
    if "/_next/image" in label:
        parsed = urlparse(label)
        real_url = parse_qs(parsed.query).get("url", [None])[0]
        if real_url:
            return real_url
    return label



class PostModernissimoConnector(BaseConnector):
    @property
    def cinema_name(self) -> str:
        return POSTMOD_CINEMA_NAME

    @property
    def cinema_slug(self) -> str:
        return POSTMOD_CINEMA_SLUG

    def scrape(self, today: str, dates: list[str] | None = None) -> ScrapeResult:
        films: list[Film] = []
        errors: list[CinemaError] = []
        self._homepage_session = requests.Session()
        self._homepage_session.headers.update(
            {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "it-IT,it;q=0.9"}
        )

        try:
            resp = retry_request("get", POSTMOD_CINEMA_URL, self._homepage_session, label="POSTMOD")
            page_html = resp.text

            target_dates = set(dates) if dates else {today}
            target_date_ints = {d.replace("-", "") for d in target_dates}

            rsc_movies = self._parse_rsc_payload(page_html)
            html_cards = self._parse_film_cards(BeautifulSoup(page_html, "lxml"))

            if not rsc_movies and html_cards:
                logger.warning("POSTMOD RSC parsing returned 0 movies, falling back to HTML cards")
                return self._fallback_from_html(html_cards, today)

            poster_map = {c["slug"]: c.get("poster_url") for c in html_cards}

            for movie in rsc_movies:
                slug = movie["slug"]

                if self._is_event_stub(movie):
                    continue

                permalink = movie.get("permalink", "")
                shows = movie.get("shows", [])

                week_shows = [
                    s
                    for s in shows
                    if s.get("date", "") in target_date_ints
                    and s.get("orario")
                    and s.get("opzioni") != "noprog"
                ]

                if not week_shows:
                    continue

                date_groups: dict[str, list[str]] = {}
                for s in week_shows:
                    d = s["date"]
                    iso_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
                    if iso_date not in date_groups:
                        date_groups[iso_date] = []
                    time_val = s["orario"]
                    if time_val not in date_groups[iso_date]:
                        date_groups[iso_date].append(time_val)

                showings = []
                for iso_date in sorted(date_groups.keys()):
                    times = sorted(date_groups[iso_date])
                    showings.append(
                        Showing(
                            cinema=self.cinema_name,
                            cinema_slug=self.cinema_slug,
                            date=iso_date,
                            times=times,
                            source_url=permalink,
                        )
                    )

                if not showings:
                    continue

                details = movie.get("details", {})
                genres_raw = details.get("genere", "")
                genres = [g.strip() for g in re.split(r"[,/]", genres_raw) if g.strip()]
                poster_url = _normalize(poster_map.get(slug)) or self._extract_poster_url(details)
                description = movie.get("content", "")
                if not description and permalink:
                    detail = self.fetch_film_detail(permalink)
                    if detail:
                        description = detail.get("description", "")

                director_raw = details.get("regia") or None
                if director_raw:
                    director_raw = director_raw.strip().strip("()").strip() or None

                film = Film(
                    title=_decode_html_entities(movie["title"]),
                    title_normalized=normalize_title(_decode_html_entities(movie["title"])),
                    present_in=showings,
                    description=description or None,
                    director=director_raw,
                    duration=details.get("durata") or None,
                    genres=genres,
                    source_poster=poster_url,
                )
                films.append(film)

        except Exception as exc:
            logger.error("POSTMOD scrape failed: %s", exc, exc_info=True)
            errors.append(make_error(self.cinema_name, exc, "scrape", url=POSTMOD_CINEMA_URL))

        for film in films:
            self._reconcile_with_detail(film)

        return ScrapeResult(films=films, errors=errors)

    def _parse_rsc_payload(self, page_html: str) -> list[dict]:
        # Next.js RSC pages embed data as self.__next_f.push([1, "..."]) inline scripts.
        # The payload is a JSON-escaped string containing all film and schedule objects.
        pattern = r'self\.__next_f\.push\(\[1,"(.*?)"\]\)'
        matches = re.findall(pattern, page_html, re.DOTALL)
        if not matches:
            return []

        biggest = max(matches, key=len)
        unescaped = biggest.replace('\\"', '"').replace("\\\\", "\\")

        movie_re = re.compile(
            r'\{"id":(\d+),"title":"([^"]+)","slug":"([^"]+)","permalink":"([^"]+)"'
        )

        candidates_by_permalink: dict[str, dict] = {}

        for m in movie_re.finditer(unescaped):
            mid, title, slug, permalink = m.groups()
            if "/eventi/" in permalink:
                continue

            shows = self._extract_shows(unescaped, m.start())
            details = self._extract_details(unescaped, m.start())

            existing = candidates_by_permalink.get(permalink)
            if existing is None:
                candidates_by_permalink[permalink] = {
                    "id": mid,
                    "title": title,
                    "slug": slug,
                    "permalink": permalink,
                    "details": details,
                    "shows": list(shows),
                    "_stream_pos": m.start(),
                }
                continue

            # Accumulate shows from all occurrences of this permalink
            existing_shows = existing.setdefault("shows", [])
            existing_keys = {(s.get("date"), s.get("orario")) for s in existing_shows}
            for s in shows:
                key = (s.get("date"), s.get("orario"))
                if key not in existing_keys:
                    existing_shows.append(s)
                    existing_keys.add(key)
            if details and not existing.get("details"):
                existing["details"] = details
            if m.start() > existing.get("_stream_pos", 0):
                existing["_stream_pos"] = m.start()

        return [
            {k: v for k, v in m.items() if k != "_stream_pos"}
            for m in candidates_by_permalink.values()
            if m["shows"]
        ]

    _EVENT_HINTS = (
        "presentano",
        "ospiti",
        "rassegna",
        "ospite",
        "dal vivo",
        "live",
        "in concerto",
        "concerto",
    )

    def _is_event_stub(self, movie: dict) -> bool:
        title = (movie.get("title") or "").lower()
        permalink = (movie.get("permalink") or "").lower()
        if "/eventi/" in permalink:
            return True
        return any(h in title for h in self._EVENT_HINTS)

    def _extract_details(self, text: str, start: int) -> dict:
        details_idx = text.find('"details":{', start)
        if details_idx < 0 or details_idx - start > 3000:
            return {}

        details_start = text.find("{", details_idx)
        depth = 0
        i = details_start
        while i < len(text) and i < details_start + 5000:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1

        try:
            return json.loads(text[details_start : i + 1])
        except json.JSONDecodeError:
            return {}

    def _extract_shows(self, text: str, start: int) -> list[dict]:
        shows_idx = text.find('"shows":[', start)
        if shows_idx < 0 or shows_idx - start > 5000:
            return []

        arr_start = text.find("[", shows_idx)
        depth = 0
        i = arr_start
        while i < len(text) and i < arr_start + 20000:
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    break
            i += 1

        try:
            return json.loads(text[arr_start : i + 1])
        except json.JSONDecodeError:
            return []

    def fetch_film_detail(self, film_url: str) -> dict | None:
        if not film_url or not film_url.startswith("http"):
            return None
        try:
            session = requests.Session()
            session.headers.update(
                {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "it-IT,it;q=0.9"}
            )
            resp = retry_request("get", film_url, session, label="POSTMOD")
            soup = BeautifulSoup(resp.text, "lxml")
            # 1. Meta description
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                return {"description": meta["content"].strip()}
            # 2. Fallback: primo paragrafo significativo
            p = soup.select_one("article p, .film-content p, .description p")
            if p:
                text = p.get_text(strip=True)
                if text:
                    return {"description": text}
        except Exception as exc:
            logger.warning("POSTMOD failed to fetch detail %s: %s", film_url, exc)
        return None

    def _fetch_detail_shows(self, permalink: str) -> list[dict]:
        """Parsa gli show dal payload RSC della pagina di dettaglio di un singolo film.

        Restituisce la lista di show (formato `{"date": "YYYYMMDD", "orario": "HH:MM", ...}`)
        come sono nella home != dettaglio quando il sito ha cache diverse tra le due pagine.
        Restituisce [] se la pagina non è raggiungibile o non contiene show parsabili.
        """
        if not permalink or not permalink.startswith("http"):
            return []
        if "/eventi/" in permalink:
            return []  # dettaglio evento, non rilevante per film
        try:
            resp = retry_request("get", permalink, self._homepage_session, label="POSTMOD")
            movies_detail = self._parse_rsc_payload(resp.text)
            for m in movies_detail:
                permalink_in_detail = m.get("permalink", "")
                slug_in_detail = m.get("slug", "")
                target_slug = permalink.rstrip("/").split("/")[-1]
                if (
                    permalink_in_detail == permalink
                    or slug_in_detail == target_slug
                ):
                    return [s for s in m.get("shows", []) if s.get("orario")]
        except Exception as exc:
            logger.warning("POSTMOD detail-shows fetch failed %s: %s", permalink, exc)
        return []

    def _reconcile_with_detail(self, film: Film) -> None:
        # Detail page is the canonical source; homepage RSC can lag behind due to edge-cache staleness.
        # If the detail shows differ from homepage, replace present_in with detail data.
        # Falls back silently if the detail page is unreachable.
        if not film.present_in:
            return
        permalink = film.present_in[0].source_url
        if not permalink:
            return
        shows_detail = self._fetch_detail_shows(permalink)
        if not shows_detail:
            return  # dettaglio non disponibile: tieni homepage

        try:
            target_date_ints = {
                s.date.replace("-", "") for s in film.present_in
            }
        except Exception:
            return

        date_groups: dict[str, list[str]] = {}
        for s in shows_detail:
            d = s.get("date", "")
            if d not in target_date_ints:
                continue
            if s.get("opzioni") == "noprog":
                continue
            iso_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            orario = s.get("orario", "")
            if not orario:
                continue
            if iso_date not in date_groups:
                date_groups[iso_date] = []
            if orario not in date_groups[iso_date]:
                date_groups[iso_date].append(orario)

        if not date_groups:
            return  # dettaglio non ha show nella finestra: tieni homepage

        # Calcola la firma (set di (date, ora)) degli show in homepage vs dettaglio
        homepage_sig = {
            (s.date, tuple(s.times))
            for s in film.present_in
        }
        detail_sig = {
            (iso, tuple(sorted(times)))
            for iso, times in date_groups.items()
        }

        if homepage_sig == detail_sig:
            return  # concordano, no-op

        logger.info(
            "POSTMOD reconciliation: %s homepage!=detail, using detail (%d show)",
            film.title,
            sum(len(v) for v in date_groups.values()),
        )

        new_showings = []
        for iso_date in sorted(date_groups.keys()):
            new_showings.append(
                Showing(
                    cinema=self.cinema_name,
                    cinema_slug=self.cinema_slug,
                    date=iso_date,
                    times=sorted(date_groups[iso_date]),
                    source_url=permalink,
                )
            )
        film.present_in = new_showings

    def _extract_poster_url(self, details: dict) -> str | None:
        yt_cover = details.get("youtube_cover")
        if isinstance(yt_cover, dict):
            url = yt_cover.get("url")
            if url:
                return url
        return None

    def _parse_film_cards(self, soup: BeautifulSoup) -> list[dict]:
        cards: list[dict] = []
        seen_slugs: set[str] = set()
        for li in soup.select("ul.movie-container > li.movie-item"):
            try:
                link = li.select_one("a[href*='/films/']")
                if not link:
                    continue
                detail_url = link.get("href", "")
                slug = detail_url.rstrip("/").split("/")[-1]

                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)

                poster_url = None
                img = li.select_one("img")
                if img and img.get("src"):
                    poster_url = _normalize(img["src"])

                title_el = li.select_one("h2")
                title = title_el.get_text(strip=True) if title_el else slug

                director_el = li.select_one("p")
                director = director_el.get_text(strip=True) if director_el else None

                cards.append(
                    {
                        "slug": slug,
                        "poster_url": poster_url,
                        "title": title,
                        "director": director,
                        "detail_url": detail_url,
                    }
                )
            except Exception as exc:
                logger.warning("POSTMOD parse card error: %s", exc)
        return cards

    def _fallback_from_html(self, html_cards: list[dict], today: str) -> ScrapeResult:
        films: list[Film] = []
        for card in html_cards:
            slug = card["slug"]
            title = card.get("title", slug)
            poster = card.get("poster_url")
            director = card.get("director")

            film = Film(
                title=_decode_html_entities(title),
                title_normalized=normalize_title(_decode_html_entities(title)),
                present_in=[],
                description=None,
                director=director,
                duration=None,
                genres=[],
                source_poster=poster,
            )
            films.append(film)

        return ScrapeResult(films=films, errors=[])
