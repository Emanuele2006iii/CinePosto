"""Re-export dei repository per import piu' comodo dai service."""
from app.repositories import cinema_repo, film_repo, showing_repo

__all__ = ["cinema_repo", "film_repo", "showing_repo"]
