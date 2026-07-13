"""SQLAlchemy model: Film. PK = intera, dedup tramite UNIQUE(title_normalized, year)."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.showing import Showing


class Film(Base):
    """Opera cinematografica, deduplicata tra i cinema.

    PK artificiale intera + chiave naturale UNIQUE(title_normalized, year):
    il titolo grezzo è troppo fragile per fare da chiave (apostrofi tipografici,
    trattini, remake omonimi — decisione D3). Metadati arricchiti via Wikidata
    (D1): i campi nullable restano null quando l'arricchimento non trova nulla.
    """

    __tablename__ = "films"
    __table_args__ = (
        UniqueConstraint("title_normalized", "year", name="uq_film_title_year"),
        UniqueConstraint("wikidata_id", name="uq_film_wikidata"),
        Index("ix_film_title_normalized", "title_normalized"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    # title_normalized = versione lowercase senza punteggiatura, usata per dedup
    title_normalized: Mapped[str] = mapped_column(String, nullable=False)
    original_title: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genres: Mapped[str | None] = mapped_column(String, nullable=True)
    director: Mapped[str | None] = mapped_column(String, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String, nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    # wikidata_id = es. "Q97154362", utile per future re-importazioni di metadati
    wikidata_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    showings: Mapped[list["Showing"]] = relationship(
        back_populates="film",
        cascade="all, delete-orphan",
    )
