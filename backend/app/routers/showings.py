"""Endpoint REST per Showings (spettacoli)."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import showing_repo
from app.schemas import ShowingDetail

router = APIRouter(prefix="/showings", tags=["showings"])


@router.get("", response_model=list[ShowingDetail])
def list_showings(
    target_date: date | None = Query(
        None,
        alias="date",
        description="Data in formato YYYY-MM-DD. Default: oggi.",
    ),
    db: Session = Depends(get_db),
):
    """Tutti gli spettacoli di una data (di tutti i cinema)."""
    return showing_repo.list_by_date(db, target_date or date.today())
