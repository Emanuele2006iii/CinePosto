"""Data access layer: CRUD su Cinema. SOLO query, niente logica business."""
# Decisione D3: PK = slug stringa. Decisione D1+D2: scraper esterno → backend readonly + upsert al seed.
#
# TODO funzioni pure su db: Session (SQLAlchemy 2.0 style — `db.scalars(select(...))`).
#
#   def get_by_slug(db, slug: str) -> Cinema | None
#   def list_all(db) -> list[Cinema]                                    # ordinato per name
#   def upsert(db, data: dict) -> Cinema                                 # usato da seed_from_json
#       # logica: SELECT by slug; se esiste UPDATE campi, altrimenti INSERT
#
# Pattern usage:
#   from sqlalchemy import select
#   def get_by_slug(db, slug):
#       return db.scalars(select(Cinema).where(Cinema.slug == slug)).one_or_none()
