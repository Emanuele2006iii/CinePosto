"""SQLAlchemy model: Cinema (sala fisica). PK = slug stringa."""
from typing import TYPE_CHECKING

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    # Solo per il type-checker/linter: a runtime il forward reference "Showing"
    # viene risolto da SQLAlchemy, senza import circolare.
    from app.models.showing import Showing


class Cinema(Base):
    """Sala cinematografica fisica.

    PK = slug testuale (es. "postmodernissimo"): i cinema sono pochi e stabili,
    e lo slug è leggibile negli URL e nei log (decisione D3). Coordinate lat/lon
    obbligatorie: servono alla mappa (RF-03).
    """

    __tablename__ = "cinemas"

    slug: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False, default="Umbria")
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    showings: Mapped[list["Showing"]] = relationship(
        back_populates="cinema",
        cascade="all, delete-orphan",
    )
