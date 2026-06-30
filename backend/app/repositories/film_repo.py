"""Data access layer: CRUD su Film. SOLO query, niente logica business."""
# Decisione D1: arricchimento via Wikidata (nello scraper), niente TMDB → niente upsert da TMDB.
# Decisione D3 opzione 2: PK intera + UNIQUE(title_normalized, year).
#
# TODO funzioni:
#   def get_by_id(db, id: int) -> Film | None
#   def get_by_natural_key(db, title_normalized: str, year: int | None) -> Film | None
#       # cerca per UNIQUE(title_normalized, year); usato dal seed per ottenere id intera dal titolo JSON
#   def get_by_wikidata_id(db, wikidata_id: str) -> Film | None
#   def search_by_title(db, query: str, limit: int = 20) -> list[Film]
#       # LIKE/ILIKE su title_normalized con `query` normalizzata
#   def list_in_programming(db, date_from: date, date_to: date) -> list[Film]
#       # JOIN con showings dove date BETWEEN date_from AND date_to, DISTINCT
#   def upsert_from_scraper(db, data: dict) -> Film
#       # logica:
#       #   1) calcola title_normalized
#       #   2) cerca per (title_normalized, year) → se trovato UPDATE solo campi non null
#       #   3) altrimenti INSERT
#       #   4) ritorna istanza con id popolato (serve al seed per le FK in showings)
