"""Pydantic schemas Showing — DTO API response."""
import json                                                                     
from datetime import date as date_type               
from pydantic import BaseModel, ConfigDict, field_validator                                 
from .cinema import CinemaOut                                                   
from .film import FilmOut
                                                                            
                                                
class ShowingOut(BaseModel):           
    """Spettacolo base — usato in liste."""
    model_config = ConfigDict(from_attributes=True)                             

    id: int                                                                     
    date: date_type                                  
    times: list[str]                       # ["18:30", "21:00"]
    language: str | None = None                                                 
    screen: str | None = None
    buy_url: str | None = None                                                  
                                                    
    @field_validator("times", mode="before")                                    
    @classmethod
    def _parse_times(cls, v):                                                   
        # Nel DB `times` e' salvato come stringa JSON: '["18:30","21:00"]'.
        # Qui la trasformiamo in lista Python PRIMA della validazione del tipo. 
        return json.loads(v) if isinstance(v, str) else v                       
                                                                                
                                                                            
class ShowingDetail(ShowingOut):                     
    """Versione denormalizzata: include cinema e film completi.                 
    Usata su GET /showings?date=... per evitare N+1 query lato client. """    
                                                                         
    cinema: CinemaOut                                                           
    film: FilmOut             