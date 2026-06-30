# CinePosto — Backend (FastAPI)

API REST per servire le programmazioni dei cinema umbri raccolte dallo scraper.

> ⚠️ **Stato reale al 2026-06-30**: i file Python sotto `app/` contengono esclusivamente docstring + commenti `TODO`. **Nessuna riga eseguibile è ancora presente**: `uvicorn app.main:app` fallisce con `ImportError`. La struttura layered descritta qui sotto è il **design target**, non lo stato attuale. Per la roadmap di implementazione completa vedi [`../docs/CONTINUAZIONE-PROGETTUALE.md`](../docs/CONTINUAZIONE-PROGETTUALE.md).
>
> **Decisioni di design pendenti** (vedi §4 del piano):
> - **D1**: arricchimento dati = Wikidata (già fatto dallo scraper) o TMDB? → proposta: Wikidata, eliminare TMDB.
> - **D2**: scheduler = standalone o nel backend? → proposta: standalone (systemd), niente APScheduler nel backend.
> - **D3**: PK in DB = stringa o intera? → proposta: `cinema.slug` PK testuale, `film.id` PK intera.
> - **D4**: PostgreSQL anche in prod? → proposta: SQLite anche in prod per MVP.

## 🏗️ Architettura a strati (Layered Architecture)

```
┌─────────────────────────────────────────────┐
│  PRESENTATION  routers/   (endpoint REST)   │  ← HTTP request/response
├─────────────────────────────────────────────┤
│  BUSINESS      services/  (regole dominio)  │  ← orchestrazione
├─────────────────────────────────────────────┤
│  DATA ACCESS   repositories/  (CRUD su DB)  │  ← query SQL
├─────────────────────────────────────────────┤
│  DOMAIN        models/    (SQLAlchemy)      │  ← entità persistite
└─────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  INTEGRATION  scrapers/  (siti esterni)  │  ← popola DB notte
  └──────────────────────────────────────────┘
```

**Regola del layering** (Sommerville §6.3): un layer può chiamare SOLO il layer sotto. Niente skip, niente call back.

