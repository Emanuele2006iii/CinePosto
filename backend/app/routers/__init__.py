"""Re-export dei router per import piu' comodo in main.py."""
from app.routers import admin, cinema, film, showings

__all__ = ["admin", "cinema", "film", "showings"]
