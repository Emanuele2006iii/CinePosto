"""Pydantic schemas Cinema — DTO API request/response."""
# Decisione D3: identificativo = slug (string), niente id intera.
# Backend è readonly (i dati vengono dallo scraper) → niente schemi Create/Update lato API.
#
# TODO schemi attesi:
#   from pydantic import BaseModel, ConfigDict
#
#   class CinemaOut(BaseModel):
#       model_config = ConfigDict(from_attributes=True)
#       slug:     str
#       name:     str
#       city:     str
#       address:  str
#       region:   str
#       lat:      float
#       lon:      float
#       website:  str | None = None
#       phone:    str | None = None
#
#   class CinemaWithCount(CinemaOut):
#       showings_count: int   # popolato dal service
