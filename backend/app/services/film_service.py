"""Business logic Film: ricerca, dedup, programmazione."""
# Decisione D1: NIENTE chiamate TMDB qui — l'arricchimento (poster, director, runtime) è già
# stato fatto dallo scraper via Wikidata e arriva nei JSON.
#
# TODO funzioni:
#   def normalize_title(title: str) -> str
#       # lowercase, rimuove punteggiatura (em-dash, apostrofi, virgolette), collapse spazi
#       # USATA SIA dal seed che dalla ricerca per garantire match consistente
#       # (replica la logica di scraper/normalizer.title_key per consistenza con i JSON in ingresso)
#
#   def search_films(db, query: str) -> list[FilmOut]
#       # film_repo.search_by_title(normalize_title(query))
#
#   def films_today(db) -> list[FilmOut]
#       # film_repo.list_in_programming(date.today(), date.today())
#
#   def films_in_range(db, date_from: date, date_to: date) -> list[FilmOut]
#       # film_repo.list_in_programming(date_from, date_to)
#
#   def get_detail(db, id: int, max_showings: int = 50) -> FilmDetail
#       # film_repo.get_by_id + prossimi showings (eager-load), 404 se non esiste
