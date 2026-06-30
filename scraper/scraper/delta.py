"""Delta merge: reconciles current run with previous output and manages film history."""
from __future__ import annotations

from datetime import datetime
import json
import logging

from scraper.config import HISTORY_DIR, MOVIES_JSON, REMOVAL_THRESHOLD_DAYS
from scraper.models import Film, Showing
from scraper.normalizer import title_key

logger = logging.getLogger(__name__)


def load_previous_movies() -> list[dict]:
    if not MOVIES_JSON.exists():
        return []
    try:
        with open(MOVIES_JSON, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("films", [])
    except Exception as exc:
        logger.warning("Failed to load previous movies.json: %s", exc)
        return []


def save_snapshot(today: str) -> None:
    if not MOVIES_JSON.exists():
        return
    try:
        snapshot_path = HISTORY_DIR / f"movies_{today}.json"
        import shutil

        shutil.copy2(MOVIES_JSON, snapshot_path)
        logger.info("Saved snapshot: %s", snapshot_path)
    except Exception as exc:
        logger.warning("Failed to save snapshot: %s", exc)


def merge_films(new_films: list[Film], previous_data: list[dict], today: str) -> list[Film]:
    prev_map: dict[str, dict] = {}
    for pf in previous_data:
        key = title_key(pf.get("title_normalized") or pf.get("title", ""))
        if key:
            prev_map[key] = pf

    merged: list[Film] = []
    seen_keys: set[str] = set()

    for film in new_films:
        key = title_key(film.title_normalized)
        seen_keys.add(key)

        prev = prev_map.get(key)
        if prev:
            existing_history = prev.get("history", [])

            old_showings = prev.get("present_in", [])
            new_showings_dicts = [
                {
                    "cinema": s.cinema,
                    "cinema_slug": s.cinema_slug,
                    "date": s.date,
                    "times": s.times,
                }
                for s in film.present_in
            ]

            if _showings_changed(old_showings, new_showings_dicts):
                film.history = existing_history + [
                    {"date": today, "action": "updated"}
                ]
            else:
                film.history = existing_history

            if film.status != "rimosso":
                film.status = "in_programmazione"

            if not film.poster and prev.get("poster"):
                film.poster = prev["poster"]
            if not film.description and prev.get("description"):
                film.description = prev["description"]

        else:
            film.history = [{"date": today, "action": "added"}]
            film.status = "in_programmazione"

        merged.append(film)

    for key, prev in prev_map.items():
        if key in seen_keys:
            continue

        prev_status = prev.get("status", "")
        prev_history = prev.get("history", [])

        removed_date = _last_removal_date(prev_history)
        if removed_date:
            days_since_removal = (
                datetime.strptime(today, "%Y-%m-%d")
                - datetime.strptime(removed_date, "%Y-%m-%d")
            ).days
        else:
            days_since_removal = 0

        prev_present = prev.get("present_in", [])
        last_date = ""
        for p in prev_present:
            if p.get("date", "") > last_date:
                last_date = p["date"]
        if last_date:
            days_since = (
                datetime.strptime(today, "%Y-%m-%d")
                - datetime.strptime(last_date, "%Y-%m-%d")
            ).days
        else:
            days_since = REMOVAL_THRESHOLD_DAYS + 1

        already_removed = prev_status == "rimosso"
        days_since_removal_val = days_since_removal if already_removed else 0

        if already_removed:
            if days_since_removal_val > REMOVAL_THRESHOLD_DAYS * 2:  # hard purge after 14 days: won't reappear
                logger.info("Purging old removed film: %s", prev.get("title"))
                continue
            film = _dict_to_film(prev)
            film.status = "rimosso"
            merged.append(film)
        elif days_since > REMOVAL_THRESHOLD_DAYS:
            film = _dict_to_film(prev)
            film.status = "rimosso"
            film.history = prev_history + [{"date": today, "action": "removed"}]
            merged.append(film)
        else:
            # Within grace period: keep in_programmazione with empty showings so the frontend
            # can still display the film without broken schedule data
            film = _dict_to_film(prev)
            film.status = "in_programmazione"
            film.present_in = []
            if not any(h.get("action") == "removed" for h in prev_history):
                film.history = prev_history + [{"date": today, "action": "removed"}]
            else:
                film.history = prev_history
            merged.append(film)

    removed_count = sum(1 for f in merged if f.status == "rimosso")
    if removed_count:
        logger.info("Removed films (filtered from output): %d", removed_count)
    return [
        f
        for f in merged
        if f.status != "rimosso" and any(s.times for s in f.present_in)
    ]


def _showings_changed(old: list[dict], new: list[dict]) -> bool:
    def _showing_key(s: dict) -> str:
        return f"{s.get('cinema_slug','')}:{s.get('date','')}:{','.join(s.get('times', []))}"

    old_keys = sorted(_showing_key(s) for s in old)
    new_keys = sorted(_showing_key(s) for s in new)
    return old_keys != new_keys


def _last_removal_date(history: list[dict]) -> str | None:
    for event in reversed(history):
        if event.get("action") == "removed":
            return event.get("date")
    return None


def _dict_to_film(data: dict) -> Film:
    """Reconstruct a Film from its serialized dict form (movies.json shape)."""
    showings = []
    for s in data.get("present_in", []):
        showings.append(
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
        )

    return Film(
        title=data.get("title", ""),
        title_normalized=data.get("title_normalized", ""),
        present_in=showings,
        poster=data.get("poster"),
        description=data.get("description"),
        genres=data.get("genres", []),
        status=data.get("status", "in_programmazione"),
        history=data.get("history", []),
        source_poster=data.get("source_poster"),
        duration=data.get("duration"),
        director=data.get("director"),
        original_title=data.get("original_title") or data.get("originalTitle"),
    )
