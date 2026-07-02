"""Entry point: orchestrates scraper run, deduplication, Wikidata enrichment, and JSON output."""
from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import sys
import time

from scraper.config import (
    CACHE_DIR,
    CINEMA_LOCATIONS,
    CINEMAS_JSON,
    CITY,
    FILMS_JSON,
    LOG_FORMAT,
    LOG_LEVEL,
    MOVIES_JSON,
    SCHEDULE_INTERVAL_HOURS,
    SCRAPER_LOG,
    SHOWINGS_JSON,
    get_week_dates,
    today_local,
)
from scraper.config import (
    SCRAPER_RETRY_DELAY as RETRY_DELAY,
)
from scraper.connectors.postmodernissimo import PostModernissimoConnector
from scraper.connectors.thespace import TheSpaceConnector
from scraper.connectors.uci import UCIConnector
from scraper.delta import load_previous_movies, merge_films, save_snapshot
from scraper.errors import write_errors
from scraper.metadata import enrich_film
from scraper.models import (
    CinemaError,
    Film,
    ScrapeResult,
    Showing,
    cinemas_to_json,
    film_to_dict,
    films_to_json,
    output_to_json,
    showings_to_json,
)
from scraper.normalizer import fuzzy_match

logger = logging.getLogger("cinema_scraper")


def _write_atomic(path, data: dict) -> None:
    """Write *data* as JSON to *path* using an atomic tmp-then-replace pattern."""
    tmp_path = str(path) + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(path))
        logger.info("Wrote %s", path)
    except Exception as exc:
        logger.error("Failed to write %s: %s", path, exc, exc_info=True)


def _save_cache(cinema_slug: str, films: list[Film]) -> None:
    try:
        cache_file = CACHE_DIR / f"{cinema_slug}.json"
        data = [film_to_dict(f) for f in films]
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("  Cache saved for %s (%d films)", cinema_slug, len(films))
    except Exception as exc:
        logger.warning("  Failed to save cache for %s: %s", cinema_slug, exc)


def _load_cache(cinema_slug: str) -> list[Film] | None:
    try:
        cache_file = CACHE_DIR / f"{cinema_slug}.json"
        if not cache_file.exists():
            return None
        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)
        films = []
        for d in data:
            showings_data = d.get("present_in", [])
            showings = [
                Showing(
                    cinema=s.get("cinema", ""),
                    cinema_slug=s.get("cinema_slug", ""),
                    date=s.get("date", ""),
                    times=s.get("times", []),
                    screen=s.get("screen"),
                    source_url=s.get("source_url"),
                    language=s.get("language"),
                    session_attributes=s.get("session_attributes", []),
                )
                for s in showings_data
            ]
            films.append(Film(
                title=d.get("title", ""),
                title_normalized=d.get("title_normalized", ""),
                present_in=showings,
                poster=d.get("poster"),
                description=d.get("description"),
                genres=d.get("genres", []),
                status=d.get("status", "in_programmazione"),
                director=d.get("director"),
                duration=d.get("duration"),
                source_poster=d.get("source_poster") or d.get("poster"),
                original_title=d.get("original_title") or d.get("originalTitle"),
                year=d.get("year"),
                wikidata_id=d.get("wikidata_id"),
            ))
        logger.info("  Cache loaded for %s (%d films)", cinema_slug, len(films))
        return films
    except Exception as exc:
        logger.warning("  Failed to load cache for %s: %s", cinema_slug, exc)
        return None


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(SCRAPER_LOG), encoding="utf-8"),
        ],
    )


