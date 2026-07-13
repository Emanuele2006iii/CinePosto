"""Pydantic schemas Film — DTO API response."""
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    # Solo per il linter: a runtime la forward reference è risolta da
    # FilmDetail.model_rebuild() in schemas/__init__.py (evita import circolare).
    from app.schemas.showing import ShowingOut


class FilmOut(BaseModel):
    """Versione 'card' — usata nelle liste (Home 'Film oggi', ricerca)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: int | None = None
    runtime_minutes: int | None = None
    genres: str | None = None            # CSV: "Drama,Thriller"
    poster_url: str | None = None


class FilmDetail(FilmOut):
    """Versione completa — usata su GET /film/{id} (schermata dettaglio)."""
    original_title: str | None = None
    director: str | None = None
    synopsis: str | None = None
    wikidata_id: str | None = None
    # Lista dei prossimi spettacoli. `ShowingOut` viene definito in schemas/showing.py:
    # usiamo forward reference (stringa) per evitare import circolare.
    showings: list["ShowingOut"] = []
