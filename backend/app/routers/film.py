"""Endpoint REST per Film."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import FilmDetail, FilmOut, ShowingOut
from app.services import film_service

router = APIRouter(prefix="/film", tags=["film"])


@router.get("/oggi", response_model=list[FilmOut])
def films_today(db: Session = Depends(get_db)):
    """Film con almeno uno spettacolo oggi. Home 'Film oggi'."""
    return film_service.get_films_today(db)


@router.get("/settimana", response_model=list[FilmOut])
def films_this_week(db: Session = Depends(get_db)):
    """Film in programmazione da oggi ai prossimi 7 giorni."""
    return film_service.get_films_this_week(db)


@router.get("/search", response_model=list[FilmOut])
def search_films(
    q: str = Query(..., min_length=2, description="Testo da cercare nel titolo"),
    limit: int = Query(20, ge=1, le=100, description="Numero massimo di risultati"),
    db: Session = Depends(get_db),
):
    """Ricerca film per titolo (case-insensitive, ignora
punteggiatura/accenti)."""
    return film_service.search_films(db, q, limit=limit)


# ⚠️  /oggi e /settimana e /search vanno DEFINITI PRIMA di /{film_id}!
# Altrimenti FastAPI interpreta "oggi" come film_id e cerca di castarlo a int (422).
@router.get("/{film_id}", response_model=FilmDetail)
def get_film(film_id: int, db: Session = Depends(get_db)):
    """Dettaglio film + prossimi spettacoli (denormalizzato)."""
    result = film_service.get_film_detail(db, film_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Film non trovato")
    film, upcoming = result
    return FilmDetail(
        **film.__dict__,
        showings=[ShowingOut.model_validate(s) for s in upcoming],
    )
