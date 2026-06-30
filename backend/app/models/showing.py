"""SQLAlchemy model: Showing (programmazione: film X cinema Y giorno Z, N orari)."""
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Showing(Base):
    __tablename__ = "showings"
    __table_args__ = (
        UniqueConstraint("film_id", "cinema_slug", "date", name="uq_showing_dedup"),
        Index("ix_showings_date", "date"),
        Index("ix_showings_film", "film_id"),
        Index("ix_showings_cinema", "cinema_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("films.id", ondelete="CASCADE"),
        nullable=False,
    )
    cinema_slug: Mapped[str] = mapped_column(
        String,
        ForeignKey("cinemas.slug", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    # times = JSON array serializzato, es: '["18:30","21:00"]'
    times: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    screen: Mapped[str | None] = mapped_column(String, nullable=True)
    buy_url: Mapped[str | None] = mapped_column(String, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    film: Mapped["Film"] = relationship(back_populates="showings")
    cinema: Mapped["Cinema"] = relationship(back_populates="showings")
