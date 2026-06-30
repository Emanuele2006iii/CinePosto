"""
Validazione qualità di movies.json e cinemas.json.

Uso (dalla root dello scraper):
    python3 validate_output.py

Exit code 0 = nessun errore critico, 1 = errori critici trovati.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
MOVIES_JSON = OUTPUT_DIR / "movies.json"
CINEMAS_JSON = OUTPUT_DIR / "cinemas.json"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")

ERRORS: list[str] = []
WARNINGS: list[str] = []


def _err(msg: str) -> None:
    ERRORS.append(msg)


def _warn(msg: str) -> None:
    WARNINGS.append(msg)


def validate_movies() -> dict:
    if not MOVIES_JSON.exists():
        _err(f"movies.json non trovato in {OUTPUT_DIR}")
        return {}

    with open(MOVIES_JSON, encoding="utf-8") as f:
        data = json.load(f)

    films = data.get("films", [])
    errors_in_json = data.get("errors", [])

    stats = {
        "total": len(films),
        "with_poster": 0,
        "with_description": 0,
        "with_genres": 0,
        "with_director": 0,
        "with_duration": 0,
        "with_showings": 0,
        "status_active": 0,
        "status_removed": 0,
        "errors_in_output": len(errors_in_json),
    }

    for i, film in enumerate(films):
        label = f"Film[{i}] '{film.get('title', '?')}'"

        # Campi obbligatori
        if not film.get("title"):
            _err(f"{label}: titolo mancante")
        if not film.get("title_normalized"):
            _warn(f"{label}: title_normalized mancante")

        # Status valido
        status = film.get("status", "")
        if status not in ("in_programmazione", "rimosso"):
            _warn(f"{label}: status inatteso '{status}'")
        elif status == "in_programmazione":
            stats["status_active"] += 1
        else:
            stats["status_removed"] += 1

        # Contatori opzionali
        if film.get("poster"):
            stats["with_poster"] += 1
        elif status == "in_programmazione":
            _warn(f"{label}: poster mancante (film attivo)")

        if film.get("description"):
            stats["with_description"] += 1
        if film.get("genres"):
            stats["with_genres"] += 1
        if film.get("director"):
            stats["with_director"] += 1
        if film.get("duration"):
            stats["with_duration"] += 1

        # Showings
        showings = film.get("present_in", [])
        if not showings and status == "in_programmazione":
            _err(f"{label}: nessun showing ma status=in_programmazione")
        if showings:
            stats["with_showings"] += 1

        for j, showing in enumerate(showings):
            slabel = f"{label} Showing[{j}]"
            date = showing.get("date", "")
            if not DATE_RE.match(date):
                _err(f"{slabel}: data non valida '{date}'")

            times = showing.get("times", [])
            if not times:
                _warn(f"{slabel}: nessun orario")
            for t in times:
                if not TIME_RE.match(str(t)):
                    _err(f"{slabel}: orario non valido '{t}'")

            if not showing.get("cinema"):
                _err(f"{slabel}: campo cinema mancante")
            if not showing.get("cinema_slug"):
                _warn(f"{slabel}: cinema_slug mancante")

    if errors_in_json:
        _warn(f"movies.json contiene {len(errors_in_json)} errori di scraping registrati")

    return stats


def validate_cinemas() -> None:
    if not CINEMAS_JSON.exists():
        _err(f"cinemas.json non trovato in {OUTPUT_DIR}")
        return

    with open(CINEMAS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    cinemas = data.get("cinemas", [])
    if not cinemas:
        _err("cinemas.json: lista cinema vuota")
        return

    for c in cinemas:
        name = c.get("name", "?")
        if not c.get("slug"):
            _err(f"Cinema '{name}': slug mancante")
        if not c.get("lat") or not c.get("lon"):
            _warn(f"Cinema '{name}': coordinate mancanti")
        if not c.get("website"):
            _warn(f"Cinema '{name}': website mancante")


def print_report(stats: dict) -> None:
    total = stats.get("total", 0)

    def pct(n: int) -> str:
        return f"{n}/{total} ({100*n//total if total else 0}%)"

    print("\n=== VALIDAZIONE OUTPUT SCRAPER ===\n")
    print(f"{'Film totali':<30} {total}")
    print(f"{'Attivi / Rimossi':<30} {stats.get('status_active', 0)} / {stats.get('status_removed', 0)}")
    print(f"{'Con showing':<30} {pct(stats.get('with_showings', 0))}")
    print(f"{'Con poster':<30} {pct(stats.get('with_poster', 0))}")
    print(f"{'Con descrizione':<30} {pct(stats.get('with_description', 0))}")
    print(f"{'Con generi':<30} {pct(stats.get('with_genres', 0))}")
    print(f"{'Con regista':<30} {pct(stats.get('with_director', 0))}")
    print(f"{'Con durata':<30} {pct(stats.get('with_duration', 0))}")
    print(f"{'Errori di scraping':<30} {stats.get('errors_in_output', 0)}")

    if WARNINGS:
        print(f"\n⚠  AVVISI ({len(WARNINGS)}):")
        for w in WARNINGS:
            print(f"   {w}")

    if ERRORS:
        print(f"\n✗  ERRORI CRITICI ({len(ERRORS)}):")
        for e in ERRORS:
            print(f"   {e}")
    else:
        print("\n✓  Nessun errore critico.")

    print()


if __name__ == "__main__":
    stats = validate_movies()
    validate_cinemas()
    print_report(stats)
    sys.exit(1 if ERRORS else 0)
