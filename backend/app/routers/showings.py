"""REST endpoints /showings — programmazione."""
# Niente POST/PUT/DELETE: i showings sono popolati dal seed_from_json, non da utenti.
#
# TODO router atteso:
#   from datetime import date as date_
#   from fastapi import APIRouter, Depends
#   from sqlalchemy.orm import Session
#   from ..database import get_db
#   from ..repositories import showing_repo
#   from ..schemas.showing import ShowingDetail
#
#   router = APIRouter(prefix="/showings")
#
#   @router.get("", response_model=list[ShowingDetail])
#   def list_showings(
#       date: date_ | None = None,           # default oggi
#       cinema_slug: str | None = None,
#       film_id: int | None = None,
#       db: Session = Depends(get_db),
#   ):
#       """Filtri opzionali combinabili. Default: showings di oggi su tutti i cinema."""
#       ...
#
#   @router.get("/today", response_model=list[ShowingDetail])
#   def showings_today(db: Session = Depends(get_db)):
#       return showing_repo.list_by_date(db, date_.today())
