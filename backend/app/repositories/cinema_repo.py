"""Data access layer: query su Cinema. SOLO query, niente logica business."""
from sqlalchemy import select                                                   
from sqlalchemy.orm import Session                   
                                                                                
from app.models.cinema import Cinema                 
                                                                                
                                                    
def get_by_slug(db: Session, slug: str) -> Cinema | None:
    """Ritorna il cinema col dato slug, o None se non esiste."""
    return db.scalars(select(Cinema).where(Cinema.slug == slug)).one_or_none()  
                                                                                
                                                                                
def list_all(db: Session) -> list[Cinema]:                                      
    """Ritorna tutti i cinema, ordinati per nome.""" 
    return list(db.scalars(select(Cinema).order_by(Cinema.name)))
                                                                                

def upsert(db: Session, data: dict) -> Cinema:                                  
    """Insert-or-update: se esiste il cinema con quel slug lo aggiorna, altrimenti lo crea. Usato dal seed_from_json."""                                                                         
    slug = data["slug"]                                                         
    cinema = get_by_slug(db, slug)                                              
                                                                                
    if cinema is None:                 
        # Non esiste → INSERT                                                   
        cinema = Cinema(**data)                      
        db.add(cinema)                                                          
    else:
        # Esiste → UPDATE dei campi (tranne slug che è PK)                      
        for key, value in data.items():                                         
            if key != "slug":          
                setattr(cinema, key, value)                                     
                                                    
    db.flush()   # forza l'esecuzione della query SENZA fare commit             
    return cinema
