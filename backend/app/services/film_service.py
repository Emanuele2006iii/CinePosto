"""Business logic per Film.                                                     
Contiene la logica 'cosa c'e in programmazione' che e' il cuore dell'app.       
"""                                                                             
from datetime import date, timedelta                                            
                                                                                
from sqlalchemy.orm import Session                   
                                        
from app.models.film import Film
from app.models.showing import Showing
from app.repositories import film_repo, showing_repo                            

                                                                                
def get_films_today(db: Session) -> list[Film]:      
    """Film con almeno uno spettacolo oggi. Feature core della Home screen."""
    today = date.today()                                                        
    return film_repo.list_in_programming(db, today, today)
                                                                                
                                                    
def get_films_this_week(db: Session) -> list[Film]:                             
    """Film in programmazione da oggi ai prossimi 7 giorni.
    Usato per il filtro 'questa settimana' della Home.                          
    """                                                                         
    today = date.today()                                                        
    week_end = today + timedelta(days=6)                                        
    return film_repo.list_in_programming(db, today, week_end)
                                        
                                                                                
def get_film_detail(
    db: Session, film_id: int                                                   
) -> tuple[Film, list[Showing]] | None:              
    """Ritorna il film + i suoi prossimi spettacoli (dal giorno stesso in poi).
    None se il film non esiste.                                                 
    """                                                                         
    film = film_repo.get_by_id(db, film_id)                                     
    if film is None:                                                            
        return None                                  
    upcoming = showing_repo.list_by_film(db, film_id, date.today())
    return film, upcoming                                                       

                                                                                
def search_films(db: Session, query: str, limit: int = 20) -> list[Film]:
    """Ricerca film per titolo (case-insensitive, no punteggiatura)."""         
    # Validazione input: query troppo corta non ha senso (rumore)               
    if len(query.strip()) < 2:                                                  
        return []                                                               
    return film_repo.search_by_title(db, query, limit=limit)                    
                                                                        