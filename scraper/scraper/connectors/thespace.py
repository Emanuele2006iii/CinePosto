"""The Space Cinema connector: OAuth2 REST API with CloakBrowser fallback."""
from __future__ import annotations

from datetime import datetime
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests

from scraper.config import (
    DEFAULT_USER_AGENT,
    THE_SPACE_AUTH_URL,
    THE_SPACE_BASE_URL,
    THE_SPACE_CINEMA_NAME,
    THE_SPACE_CINEMA_SLUG,
    THE_SPACE_CINEMA_URL,
    THE_SPACE_FILMS_URL,
)
from scraper.connectors.base import BaseConnector
from scraper.errors import make_error
from scraper.http import retry_request
from scraper.models import CinemaError, Film, ScrapeResult, Showing
from scraper.normalizer import normalize_genres, normalize_title

logger = logging.getLogger(__name__)


class TheSpaceConnector(BaseConnector):
    """Connettore The Space Corciano — API REST del sito, con fallback browser.

    Fonte primaria: l'API microservice del sito (token guest via POST vuoto
    all'endpoint auth, poi una chiamata films per data). Se l'API fallisce si
    degrada allo scraping HTML via CloakBrowser, che copre il solo giorno corrente.
    """

    @property
    def cinema_name(self) -> str:
        """Nome pubblico del cinema (da config)."""
        return THE_SPACE_CINEMA_NAME

    @property
    def cinema_slug(self) -> str:
        """Slug stabile del cinema (da config)."""
        return THE_SPACE_CINEMA_SLUG

    def scrape(self, today: str, dates: list[str] | None = None) -> ScrapeResult:
        """Prova l'API per tutte le date; su errore ripiega sul browser (solo oggi).

        Se falliscono entrambe le vie ritorna un ScrapeResult con il solo
        errore `scrape_fallback`: la run complessiva prosegue con gli altri cinema.
        """
        target_dates = dates or [today]
        try:
            return self._scrape_via_api(today, target_dates)
        except Exception as exc:
            logger.warning("The Space API failed, falling back to CloakBrowser: %s", exc)
            try:
                return self._scrape_via_browser(today)
            except Exception as browser_exc:
                logger.error("The Space CloakBrowser fallback also failed: %s", browser_exc, exc_info=True)
                return ScrapeResult(
                    errors=[
                        make_error(
                            self.cinema_name,
                            browser_exc,
                            "scrape_fallback",
                            url=THE_SPACE_CINEMA_URL,
                            detail=f"API failed: {exc}; Browser failed: {browser_exc}",
                        )
                    ]
                )

    def _scrape_via_api(self, today: str, dates: list[str]) -> ScrapeResult:
        """Percorso primario: una chiamata API per data, dedup dei film per titolo.

        Lo stesso film appare nella risposta di ogni data in cui è programmato:
        `seen_titles` accumula gli showings sul primo Film incontrato. Gli
        errori di parsing del singolo film non fermano il resto della risposta.
        """
        films: list[Film] = []
        errors: list[CinemaError] = []
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/json",
                "Referer": THE_SPACE_CINEMA_URL,
            }
        )

        try:
            # Empty POST body returns a guest Bearer token; the API requires it before any films endpoint
            auth_resp = retry_request("post", THE_SPACE_AUTH_URL, session, label="THESPACE", json={})
            logger.info("The Space auth status: %s", auth_resp.status_code)

            seen_titles: dict[str, Film] = {}

            for target_date in dates:
                films_url = f"{THE_SPACE_FILMS_URL}?showingDate={target_date}&includesSession=true&includeSessionAttributes=true"
                resp = retry_request("get", films_url, session, label="THESPACE")
                data = resp.json()

                api_films = data.get("result") or data.get("films") or []
                if isinstance(api_films, dict):
                    api_films = api_films.get("films") or api_films.get("items") or []

                for film_data in api_films:
                    try:
                        film = self._parse_api_film(film_data, target_date)
                        if not film:
                            continue
                        key = film.title_normalized
                        if key in seen_titles:
                            seen_titles[key].present_in.extend(film.present_in)
                        else:
                            seen_titles[key] = film
                            films.append(film)
                    except Exception as exc:
                        logger.warning("The Space parse film error: %s", exc)
                        errors.append(make_error(self.cinema_name, exc, "parse_api_film"))

        except Exception as exc:
            logger.error("The Space API scrape failed: %s", exc, exc_info=True)
            raise

        return ScrapeResult(films=films, errors=errors)

    def _parse_api_film(self, data: dict, today: str) -> Film | None:
        """Costruisce un Film dal JSON dell'API; None se manca il titolo.

        I nomi dei campi hanno più varianti (filmTitle/title, posterImageSrc/
        panelImageUrl...): si prova in ordine di affidabilità osservata.
        URL relativi risolti contro THE_SPACE_BASE_URL.
        """
        title = data.get("filmTitle") or data.get("title") or ""
        if not title:
            return None

        detail_url = data.get("filmUrl") or ""
        if detail_url and not detail_url.startswith("http"):
            detail_url = urljoin(THE_SPACE_BASE_URL, detail_url)
        if not detail_url:
            film_id = data.get("filmId") or ""
            slug = data.get("filmUrl", "").rstrip("/").split("/")[-1] if data.get("filmUrl") else film_id
            detail_url = f"{THE_SPACE_BASE_URL}/film/{slug}" if slug else THE_SPACE_CINEMA_URL

        poster = data.get("posterImageSrc") or data.get("panelImageUrl") or ""
        if poster and not poster.startswith("http"):
            poster = urljoin(THE_SPACE_BASE_URL, poster)

        description = data.get("synopsisShort") or data.get("synopsis") or ""
        running_time = data.get("runningTime")
        duration = f"{running_time} min" if running_time and not data.get("isDurationUnknown") else None

        genres = normalize_genres(data.get("genres"))

        director = (data.get("director") or "").strip() or None

        showings = self._parse_api_showing_groups(data, today, detail_url)

        return Film(
            title=title,
            title_normalized=normalize_title(title),
            present_in=showings,
            poster=poster if poster else None,
            description=description or None,
            genres=genres,
            duration=duration,
            director=director,
            source_poster=poster if poster else None,
        )

    def _parse_api_showing_groups(self, film_data: dict, today: str, detail_url: str) -> list[Showing]:
        """Converte i `showingGroups` dell'API (gruppo per data → sessions) in Showing.

        Un Showing per sessione (poi consolidati per data in fase di
        serializzazione). Date e orari arrivano ISO con timezone: vengono
        normalizzati a YYYY-MM-DD e HH:MM. Dagli `attributes` della sessione
        si ricavano lingua (attributeType == "Language") e varianti (3D, IMAX...).
        Sessioni senza orario riconoscibile vengono scartate.
        """
        showings: list[Showing] = []
        showing_groups = film_data.get("showingGroups") or []

        for group in showing_groups:
            if not isinstance(group, dict):
                continue

            group_date = group.get("date", "")
            try:
                parsed_date = datetime.fromisoformat(str(group_date).replace("Z", "+00:00"))
                date_str = parsed_date.strftime("%Y-%m-%d")
            except Exception:
                logger.warning("TheSpace failed to parse date %s, skipping group", group_date)
                continue

            sessions = group.get("sessions") or []

            for session in sessions:
                if not isinstance(session, dict):
                    continue

                show_time = session.get("startTime") or session.get("showTime") or ""
                time_str = ""
                if show_time:
                    try:
                        parsed = datetime.fromisoformat(str(show_time).replace("Z", "+00:00"))
                        time_str = parsed.strftime("%H:%M")
                    except Exception:
                        if isinstance(show_time, str) and re.match(r"\d{1,2}:\d{2}", show_time[:5]):
                            time_str = show_time[:5]

                if not time_str:
                    continue

                screen = session.get("screenName") or None

                language = None
                attrs: list[str] = []
                for attr in session.get("attributes") or []:
                    if isinstance(attr, dict):
                        name = attr.get("name") or attr.get("value") or ""
                        attr_type = attr.get("attributeType", "")
                        if name:
                            attrs.append(name)
                        if attr_type == "Language" and name and not language:
                            language = name

                showing = Showing(
                    cinema=self.cinema_name,
                    cinema_slug=self.cinema_slug,
                    date=date_str,
                    times=[time_str],
                    screen=screen,
                    source_url=detail_url,
                    language=language,
                    session_attributes=attrs,
                )
                showings.append(showing)

        return showings

    def _scrape_via_browser(self, today: str) -> ScrapeResult:
        """Fallback CloakBrowser: parsa le card HTML della pagina cinema.

        Copre solo il giorno corrente e meno metadati dell'API — è la modalità
        degradata, non quella di regime. Selettori CSS multipli per resistere
        ai piccoli restyling del sito.
        """
        from scraper.browser import fetch_page_html

        html = fetch_page_html(THE_SPACE_CINEMA_URL, wait_for=".showing-listing")
        soup = BeautifulSoup(html, "lxml")
        films: list[Film] = []
        errors: list[CinemaError] = []

        for card in soup.select(".showing-listing__list > li, .film-card, [data-test*='film']"):
            try:
                title_el = card.select_one("h2, h3, .film-title, [data-test*='title']")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                link_el = card.select_one("a[href*='/film/']")
                detail_url = link_el["href"] if link_el and link_el.get("href") else ""
                if detail_url and not detail_url.startswith("http"):
                    detail_url = urljoin(THE_SPACE_BASE_URL, detail_url)

                poster = None
                img = card.select_one("img")
                if img and img.get("src"):
                    poster = img["src"]
                    if not poster.startswith("http"):
                        poster = urljoin(THE_SPACE_BASE_URL, poster)

                times: list[str] = []
                for time_el in card.select("[data-test*='time'], .session-time, .showtime"):
                    t = time_el.get_text(strip=True)
                    if re.match(r"\d{1,2}:\d{2}", t):
                        times.append(t)

                showing = Showing(
                    cinema=self.cinema_name,
                    cinema_slug=self.cinema_slug,
                    date=today,
                    times=times,
                    source_url=detail_url or THE_SPACE_CINEMA_URL,
                )

                film = Film(
                    title=title,
                    title_normalized=normalize_title(title),
                    present_in=[showing],
                    source_poster=poster,
                )
                films.append(film)

            except Exception as exc:
                logger.warning("The Space browser parse error: %s", exc)

        return ScrapeResult(films=films, errors=errors)

    def fetch_film_detail(self, film_url: str) -> dict | None:
        """Recupera la sinossi dalla pagina film: prima con requests, poi via browser."""
        session = requests.Session()
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html"})
        try:
            resp = retry_request("get", film_url, session, label="THESPACE")
            soup = BeautifulSoup(resp.text, "lxml")
            result: dict = {}

            desc = soup.select_one("[data-test*='synopsis'], .synopsis, .film-description")
            if desc:
                result["description"] = desc.get_text(strip=True)

            return result
        except Exception:
            try:
                from scraper.browser import fetch_page_html

                html = fetch_page_html(film_url)
                soup = BeautifulSoup(html, "lxml")
                result: dict = {}
                desc = soup.select_one("[data-test*='synopsis'], .synopsis, .film-description")
                if desc:
                    result["description"] = desc.get_text(strip=True)
                return result
            except Exception as exc:
                logger.warning("The Space detail fetch failed for %s: %s", film_url, exc)
                return None
