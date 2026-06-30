"""Data access layer: CRUD su Showing. SOLO query, niente logica business."""
# Decisione D3: FK = (film_id int, cinema_slug str). UNIQUE(film_id, cinema_slug, date) → upsert per dedup.
#
# TODO funzioni:
#   def list_by_date(db, date_: date) -> list[Showing]
#       # eager-load di film e cinema (selectinload) per evitare N+1
#   def list_by_cinema(db, cinema_slug: str, date_from: date, date_to: date) -> list[Showing]
#   def list_by_film(db, film_id: int, from_today: bool = True) -> list[Showing]
#   def upsert(db, data: dict) -> Showing
#       # cerca per (film_id, cinema_slug, date) → UPDATE times/language/screen se esiste, INSERT altrimenti
#   def delete_old(db, before: date) -> int
#       # cleanup showings con date < before (chiamato dopo ogni reimport)
#
# Pattern eager-load (SQLAlchemy 2.0):
#   from sqlalchemy import select
#   from sqlalchemy.orm import selectinload
#   stmt = (
#       select(Showing)
#       .options(selectinload(Showing.film), selectinload(Showing.cinema))
#       .where(Showing.date == date_)
#   )
