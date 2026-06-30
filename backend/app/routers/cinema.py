"""REST endpoints /cinemas — sola lettura (i dati arrivano dallo scraper)."""
# Decisione D3: il path param è `slug` stringa, non `id` intera.
#
# TODO router atteso:
#   from datetime import date as date_
#   from fastapi import APIRouter, Depends, HTTPException
#   from sqlalchemy.orm import Session
#   from ..database import get_db
#   from ..services import cinema_service
#   from ..schemas.cinema import CinemaOut, CinemaWithCount
#   from ..schemas.showing import ShowingOut
#
#   router = APIRouter(prefix="/cinemas")
#
#   @router.get("", response_model=list[CinemaOut])
#   def list_cinemas(db: Session = Depends(get_db)):
#       return cinema_service.list_cinemas(db)
#
#   @router.get("/nearby", response_model=list[CinemaOut])
#   def cinemas_nearby(lat: float, lon: float, radius_km: float = 20, db: Session = Depends(get_db)):
#       return cinema_service.find_nearby(db, lat, lon, radius_km)
#
#   @router.get("/{slug}", response_model=CinemaWithCount)
#   def get_cinema(slug: str, db: Session = Depends(get_db)):
#       cinema = cinema_service.get_detail(db, slug)
#       if cinema is None: raise HTTPException(404, "Cinema not found")
#       return cinema
#
#   @router.get("/{slug}/showings", response_model=list[ShowingOut])
#   def cinema_showings(slug: str, date_from: date_ | None = None, date_to: date_ | None = None,
#                       db: Session = Depends(get_db)):
#       # default: oggi → +7 giorni
#       return cinema_service.get_schedule(db, slug, date_from, date_to)
