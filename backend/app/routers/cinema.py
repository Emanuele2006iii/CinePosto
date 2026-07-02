"""Endpoint REST per Cinema."""                                                 
from fastapi import APIRouter, Depends, HTTPException, Query                    
from sqlalchemy.orm import Session                                              
                                                                                
from app.database import get_db                      
from app.schemas import CinemaOut, CinemaWithCount, ShowingDetail               
from app.services import cinema_service              
from app.repositories import showing_repo
from datetime import date, timedelta                                            

router = APIRouter(prefix="/cinema", tags=["cinema"])                           
                                                    
                                                                                
@router.get("", response_model=list[CinemaOut])
def list_cinemas(db: Session = Depends(get_db)):                                
    """Lista tutti i cinema (ordinati per nome)."""  
    return cinema_service.list_cinemas(db)                                      

                                                                                
@router.get("/{slug}", response_model=CinemaWithCount)
def get_cinema(slug: str, db: Session = Depends(get_db)):
    """Dettaglio cinema + conteggio spettacoli futuri."""                       
    result = cinema_service.get_cinema_with_count(db, slug)                     
    if result is None:                                                          
        raise HTTPException(status_code=404, detail="Cinema non trovato")       
    cinema, count = result                                                      
    # Ricostruiamo lo schema combinando l'oggetto SQLAlchemy + il count calcolato.                                                                      
    return CinemaWithCount(**cinema.__dict__, showings_count=count)
                                                                                
                                                                                
@router.get("/{slug}/showings", response_model=list[ShowingDetail])
def list_cinema_showings(                                                       
    slug: str,                                       
    date_from: date | None = Query(None, description="Formato YYYY-MM-DD, default: oggi"),                                                                
    date_to: date | None = Query(None, description="Formato YYYY-MM-DD, default: +7 giorni"),                                                                   
    db: Session = Depends(get_db),                   
):                                                                              
    """Programmazione di un cinema in un range di date (default: prossimi 7 giorni)."""                                                                     
    # Verifica che il cinema esista (altrimenti 404, non lista vuota silenziosa)
    if cinema_service.get_cinema(db, slug) is None:                             
        raise HTTPException(status_code=404, detail="Cinema non trovato")
                                                                                
    # Default range: da oggi a +7 giorni             
    df = date_from or date.today()                                              
    dt = date_to or (df + timedelta(days=7))         
                                                                                
    return showing_repo.list_by_cinema_in_range(db, slug, df, dt)
                                                                    