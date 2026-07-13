"""UCI Cinemas connector: undocumented Cloud Run programming API."""
from __future__ import annotations

import html
import logging
import re

import requests

from scraper.config import (
    DEFAULT_USER_AGENT,
    UCI_BASE_URL,
    UCI_CINEMA_NAME,
    UCI_CINEMA_SLUG,
    UCI_PROGRAMMING_URL,
)
from scraper.connectors.base import BaseConnector
from scraper.errors import make_error
from scraper.http import retry_request
from scraper.models import CinemaError, Film, ScrapeResult, Showing
from scraper.normalizer import normalize_genres, normalize_title

logger = logging.getLogger(__name__)


def _strip_html(text: str) -> str:
    """Rimuove i tag HTML dalle descrizioni (l'API UCI le fornisce come HTML)."""
    return re.sub(r"<[^>]+>", "", html.unescape(text)).strip()


class UCIConnector(BaseConnector):
    """Connettore UCI Perugia — API Cloud Run non documentata (reverse-engineered).

    L'endpoint programming/{date} è stato ricavato dal traffico XHR del sito:
    può cambiare senza preavviso a ogni redeploy di UCI (rischio R-01 del risk
    assessment). Niente fallback browser: il sito è dietro protezioni anti-bot
    aggressive, l'API è l'unica via praticabile.
    """

    @property
    def cinema_name(self) -> str:
        """Nome pubblico del cinema (da config)."""
        return UCI_CINEMA_NAME

    @property
    def cinema_slug(self) -> str:
        """Slug stabile del cinema (da config)."""
        return UCI_CINEMA_SLUG

    def scrape(self, today: str, dates: list[str] | None = None) -> ScrapeResult:
        """Interroga l'API programming per ogni data richiesta."""
        target_dates = dates or [today]
        return self._scrape_via_programming(today, target_dates)

    def _scrape_via_programming(self, today: str, dates: list[str]) -> ScrapeResult:
        """Una chiamata API per data; dedup dei film per titolo tra le date.

        L'API ritorna l'intero catalogo del cinema: il flag `not_today` marca i
        film senza proiezioni nella data richiesta e va filtrato. L'errore su
        una singola data non ferma le altre.
        """
        films: list[Film] = []
        seen_titles: dict[str, Film] = {}
        errors: list[CinemaError] = []
        session = requests.Session()
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"})

        for target_date in dates:
            url = UCI_PROGRAMMING_URL.format(date=target_date)
            try:
                resp = retry_request("get", url, session, label="UCI")
                data = resp.json()
                api_movies = data.get("data", [])
                logger.info("UCI programming API returned %d movies for %s", len(api_movies), target_date)

                for movie_data in api_movies:
                    try:
                        # UCI returns all films in the catalogue; not_today flags those without today's screenings
                        if movie_data.get("not_today") is True:
                            continue
                        film = self._parse_programming_movie(movie_data, target_date)
                        if film:
                            key = film.title_normalized
                            if key in seen_titles:
                                seen_titles[key].present_in.extend(film.present_in)
                            else:
                                seen_titles[key] = film
                                films.append(film)
                    except Exception as exc:
                        logger.warning("UCI parse programming movie error: %s", exc)
                        errors.append(make_error(self.cinema_name, exc, "parse_programming_movie"))

            except Exception as exc:
                logger.error("UCI programming API scrape failed for %s: %s", target_date, exc, exc_info=True)
                errors.append(make_error(self.cinema_name, exc, "scrape", url=url))

        return ScrapeResult(films=films, errors=errors)

    def _parse_programming_movie(self, data: dict, today: str) -> Film | None:
        """Costruisce un Film dal JSON dell'API; None se senza titolo o senza showings.

        L'API non fornisce regista né durata (li completa Wikidata a valle).
        Poster accettato solo se URL assoluto.
        """
        title = data.get("title") or ""
        if not title:
            return None

        slug = data.get("slug") or ""
        detail_url = f"{UCI_BASE_URL}/film/{slug}/" if slug else UCI_BASE_URL

        poster = data.get("poster") or data.get("top_image") or ""
        if poster and not poster.startswith("http"):
            poster = ""

        genres = normalize_genres(data.get("genres"))

        description = data.get("description") or ""
        if description:
            description = _strip_html(description)

        showings = self._build_showings_from_screens(data.get("screens", []), today, detail_url)

        if not showings:
            return None

        return Film(
            title=title,
            title_normalized=normalize_title(title),
            present_in=showings,
            poster=poster or None,
            description=description or None,
            genres=genres,
            duration=None,
            director=None,
            source_poster=poster or None,
        )

    def _build_showings_from_screens(
        self, screens: list, today: str, detail_url: str
    ) -> list[Showing]:
        """Appiattisce la struttura annidata `screens` dell'API in Showing.

        Struttura sorgente: lista di gruppi → {formato: [varianti]} → variante
        con lingua, sala e `performances` (una per orario). Si tengono solo le
        performance del giorno richiesto; il formato (es. "3D") finisce in
        session_attributes quando non coincide col nome della sala.
        """
        showings: list[Showing] = []

        for screen_group in screens:
            if not isinstance(screen_group, dict):
                continue

            for fmt, variants in screen_group.items():
                if not isinstance(variants, list):
                    continue

                for variant in variants:
                    if not isinstance(variant, dict):
                        continue

                    lang_obj = variant.get("language") or {}
                    language = lang_obj.get("name") if isinstance(lang_obj, dict) else None

                    screen_obj = variant.get("screen") or {}
                    screen_name = screen_obj.get("name") if isinstance(screen_obj, dict) else fmt

                    performances = variant.get("performances") or []
                    times = []
                    for perf in performances:
                        if not isinstance(perf, dict):
                            continue
                        perf_day = perf.get("day", "")
                        if perf_day and perf_day != today:
                            continue
                        start = perf.get("actual_start_at") or ""
                        if start:
                            times.append(start)

                    times.sort()

                    showings.append(
                        Showing(
                            cinema=self.cinema_name,
                            cinema_slug=self.cinema_slug,
                            date=today,
                            times=times,
                            screen=screen_name,
                            source_url=detail_url,
                            language=language,
                            session_attributes=[fmt] if fmt and fmt != screen_name else [],
                        )
                    )

        return showings

    def fetch_film_detail(self, film_url: str) -> dict | None:
        """Non implementato per UCI: l'API programming contiene già la descrizione."""
        return None
