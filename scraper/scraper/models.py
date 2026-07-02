"""Domain models (Film, Showing, CinemaError, ScrapeResult) and JSON serializers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import html
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from scraper.normalizer import normalize_duration

_ROME = ZoneInfo("Europe/Rome")


@dataclass
class Showing:
    cinema: str
    cinema_slug: str
    date: str
    times: list[str] = field(default_factory=list)
    screen: str | None = None
    source_url: str | None = None
    language: str | None = None
    session_attributes: list[str] = field(default_factory=list)


@dataclass
class Film:
    title: str
    title_normalized: str
    present_in: list[Showing] = field(default_factory=list)
    poster: str | None = None
    description: str | None = None
    genres: list[str] = field(default_factory=list)
    status: str = "in_programmazione"
    history: list[dict] = field(default_factory=list)
    source_poster: str | None = None
    duration: str | None = None
    director: str | None = None
    original_title: str | None = None
    year: int | None = None
    wikidata_id: str | None = None


@dataclass
class CinemaError:
    cinema: str
    timestamp: str
    exception: str
    phase: str
    url: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict:
        return {
            "cinema": self.cinema,
            "timestamp": self.timestamp,
            "exception": self.exception,
            "phase": self.phase,
            "url": self.url,
            "detail": self.detail,
        }


@dataclass
class ScrapeResult:
    films: list[Film] = field(default_factory=list)
    errors: list[CinemaError] = field(default_factory=list)


def _consolidate_showings(showings: list[Showing]) -> list[dict]:
    groups: dict[tuple, dict] = {}
    for s in showings:
        lang_key = s.language or ""
        screen_key = s.screen or ""
        attrs_key = ",".join(sorted(s.session_attributes))
        key = (s.cinema, s.cinema_slug, s.date, lang_key, screen_key, attrs_key)
        if key not in groups:
            groups[key] = {
                "cinema": s.cinema,
                "cinema_slug": s.cinema_slug,
                "date": s.date,
                "times": [],
                "screen": s.screen,
                "source_url": s.source_url,
                "language": s.language,
                "session_attributes": list(s.session_attributes),
            }
        g = groups[key]
        for t in s.times:
            if t and t not in g["times"]:
                g["times"].append(t)
        if s.source_url and not g["source_url"]:
            g["source_url"] = s.source_url
        for a in s.session_attributes:
            if a and a not in g["session_attributes"]:
                g["session_attributes"].append(a)
    for g in groups.values():
        g["times"].sort()
    results = []
    for g in groups.values():
        entry = {k: v for k, v in g.items() if v is not None and v != [] and v != ""}
        results.append(entry)
    return results


def _clean_poster(url: str | None) -> str | None:
    if not url:
        return None
    if "/_next/image" in url:
        parsed = urlparse(url)
        real = parse_qs(parsed.query).get("url", [None])[0]
        if real:
            return real
    return url


def film_to_dict(film: Film) -> dict:
    return {
        "title": html.unescape(film.title) if film.title else film.title,
        "title_normalized": html.unescape(film.title_normalized) if film.title_normalized else film.title_normalized,
        "poster": _clean_poster(film.poster),
        "description": html.unescape(film.description) if film.description else film.description,
        "genres": film.genres if film.genres else None,
        "status": film.status,
        "director": film.director,
        "original_title": film.original_title,
        "duration": normalize_duration(film.duration),
        "year": film.year,
        "wikidata_id": film.wikidata_id,
        "present_in": _consolidate_showings(film.present_in),
        "history": film.history,
    }


def cinemas_to_json(locations: dict) -> dict:
    return {
        "generated_at": datetime.now(_ROME).isoformat(),
        "cinemas": [{"slug": slug, **data} for slug, data in locations.items()],
    }


def films_to_json(films: list[Film]) -> dict:
    result = []
    for film in films:
        first_seen = next((h["date"] for h in film.history if h.get("action") == "added"), None)
        last_seen = next(
            (h["date"] for h in reversed(film.history) if h.get("action") in ("added", "updated")),
            first_seen,
        )
        result.append({
            "id": film.title_normalized,
            "title": html.unescape(film.title) if film.title else film.title,
            "title_normalized": film.title_normalized,
            "original_title": film.original_title,
            "poster": _clean_poster(film.poster),
            "description": html.unescape(film.description) if film.description else film.description,
            "genres": film.genres or [],
            "director": film.director,
            "duration": normalize_duration(film.duration),
            "year": film.year,
            "wikidata_id": film.wikidata_id,
            "status": film.status,
            "first_seen": first_seen,
            "last_seen": last_seen,
        })
    return {
        "generated_at": datetime.now(_ROME).isoformat(),
        "films": result,
    }


def showings_to_json(films: list[Film], date_from: str, date_to: str) -> dict:
    rows = []
    for film in films:
        for group in _consolidate_showings(film.present_in):
            rows.append({
                "film_id": film.title_normalized,
                **{k: v for k, v in group.items() if k != "cinema"},
            })
    return {
        "generated_at": datetime.now(_ROME).isoformat(),
        "date_from": date_from,
        "date_to": date_to,
        "showings": rows,
    }


def output_to_json(films: list[Film], errors: list[CinemaError], city: str = "Perugia") -> dict:
    return {
        "generated_at": datetime.now(_ROME).isoformat(),
        "city": city,
        "films": [film_to_dict(f) for f in films],
        "errors": [e.to_dict() for e in errors],
    }
