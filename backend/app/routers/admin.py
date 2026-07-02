"""Endpoint amministrativi — protetti da token."""
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Cinema, Film, Showing
from app.seed_from_json import seed_from_json

router = APIRouter(prefix="/admin", tags=["admin"])


def _verify_admin_token(x_admin_token: str = Header(...)):
    """Dependency: verifica che l'header X-Admin-Token corrisponda a quello in .env."""
    settings = get_settings()
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token amministratore non valido",
        )


@router.post("/reimport", dependencies=[Depends(_verify_admin_token)])
def reimport_json(db: Session = Depends(get_db)):
    """Rilegge i JSON dello scraper e ripopola il database."""
    settings = get_settings()
    output_dir = Path(settings.scraper_output_dir).resolve()

    if not output_dir.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Cartella scraper output non trovata: {output_dir}",
        )

    try:
        stats = seed_from_json(db, output_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "imported": stats}


@router.get("/dataset-info", dependencies=[Depends(_verify_admin_token)])
def dataset_info(db: Session = Depends(get_db)):
    """Riepilogo dei dati nel DB. Utile per monitoring / debug."""
    cinemas_count = db.scalar(select(func.count()).select_from(Cinema))
    films_count = db.scalar(select(func.count()).select_from(Film))
    showings_count = db.scalar(select(func.count()).select_from(Showing))
    latest_scraped = db.scalar(select(func.max(Showing.scraped_at)))

    return {
        "cinemas": cinemas_count,
        "films": films_count,
        "showings": showings_count,
        "latest_scraped_at": latest_scraped.isoformat() if latest_scraped else None,
    }