- `routers/` chiama `services/`
- `services/` chiama `repositories/`
- `repositories/` legge/scrive `models/`
- `scrapers/` popola `models/` via `repositories/` (di lato, non dall'alto)

## 📁 Struttura

```
backend/
├── requirements.txt
├── .env.example          ← copia in .env e compila
├── .gitignore
├── app/
│   ├── main.py           ← FastAPI app + CORS + lifespan
│   ├── config.py         ← Settings da .env (pydantic-settings)
│   ├── database.py       ← engine SQLAlchemy + SessionLocal + get_db
│   │
│   ├── routers/          ← PRESENTATION: cinema.py, spettacoli.py, film.py
│   ├── services/         ← BUSINESS: cinema_service.py, film_service.py
│   ├── repositories/     ← DATA ACCESS: cinema_repo.py, spettacolo_repo.py, film_repo.py
│   ├── models/           ← DOMAIN: cinema.py, spettacolo.py, film.py
│   ├── schemas/          ← PYDANTIC DTO: cinema.py, spettacolo.py, film.py
│   └── scrapers/         ← INTEGRATION: base.py (ABC), scheduler.py, multisala_*.py
│
└── tests/
    ├── test_routers/
    ├── test_services/
    └── test_repositories/
```

## 🚀 Setup e avvio (post-implementazione, non ancora funzionante)

> ⚠️ **Python 3.12 obbligatorio** (NON 3.13/3.14). `pydantic-core 2.27` non supporta ancora Python 3.14.
> Su Mac: `brew install python@3.12` se manca. Crea il venv esplicitamente con `python3.12 -m venv venv`.

```bash
# 1. Crea venv (Python 3.12 esplicito)
python3.12 -m venv venv
source venv/bin/activate

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Copia env
cp .env.example .env
# (DATABASE_URL e CORS_ORIGINS sono i campi necessari; TMDB_API_KEY/SCRAPE_CRON
#  da rimuovere se si adottano le decisioni D1/D2 — vedi piano §4)

# 4. Avvia (RICHIEDE Sprint 2 completato)
uvicorn app.main:app --reload --port 8000
```

Endpoint previsti (definiti in `docs/CONTINUAZIONE-PROGETTUALE.md` §5):
- `http://localhost:8000/docs` → Swagger UI auto-generato
- `GET /api/v1/cinema` → lista cinema
- `GET /api/v1/cinema/{slug}` → dettaglio cinema
- `GET /api/v1/cinema/{slug}/spettacoli` → spettacoli di un cinema
- `GET /api/v1/film/oggi` → film con almeno uno spettacolo oggi
- `GET /api/v1/film/{id}` → dettaglio film + prossimi spettacoli
- `GET /api/v1/film/search?q=...` → ricerca per titolo
- `GET /api/v1/spettacoli?data=YYYY-MM-DD` → tutti gli spettacoli di una data
- `POST /api/v1/admin/reimport` → rilegge i JSON dello scraper e aggiorna il DB
- `GET /health` → liveness probe

## 🧪 Test

```bash
pytest tests/
```

## 🔌 Aggiungere uno scraper nuovo

Vedi `app/scrapers/README.md`.

## 📚 Decisioni di progetto

| Cosa | Scelta | Perché |
|---|---|---|
| Framework | FastAPI | Async, validazione automatica con Pydantic, Swagger auto |
| ORM | SQLAlchemy 2.0 sync | Più semplice di async, sufficiente per la scala del progetto |
| DB dev + prod (D4) | **SQLite** | Bassa concorrenza, read-heavy, zero ops; migrazione a PostgreSQL solo se servisse |
| Arricchimento dati (D1) | **Wikidata via scraper** | Già fatto a monte, nessuna API key, nessuna chiamata esterna runtime |
| Scheduling (D2) | **Esterno**: scraper standalone via systemd timer | Backend resta stateless rispetto allo scraping; il reimport è triggerato da `POST /api/v1/admin/reimport` |
| PK Cinema (D3) | **slug stringa** | Allineato al JSON dello scraper, URL parlanti |
| PK Film (D3) | **intera + UNIQUE(titolo_norm, anno)** | Robusto a remake e a encoding fragile del titolo |
| Dati | JSON prodotti dallo scraper | Nessun re-scraping nel backend; single source of truth |
| Migrations | Alembic | Standard SQLAlchemy |

## 🗺️ Status

- [x] **2026-06-14**: Architettura definita, struttura cartelle creata, requirements.txt + .env.example pronti
- [x] **2026-06-30 mattina**: Audit + decisioni di design (D1-D5 + L1-L5) + piano operativo Sprint 2
- [x] **2026-06-30 sera**: `config.py` + `database.py` + 3 modelli SQLAlchemy (Cinema/Film/Showing) implementati e smoke-testati
- [ ] Implementare schemas Pydantic
- [ ] Implementare repositories (CRUD readonly + upsert)
- [ ] Implementare services (films_today, find_nearby, search_films)
- [ ] Implementare routers (endpoint REST + Swagger)
- [ ] `main.py` entrypoint con `create_app()` factory
- [ ] Script `seed.py` (legge `scraper/output/` e popola DB)
- [ ] Endpoint admin `POST /api/v1/admin/reimport`
- [ ] Tests pytest con TestClient (conftest.py + 3-4 test endpoint chiave)
- [ ] Alembic init + migrazione iniziale

## 🎯 Presentazione — 14/07/2026

Per la presentazione minima (MVP):
- README chiaro con architettura ✅ (questo)
- Backend funzionante con 3+ endpoint readonly (cinema, film/oggi, spettacoli)
- Seed DB dai JSON prodotti dallo scraper (`scraper/output/`)
- Swagger UI accessibile su `/docs`
- App collegata al backend (vedi `docs/CONTINUAZIONE-PROGETTUALE.md` §7 Sprint 3)
