"""Pydantic schemas Showing — DTO API request/response."""
# Backend è readonly → niente Create/Update lato API.
# Nota: `times` arriva da DB come stringa JSON; va parsata in list[str] nel response.
#
# TODO schemi attesi:
#   from datetime import date as date_
#   from pydantic import BaseModel, ConfigDict, field_validator
#   import json
#
#   class ShowingOut(BaseModel):
#       model_config = ConfigDict(from_attributes=True)
#       id:        int
#       date:      date_
#       times:     list[str]                # ["18:30", "21:00"]
#       language:  str | None = None
#       screen:    str | None = None
#       buy_url:   str | None = None
#
#       @field_validator("times", mode="before")
#       def _parse_times(cls, v):
#           return json.loads(v) if isinstance(v, str) else v
#
#   class ShowingDetail(ShowingOut):
#       """Versione "denormalizzata" per evitare N+1 sul client."""
#       cinema: "CinemaOut"
#       film:   "FilmOut"
