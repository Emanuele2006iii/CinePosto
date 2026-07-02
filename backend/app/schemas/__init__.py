"""Re-export degli schemas + risoluzione delle forward reference."""
from .cinema import CinemaOut, CinemaWithCount                                  
from .film import FilmDetail, FilmOut                                           
from .showing import ShowingDetail, ShowingOut                                  
                                                                                
# FilmDetail contiene `list["ShowingOut"]` come forward reference (stringa).    
# Ora che tutti gli schemi sono importati, chiediamo a Pydantic di risolvere
# quel riferimento in classe reale. Senza questa chiamata, /film/{id}           
# fallirebbe a runtime con PydanticInvalidForwardRef.                           
FilmDetail.model_rebuild()                                                      
                                                                                
__all__ = [                                                                     
    "CinemaOut",                                                                
    "CinemaWithCount",                               
    "FilmOut",                         
    "FilmDetail",
    "ShowingOut",
    "ShowingDetail",
]  