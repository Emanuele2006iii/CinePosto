"""Re-export dei modelli. Importare TUTTI prima di chiamare Base.metadata.create_all."""
from app.models.cinema import Cinema
from app.models.film import Film
from app.models.showing import Showing

__all__ = ["Cinema", "Film", "Showing"]
