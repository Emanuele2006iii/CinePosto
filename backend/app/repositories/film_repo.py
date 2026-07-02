"""Data access layer: query su Film."""
import re
import unicodedata
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.film import Film
from app.models.showing import Showing


def normalize_title(title: str) -> str:
    """Trasforma un titolo in forma normalizzata per dedup.
    - lowercase
    - accenti rimossi (NFKD + drop combining chars)
    - punteggiatura -> spazio
    - spazi multipli collassati
    """
    nfkd = unicodedata.normalize("NFKD", title)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    no_punct = re.sub(r"[^\w\s]", " ", ascii_only.lower(), flags=re.UNICODE)
    collapsed = re.sub(r"\s+", " ", no_punct).strip()
    return collapsed


def get_by_id(db: Session, film_id: int) -> Film | None:
    return db.get(Film, film_id)


def get_by_natural_key(db: Session, title_normalized: str, year: int | None) -> Film | None:
    stmt = select(Film).where(
        Film.title_normalized == title_normalized,
        Film.year == year,
    )
    return db.scalars(stmt).one_or_none()


def search_by_title(db: Session, query: str, limit: int = 20) -> list[Film]:
    q_norm = normalize_title(query)
    stmt = (
        select(Film)
        .where(Film.title_normalized.like(f"%{q_norm}%"))
        .order_by(Film.title)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_in_programming(db: Session, date_from: date_type, date_to: date_type) -> list[Film]:
    stmt = (
        select(Film)
        .join(Showing, Showing.film_id == Film.id)
        .where(Showing.date >= date_from, Showing.date <= date_to)
        .order_by(Film.title)
        .distinct()
    )
    return list(db.scalars(stmt))


def upsert_from_scraper(db: Session, data: dict) -> Film:
    title = data["title"]
    title_normalized = normalize_title(title)
    year = data.get("year")

    film = get_by_natural_key(db, title_normalized, year)

    if film is None:
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
        for key in ("original_title", "runtime_minutes", "genres",
                    "director", "poster_url", "synopsis", "wikidata_id"):
            if data.get(key) is not None:
                setattr(film, key, data[key])

    db.flush()
    return film
