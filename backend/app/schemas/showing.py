"""Pydantic schemas Showing — DTO API response."""
from datetime import date as date_type
import json

from pydantic import BaseModel, ConfigDict, field_validator

from .cinema import CinemaOut
from .film import FilmOut


class ShowingOut(BaseModel):
    """Spettacolo base — usato in liste."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date_type
    times: list[str]                       # ["18:30", "21:00"]
    language: str | None = None
    screen: str | None = None
    buy_url: str | None = None

    @field_validator("times", mode="before")
    @classmethod
    def _parse_times(cls, v):
        """Converte `times` da stringa JSON del DB a lista Python.

        Nel DB il campo è salvato come '["18:30","21:00"]' (vedi Showing.times);
        l'API espone una vera lista. `mode="before"` = il parsing avviene PRIMA
        della validazione del tipo `list[str]`.
        """
        return json.loads(v) if isinstance(v, str) else v


class ShowingDetail(ShowingOut):
    """Versione denormalizzata: include cinema e film completi.
    Usata su GET /showings?date=... per evitare N+1 query lato client. """

    cinema: CinemaOut
    film: FilmOut
