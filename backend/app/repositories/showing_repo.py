"""Data access layer: query su Showing (spettacoli)."""
from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.showing import Showing


def get_by_id(db: Session, showing_id: int) -> Showing | None:
    """Ritorna lo spettacolo con la PK data, o None se non esiste."""
    return db.get(Showing, showing_id)


def list_by_date(db: Session, target_date: date_type) -> list[Showing]:
    """Tutti gli spettacoli di una data specifica, con Film e Cinema pre-caricati.
    Il `joinedload` evita il classico problema N+1: senza, l'ORM farebbe
    1 query per la lista + N query per caricare cinema e film di ognuno.
    Con joinedload → 1 query JOIN sola.
    """
    stmt = (
        select(Showing)
        .options(joinedload(Showing.film), joinedload(Showing.cinema))
        .where(Showing.date == target_date)
        .order_by(Showing.date)
    )
    return list(db.scalars(stmt))


def list_by_date_range(
    db: Session, date_from: date_type, date_to: date_type
) -> list[Showing]:
    """Spettacoli nel range di date (estremi inclusi), con Film e Cinema pre-caricati."""
    stmt = (
        select(Showing)
        .options(joinedload(Showing.film), joinedload(Showing.cinema))
        .where(Showing.date >= date_from, Showing.date <= date_to)
        .order_by(Showing.date)
    )
    return list(db.scalars(stmt))


def list_by_cinema_in_range(
    db: Session, cinema_slug: str, date_from: date_type, date_to: date_type
) -> list[Showing]:
    """Programmazione di un singolo cinema nel range di date (estremi inclusi).

    Eager loading del solo Film: il Cinema è già noto al chiamante (è il filtro).
    """
    stmt = (
        select(Showing)
        .options(joinedload(Showing.film))   # solo film, cinema noto
        .where(
            Showing.cinema_slug == cinema_slug,
            Showing.date >= date_from,
            Showing.date <= date_to,
        )
        .order_by(Showing.date)
    )
    return list(db.scalars(stmt))


def list_by_film(
    db: Session, film_id: int, from_date: date_type
) -> list[Showing]:
    """Prossimi spettacoli di un dato film a partire da una data. Include cinema."""
    stmt = (
        select(Showing)
        .options(joinedload(Showing.cinema))
        .where(Showing.film_id == film_id, Showing.date >= from_date)
        .order_by(Showing.date)
    )
    return list(db.scalars(stmt))


def count_by_cinema(db: Session, cinema_slug: str) -> int:
    """Numero di spettacoli attivi (futuri) per un cinema. Usato in CinemaWithCount."""
    # COUNT eseguito dal DB: evita di caricare tutte le righe solo per contarle
    stmt = select(func.count()).select_from(Showing).where(
        Showing.cinema_slug == cinema_slug,
        Showing.date >= date_type.today(),
    )
    return db.scalar(stmt)


def upsert(db: Session, data: dict) -> Showing:
    """Insert or update per Showing. Usato dal seed.
    UNIQUE key = (film_id, cinema_slug, date).
    """
    stmt = select(Showing).where(
        Showing.film_id == data["film_id"],
        Showing.cinema_slug == data["cinema_slug"],
        Showing.date == data["date"],
    )
    showing = db.scalars(stmt).one_or_none()

    if showing is None:
        showing = Showing(**data)
        db.add(showing)
    else:
        # Aggiorna orari, lingua, sala, url — questi cambiano tra scraping.
        for key in ("times", "language", "screen", "buy_url"):
            if key in data:
                setattr(showing, key, data[key])

    db.flush()
    return showing
