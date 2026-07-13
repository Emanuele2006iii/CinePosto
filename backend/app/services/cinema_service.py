"""Business logic per Cinema.
I service orchestrano i repository; NON toccano direttamente il DB.
Restituiscono oggetti Model (o tuple), NON schemi Pydantic (quello lo fa il
router).
"""
from sqlalchemy.orm import Session

from app.models.cinema import Cinema
from app.repositories import cinema_repo, showing_repo


def list_cinemas(db: Session) -> list[Cinema]:
    """Ritorna tutti i cinema (ordinati per nome)."""
    return cinema_repo.list_all(db)


def get_cinema(db: Session, slug: str) -> Cinema | None:
    """Ritorna un cinema per slug, o None se non trovato."""
    return cinema_repo.get_by_slug(db, slug)


def get_cinema_with_count(db: Session, slug: str) -> tuple[Cinema, int] | None:
    """Cinema + numero di spettacoli futuri.
    Usato dall'endpoint dettaglio; il router poi costruisce lo schema
    `CinemaWithCount` combinando i due.
    """
    cinema = cinema_repo.get_by_slug(db, slug)
    if cinema is None:
        return None
    count = showing_repo.count_by_cinema(db, slug)
    return cinema, count
