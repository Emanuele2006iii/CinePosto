"""
Report leggibile di movies.json — per capire cosa ha preso lo scraper.

Uso:
    python3 report.py                  # tutti i cinema, oggi
    python3 report.py --cinema uci     # solo UCI
    python3 report.py --date 2026-07-01
    python3 report.py --all-dates      # tutti i giorni in programmazione
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

MOVIES_JSON = Path(__file__).resolve().parent / "output" / "movies.json"

CINEMA_ORDER = ["postmodernissimo", "the-space-corciano", "uci-perugia"]


def load() -> tuple[list[dict], str]:
    with open(MOVIES_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("films", []), data.get("generated_at", "?")


def icon(val) -> str:
    return "✓" if val else "✗"


def print_film(film: dict, target_dates: set[str] | None) -> None:
    title = film.get("title", "?")
    genres = ", ".join(film.get("genres") or []) or "—"
    duration = film.get("duration") or "?"
    poster = icon(film.get("poster"))
    desc = icon(film.get("description"))
    director = film.get("director") or "—"

    print(f"  • {title}")
    print(f"    Generi: {genres}  |  Durata: {duration}  |  Regista: {director}")
    print(f"    Poster: {poster}  Descrizione: {desc}")

    showings = film.get("present_in", [])
    if not showings:
        print("    ⚠  Nessun orario")
        return

    # Raggruppa per cinema_slug e data
    by_cinema: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for s in showings:
        date = s.get("date", "?")
        if target_dates and date not in target_dates:
            continue
        slug = s.get("cinema_slug", "?")
        times = s.get("times", [])
        by_cinema[slug][date].extend(times)

    for slug in CINEMA_ORDER:
        if slug not in by_cinema:
            continue
        for date, times in sorted(by_cinema[slug].items()):
            times_sorted = sorted(set(times))
            print(f"    {date} [{slug}]: {', '.join(times_sorted) if times_sorted else '—'}")

    # Cinema non nell'ordine predefinito
    for slug, dates in by_cinema.items():
        if slug in CINEMA_ORDER:
            continue
        for date, times in sorted(dates.items()):
            times_sorted = sorted(set(times))
            print(f"    {date} [{slug}]: {', '.join(times_sorted)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cinema", help="Filtra per cinema slug (es: uci, postmodernissimo, the-space)")
    parser.add_argument("--date", help="Filtra per data (YYYY-MM-DD)")
    parser.add_argument("--all-dates", action="store_true", help="Mostra tutti i giorni")
    parser.add_argument("--active-only", action="store_true", default=True, help="Solo film in_programmazione (default)")
    parser.add_argument("--all-status", action="store_true", help="Include anche i film rimossi")
    args = parser.parse_args()

    if not MOVIES_JSON.exists():
        print(f"✗ movies.json non trovato: {MOVIES_JSON}")
        return

    films, generated_at = load()
    print(f"\n=== Report scraper — {generated_at} ===\n")

    # Determina date target
    from scraper.config import get_week_dates, today_local
    today = today_local().isoformat()
    if args.all_dates:
        target_dates = None  # tutti
    elif args.date:
        target_dates = {args.date}
    else:
        target_dates = {today}

    # Filtra per cinema se richiesto
    cinema_filter: str | None = None
    if args.cinema:
        slug_map = {
            "uci": "uci-perugia",
            "thespace": "the-space-corciano",
            "the-space": "the-space-corciano",
            "postmod": "postmodernissimo",
            "postmodernissimo": "postmodernissimo",
        }
        cinema_filter = slug_map.get(args.cinema.lower(), args.cinema.lower())

    # Raggruppa i film per cinema principale (primo showing)
    by_cinema: dict[str, list[dict]] = defaultdict(list)
    for film in films:
        status = film.get("status", "")
        if not args.all_status and status == "rimosso":
            continue

        showings = film.get("present_in", [])

        # Trova i cinema che mostrano questo film nelle date target
        cinema_slugs: set[str] = set()
        for s in showings:
            date = s.get("date", "")
            slug = s.get("cinema_slug", "?")
            if target_dates is None or date in target_dates:
                cinema_slugs.add(slug)

        if not cinema_slugs:
            continue  # film senza showing nelle date richieste

        if cinema_filter:
            if cinema_filter not in cinema_slugs:
                continue
            by_cinema[cinema_filter].append(film)
        else:
            for slug in cinema_slugs:
                by_cinema[slug].append(film)

    if not by_cinema:
        date_label = args.date or today
        print(f"Nessun film trovato per la data {date_label}.")
        if not args.all_dates:
            print("Prova con --all-dates per vedere tutta la programmazione.")
        return

    total = 0
    for slug in CINEMA_ORDER + [s for s in by_cinema if s not in CINEMA_ORDER]:
        if slug not in by_cinema:
            continue
        cinema_films = by_cinema[slug]
        print(f"{'─'*60}")
        print(f"  {slug.upper()}  ({len(cinema_films)} film)")
        print(f"{'─'*60}")
        for film in sorted(cinema_films, key=lambda f: f.get("title", "")):
            print_film(film, target_dates)
            print()
        total += len(cinema_films)

    date_label = f"il {args.date}" if args.date else ("tutte le date" if args.all_dates else f"oggi ({today})")
    print(f"Totale: {total} film programmati {date_label}\n")


if __name__ == "__main__":
    main()
