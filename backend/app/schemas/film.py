
"""Pydantic schemas Film — DTO API response."""
from pydantic import BaseModel, ConfigDict                                      
                                                                                
                                                                                
class FilmOut(BaseModel):                                                       
    """Versione 'card' — usata nelle liste (Home 'Film oggi', ricerca)."""
    model_config = ConfigDict(from_attributes=True)                             

    id: int                                                                     
    title: str                                       
    year: int | None = None            
    runtime_minutes: int | None = None                                          
    genres: str | None = None            # CSV: "Drama,Thriller"
    poster_url: str | None = None                                               
                                                                                
                                        
class FilmDetail(FilmOut):                                                      
    """Versione completa — usata su GET /film/{id} (schermata dettaglio)."""
    original_title: str | None = None                                           
    director: str | None = None
    synopsis: str | None = None                                                 
    wikidata_id: str | None = None                   
    # Lista dei prossimi spettacoli. `ShowingOut` viene definito in schemas/showing.py:                                                             
    # usiamo forward reference (stringa) per evitare import circolare.          
    showings: list["ShowingOut"] = []