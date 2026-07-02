"""Pydantic schemas Cinema — DTO API response."""
from pydantic import BaseModel, ConfigDict                                      
                                                                                
                                        
class CinemaOut(BaseModel):                                                     
    """Cinema di base — usato in liste e come sotto-oggetto altrove."""
    # from_attributes=True permette a Pydantic di leggere dagli oggetti SQLAlchemy                                                                      
    # (attributi come `.slug`, `.name`, ecc.) invece che da un dict.            
    model_config = ConfigDict(from_attributes=True)                             
                                                    
    slug: str                                                                   
    name: str                                        
    city: str                                                                   
    address: str
    region: str                                                                 
    lat: float                                       
    lon: float                         
    website: str | None = None
    phone: str | None = None

                                                                                
class CinemaWithCount(CinemaOut):
    """Estensione: include il conteggio degli spettacoli attivi (popolato dal service)."""                                                                    
    showings_count: int