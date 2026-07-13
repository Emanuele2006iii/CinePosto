"""Data access layer: query su Film."""
from datetime import date as date_type
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film
from app.models.showing import Showing


def normalize_title(title: str) -> str:
    """Trasforma un titolo in forma normalizzata per dedup.
    Es: 'Ricchi…da morire – Delitti in famiglia' → 'ricchi da morire delitti in famiglia'
    Regole:
    - lowercase
    - accenti rimossi (NFKD + drop combining chars)
    - punteggiatura → spazio
    - spazi multipli collassati
    """
    nfkd = unicodedata.normalize("NFKD", title)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    no_punct = re.sub(r"[^\w\s]", " ", ascii_only.lower(), flags=re.UNICODE)
    collapsed = re.sub(r"\s+", " ", no_punct).strip()
    return collapsed


def get_by_id(db: Session, film_id: int) -> Film | None:
    """Ritorna il film con la PK data, o None se non esiste."""
    return db.get(Film, film_id)


def get_by_natural_key(
    db: Session, title_normalized: str, year: int | None
) -> Film | None:
    """Cerca per la UNIQUE key (title_normalized, year). Usato dal seed."""
    stmt = select(Film).where(
        Film.title_normalized == title_normalized,
        Film.year == year,
    )
    return db.scalars(stmt).one_or_none()


def search_by_title(db: Session, query: str, limit: int = 20) -> list[Film]:
    """Ricerca 'contains' sul titolo normalizzato."""
    q_norm = normalize_title(query)
    stmt = (
        select(Film)
        .where(Film.title_normalized.like(f"%{q_norm}%"))
        .order_by(Film.title)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_in_programming(
    db: Session, date_from: date_type, date_to: date_type
) -> list[Film]:
    """Film con almeno uno spettacolo tra date_from e date_to (inclusi).
    JOIN con showings + DISTINCT per evitare duplicati.
    """
    stmt = (
        select(Film)
        .join(Showing, Showing.film_id == Film.id)
        .where(Showing.date >= date_from, Showing.date <= date_to)
        .order_by(Film.title)
        .distinct()
    )
    return list(db.scalars(stmt))


def upsert_from_scraper(db: Session, data: dict) -> Film:
    """Insert or update per Film. Usato dal seed_from_json.

    Il JSON scraper NON ha `title_normalized` né `year` come chiave —
    li ricaviamo qui. Torna sempre un Film con `.id` popolato (serve per FK).
    """
    title = data["title"]
    title_normalized = normalize_title(title)
    year = data.get("year")

    film = get_by_natural_key(db, title_normalized, year)

    if film is None:
        # Nuovo film — insert
        film = Film(
            title=title,
            title_normalized=title_normalized,
            original_title=data.get("original_title"),
            year=year,
            runtime_minutes=data.get("runtime_minutes"),
            genres=data.get("genres"),
            director=data.get("director"),
            poster_url=data.get("poster_url"),
            synopsis=data.get("synopsis"),
            wikidata_id=data.get("wikidata_id"),
        )
        db.add(film)
    else:
        # Esiste — aggiorna solo i campi NON null nel JSON (i null non sovrascrivono).
        # Utile se Wikidata inizialmente non aveva la sinossi e poi la trova.
        for key in ("original_title", "runtime_minutes", "genres",
                    "director", "poster_url", "synopsis", "wikidata_id"):
            if data.get(key) is not None:
                setattr(film, key, data[key])

    db.flush()   # forza l'assegnazione dell'id (serve al seed di showings)
    return film