def run_scraper() -> None:
    today = today_local().isoformat()
    week_dates = get_week_dates()
    logger.info("=== Cinema Scraper started (%s) ===", today)
    logger.info("Week dates: %s", week_dates)

    connectors = [
        PostModernissimoConnector(),
        TheSpaceConnector(),
        UCIConnector(),
    ]

    all_films: list[Film] = []
    all_errors = []
    failed_connectors: list = []
    cache_fallbacks: dict[str, list[Film]] = {}

    for connector in connectors:
        logger.info("Scraping %s ...", connector.cinema_name)
        try:
            result: ScrapeResult = connector.scrape(today, dates=week_dates)
            logger.info(
                "  %s: %d films, %d errors",
                connector.cinema_name,
                len(result.films),
                len(result.errors),
            )
            if result.films:
                _save_cache(connector.cinema_slug, result.films)
            all_films.extend(result.films)
            all_errors.extend(result.errors)
        except Exception as exc:
            logger.error(
                "  %s: SCRAPE FAILED - %s", connector.cinema_name, exc, exc_info=True
            )
            failed_connectors.append(connector)
            # Store cache for later — only use it if retry also fails
            cached = _load_cache(connector.cinema_slug)
            if cached:
                cache_fallbacks[connector.cinema_slug] = cached

            all_errors.append(
                CinemaError(
                    cinema=connector.cinema_name,
                    timestamp=datetime.now().isoformat(),
                    exception=type(exc).__name__,
                    phase="scrape",
                    detail=str(exc),
                )
            )

    if failed_connectors:
        logger.info("Retrying %d failed cinemas in %d seconds ...", len(failed_connectors), RETRY_DELAY)
        time.sleep(RETRY_DELAY)
        for connector in failed_connectors:
            logger.info("Retrying %s ...", connector.cinema_name)
            try:
                result: ScrapeResult = connector.scrape(today, dates=week_dates)
                logger.info(
                    "  %s (retry): %d films, %d errors",
                    connector.cinema_name,
                    len(result.films),
                    len(result.errors),
                )
                if result.films:
                    _save_cache(connector.cinema_slug, result.films)
                    all_films.extend(result.films)
                all_errors.extend(result.errors)
            except Exception as exc:
                logger.error(
                    "  %s (retry): STILL FAILED - %s", connector.cinema_name, exc
                )
                # Both attempts failed — fall back to stale cache
                cached = cache_fallbacks.get(connector.cinema_slug)
                if cached:
                    logger.info("  %s: using %d cached films as fallback", connector.cinema_name, len(cached))
                    all_films.extend(cached)

    logger.info("Deduplicating %d films ...", len(all_films))
    all_films = _deduplicate_films(all_films)

    logger.info("Enriching %d films with Wikidata ...", len(all_films))
    for film in all_films:
        try:
            enrich_film(film)
        except Exception as exc:
            logger.warning("Wikidata enrichment failed for '%s': %s", film.title, exc)

    logger.info("Merging with previous data ...")
    previous_data = load_previous_movies()
    merged_films = merge_films(all_films, previous_data, today)

    for film in merged_films:
        if not film.poster and film.source_poster:
            film.poster = film.source_poster

    output = output_to_json(merged_films, all_errors, CITY)

    # movies.json — stato interno: include history per il delta
    _write_atomic(MOVIES_JSON, output)

    # DB-ready: tabella films (id, title, poster, genres, director, duration, first_seen, last_seen)
    active_films = [f for f in merged_films if f.status == "in_programmazione"]
    _write_atomic(FILMS_JSON, films_to_json(active_films))

    # DB-ready: tabella showings (film_id FK, cinema_slug FK, date, times, screen, language)
    _write_atomic(SHOWINGS_JSON, showings_to_json(active_films, week_dates[0], week_dates[-1]))

    # cinemas.json — tabella cinemas (slug, name, lat, lon, website)
    _write_atomic(CINEMAS_JSON, cinemas_to_json(CINEMA_LOCATIONS))

    save_snapshot(today)
    write_errors(all_errors, today)

    try:
        from scraper.browser import close_browser

        close_browser()
    except Exception:
        pass

    active = sum(1 for f in merged_films if f.status == "in_programmazione")
    removed = sum(1 for f in merged_films if f.status == "rimosso")
    logger.info(
        "=== Scraper complete: %d active, %d removed, %d errors ===",
        active,
        removed,
        len(all_errors),
    )


def _deduplicate_films(films: list[Film]) -> list[Film]:
    result: list[Film] = []

    for film in films:
        found = False
        for existing in result:
            if fuzzy_match(existing.title_normalized, film.title_normalized):
                existing.present_in.extend(film.present_in)
                if not existing.poster and film.poster:
                    existing.poster = film.poster
                if not existing.description and film.description:
                    existing.description = film.description
                if not existing.genres and film.genres:
                    existing.genres = film.genres
                if not existing.director and film.director:
                    existing.director = film.director
                if not existing.duration and film.duration:
                    existing.duration = film.duration
                found = True
                break

        if not found:
            result.append(film)

    return result


def schedule() -> None:
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_scraper,
        "interval",
        hours=SCHEDULE_INTERVAL_HOURS,
        id="daily_scrape",
        next_run_time=datetime.now(),
    )
    logger.info("Scheduler started: runs every %d hours", SCHEDULE_INTERVAL_HOURS)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    setup_logging()
    import argparse

    parser = argparse.ArgumentParser(description="CinePosto Scraper — Perugia cinema scraper")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no scheduling)")
    # NB: in produzione preferire systemd timer + --once. --schedule resta per uso dev locale.
    parser.add_argument("--schedule", action="store_true", help="Run with APScheduler (every 24h, dev only)")
    args = parser.parse_args()

    if args.once or not args.schedule:
        run_scraper()
    else:
        schedule()
