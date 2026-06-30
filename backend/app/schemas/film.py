"""Pydantic schemas Film — DTO API request/response."""
# Backend è readonly → niente Create/Update lato API.
#
# TODO schemi attesi:
#   from pydantic import BaseModel, ConfigDict
#
#   class FilmOut(BaseModel):
#       """Versione "card" — usata nelle liste."""
#       model_config = ConfigDict(from_attributes=True)
#       id:               int
#       title:            str
#       year:             int | None = None
#       runtime_minutes:  int | None = None
#       genres:           str | None = None
#       poster_url:       str | None = None
#
#   class FilmDetail(FilmOut):
#       """Versione completa — usata su GET /films/{id}."""
#       original_title:   str | None = None
#       director:         str | None = None
#       synopsis:         str | None = None
#       wikidata_id:      str | None = None
#       showings:         list["ShowingOut"] = []  # prossimi N showings
