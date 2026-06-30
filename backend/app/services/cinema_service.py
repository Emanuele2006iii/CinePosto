"""Business logic Cinema: orchestrazione repository + regole di dominio."""
# REGOLA Sommerville §6.3: i router chiamano services, services chiamano repositories. Niente shortcut.
#
# TODO funzioni:
#   def list_cinemas(db) -> list[CinemaOut]
#       # cinema_repo.list_all → mapping Pydantic
#   def get_detail(db, slug: str) -> CinemaWithCount
#       # cinema_repo.get_by_slug + conteggio showings prossimi
#   def find_nearby(db, lat: float, lon: float, radius_km: float = 20) -> list[CinemaOut]
#       # cinema_repo.list_all + filtro Haversine in Python (3 cinema → costo trascurabile)
#   def get_schedule(db, slug: str, date_from: date, date_to: date) -> list[ShowingOut]
#       # showing_repo.list_by_cinema(slug, date_from, date_to)
#
# Haversine helper:
#   def haversine_km(lat1, lon1, lat2, lon2) -> float: ...
