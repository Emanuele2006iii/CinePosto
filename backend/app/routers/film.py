"""REST endpoints /films — ricerca, dettaglio, programmazione corrente."""
# Decisione D3: path param `id` = intera (PK autoincrement).
#
# TODO router atteso:
#   from fastapi import APIRouter, Depends, HTTPException
#   from sqlalchemy.orm import Session
#   from ..database import get_db
#   from ..services import film_service
#   from ..schemas.film import FilmOut, FilmDetail
#
#   router = APIRouter(prefix="/films")
#
#   @router.get("/today", response_model=list[FilmOut])
#   def films_today(db: Session = Depends(get_db)):
#       """Films with at least one showing today."""
#       return film_service.films_today(db)
#
#   @router.get("/search", response_model=list[FilmOut])
#   def search(q: str, db: Session = Depends(get_db)):
#       """Substring search on title_normalized."""
#       return film_service.search_films(db, q)
#
#   @router.get("/{id}", response_model=FilmDetail)
#   def get_film(id: int, db: Session = Depends(get_db)):
#       film = film_service.get_detail(db, id)
#       if film is None: raise HTTPException(404, "Film not found")
#       return film
#
# Nota ordine route: /today e /search PRIMA di /{id}, altrimenti FastAPI le matcha come id.
