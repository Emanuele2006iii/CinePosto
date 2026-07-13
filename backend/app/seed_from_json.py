"""Seed del database dai JSON prodotti dallo scraper.

Ordine di esecuzione (vincoli di FK):
1. cinemas.json  -> upsert per slug
2. films.json    -> upsert per (title_normalized, year), costruisci lookup {titolo_str_JSON: id_int_DB}
3. showings.json -> risolvi film_id (stringa) -> id (intero) via lookup; upsert per UNIQUE(film_id, cinema_slug, date)

Puo' essere eseguito:
- come script standalone: `python -m app.seed_from_json`
- via endpoint admin: POST /api/v1/admin/reimport
"""
from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
import re

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Cinema, Film, Showing  # noqa: F401
from app.repositories import cinema_repo, film_repo, showing_repo

logger = logging.getLogger(__name__)


def _parse_duration(raw: str | int | None) -> int | None:
    """Estrae i minuti da una duration tipo '109 min' o 109 (int).
    Ritorna None se non ci sono numeri riconoscibili.
    """
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    match = re.search(r"(\d+)", str(raw))
    return int(match.group(1)) if match else None


def _load_json(path: Path) -> dict:
    """Carica un JSON dello scraper; errore esplicito se il file manca.

    FileNotFoundError con path completo invece di un generico errore a valle:
    il file mancante è il failure mode più comune (scraper non ancora girato).
    """
    if not path.exists():
        raise FileNotFoundError(f"File JSON dello scraper mancante: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _seed_cinemas(db: Session, data: dict) -> int:
    """Upsert dei cinema. Ritorna il numero di record processati."""
    count = 0
    for entry in data.get("cinemas", []):
        cinema_repo.upsert(db, {
            "slug": entry["slug"],
            "name": entry["name"],
            "city": entry["city"],
            "address": entry["address"],
            "region": entry.get("region", "Umbria"),
            "lat": entry["lat"],
            "lon": entry["lon"],
            "website": entry.get("website"),
            "phone": entry.get("phone"),
        })
        count += 1
    return count


def _seed_films(db: Session, data: dict) -> tuple[int, dict[str, int]]:
    """Upsert dei film. Ritorna (numero, lookup titolo_JSON -> id_DB).

    Il JSON dello scraper usa il TITOLO come chiave; il DB usa un id intero.
    Costruiamo un dizionario di mappatura che sara' usato dal seed di showings
    per risolvere le FK.
    """
    lookup: dict[str, int] = {}
    count = 0
    for entry in data.get("films", []):
        # Il JSON scraper usa 'poster' invece che 'poster_url'.
        # 'genres' arriva come lista Python: la serializziamo in CSV per il model String.
        genres_raw = entry.get("genres")
        if isinstance(genres_raw, list):
            genres_csv = ",".join(str(g) for g in genres_raw) if genres_raw else None
        else:
            genres_csv = genres_raw

        # Il JSON scraper usa 'duration' (stringa "109 min"); qui ricaviamo il numero.
        runtime = _parse_duration(entry.get("duration") or entry.get("runtime_minutes"))

        payload = {
            "title": entry["title"],
            "original_title": entry.get("original_title"),
            "year": entry.get("year"),        # da Wikidata P577; null se il film non è stato arricchito
            "runtime_minutes": runtime,
            "genres": genres_csv,
            "director": entry.get("director"),
            "poster_url": entry.get("poster") or entry.get("poster_url"),
            "synopsis": entry.get("synopsis") or entry.get("description"),
            "wikidata_id": entry.get("wikidata_id"),   # null se il film non è su Wikidata
        }
        film = film_repo.upsert_from_scraper(db, payload)
        # entry['id'] e' il TITOLO stringa nel JSON scraper; lo usiamo come chiave.
        json_key = entry.get("id") or entry["title"]
        lookup[json_key] = film.id
        count += 1
    return count, lookup


def _seed_showings(db: Session, data: dict, film_lookup: dict[str, int]) -> int:
    """Upsert degli spettacoli, UNENDO gli orari per (film, cinema, data).

    Lo scraper puo' emettere piu' record per lo stesso (film, cinema, data) —
    tipicamente uno per sala (es. The Space: Odissea in 7 sale). Il DB pero' ha
    UNIQUE(film_id, cinema_slug, date): senza pre-aggregazione l'upsert terrebbe
    solo l'ultima sala, perdendo tutti gli altri orari. Qui li uniamo in un'unica
    riga. `screen` si conserva solo se proviene da un'unica sala (altrimenti e'
    ambiguo e viene omesso). Salta le righe orfane (film_id JSON non trovato).
    """
    aggregated: dict[tuple, dict] = {}
    skipped = 0
    for entry in data.get("showings", []):
        film_key = entry["film_id"]
        film_id = film_lookup.get(film_key)
        if film_id is None:
            skipped += 1
            logger.warning("Showing orfano (film JSON non trovato): %s", film_key)
            continue

        # Parsing data
        date_raw = entry["date"]
        showing_date = (
            datetime.strptime(date_raw, "%Y-%m-%d").date()
            if isinstance(date_raw, str) else date_raw
        )

        key = (film_id, entry["cinema_slug"], showing_date)
        times_raw = entry.get("times", [])
        times_list = times_raw if isinstance(times_raw, list) else [times_raw]

        agg = aggregated.get(key)
        if agg is None:
            agg = {
                "film_id": film_id,
                "cinema_slug": entry["cinema_slug"],
                "date": showing_date,
                "times": [],
                "screens": set(),
                "language": entry.get("language"),
                "buy_url": entry.get("buy_url") or entry.get("source_url"),
            }
            aggregated[key] = agg
        for t in times_list:
            if t and t not in agg["times"]:
                agg["times"].append(t)
        if entry.get("screen"):
            agg["screens"].add(entry["screen"])
        if not agg["language"] and entry.get("language"):
            agg["language"] = entry.get("language")
        if not agg["buy_url"]:
            agg["buy_url"] = entry.get("buy_url") or entry.get("source_url")

    count = 0
    for agg in aggregated.values():
        agg["times"].sort()
        screen = next(iter(agg["screens"])) if len(agg["screens"]) == 1 else None
        showing_repo.upsert(db, {
            "film_id": agg["film_id"],
            "cinema_slug": agg["cinema_slug"],
            "date": agg["date"],
            "times": json.dumps(agg["times"]),
            "language": agg["language"],
            "screen": screen,
            "buy_url": agg["buy_url"],
        })
        count += 1

    if skipped:
        logger.warning("%d showings saltati (film non risolvibile)", skipped)
    return count


def seed_from_json(db: Session, output_dir: Path) -> dict[str, int]:
    """Legge cinemas.json + films.json + showings.json e popola il DB.

    Args:
        db: sessione SQLAlchemy attiva.
        output_dir: cartella con i JSON dello scraper.

    Returns:
        dict con conteggi processati: {"cinemas": N, "films": N, "showings": N}.
    """
    logger.info("Seed da %s", output_dir)

    cinemas_data = _load_json(output_dir / "cinemas.json")
    films_data = _load_json(output_dir / "films.json")
    showings_data = _load_json(output_dir / "showings.json")

    try:
        n_cinemas = _seed_cinemas(db, cinemas_data)
        n_films, film_lookup = _seed_films(db, films_data)
        n_showings = _seed_showings(db, showings_data, film_lookup)
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info("Seed completato: %d cinema, %d film, %d showings",
                n_cinemas, n_films, n_showings)

    return {
        "cinemas": n_cinemas,
        "films": n_films,
        "showings": n_showings,
    }


def main():
    """Uso standalone: python -m app.seed_from_json"""
    from app.config import get_settings
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    settings = get_settings()
    output_dir = Path(settings.scraper_output_dir).resolve()

    # Crea tabelle se non esistono
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        stats = seed_from_json(db, output_dir)
        print(f"OK: {stats}")


if __name__ == "__main__":
    main()
