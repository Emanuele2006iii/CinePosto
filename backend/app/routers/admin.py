"""REST endpoints /admin — operazioni protette (reimport, healthcheck dati)."""
# Sostituisce il vecchio APScheduler interno (D2): qui il backend espone un endpoint
# che lo studente/cron esterno può chiamare DOPO che lo scraper ha aggiornato i JSON.
#
# Sicurezza: header `X-Admin-Token` confrontato con settings.admin_token.
#
# TODO router atteso:
#   from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
#   from sqlalchemy.orm import Session
#   from ..database import get_db
#   from ..config import get_settings
#   # from ..seed import run_seed                          # TODO: script seed_from_json.py
#
#   router = APIRouter()
#
#   def _require_admin(x_admin_token: str | None = Header(None)):
#       if x_admin_token != get_settings().admin_token:
#           raise HTTPException(401, "Unauthorized")
#
#   @router.post("/reimport", dependencies=[Depends(_require_admin)])
#   def reimport_json(background: BackgroundTasks, db: Session = Depends(get_db)):
#       """Rilegge scraper/output/*.json e fa upsert su DB. Risponde subito (job in background)."""
#       background.add_task(run_seed, db_session_factory=...)
#       return {"status": "accepted", "msg": "Reimport in background"}
#
#   @router.get("/dataset-info", dependencies=[Depends(_require_admin)])
#   def dataset_info(db: Session = Depends(get_db)):
#       """Conteggi rapidi: # film, # spettacoli, # cinema, ultima data spettacolo."""
#       ...
