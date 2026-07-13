# Backend — Architettura tecnica

Vedi setup e avvio in [backend/README.md](../../backend/README.md).
Per le decisioni di design e il quadro d'insieme vedi [panoramica.md](../panoramica.md).
Per il mapping JSON scraper → DB vedi [schema-mapping.md](schema-mapping.md).

---

## Architettura a strati

```
routers/       ← PRESENTATION: riceve HTTP, valida input con Pydantic, chiama services
services/      ← BUSINESS: orchestrazione, regole di dominio
repositories/  ← DATA ACCESS: query SQLAlchemy, nessuna logica di business
models/        ← DOMAIN: entità SQLAlchemy persistite su SQLite
schemas/       ← DTO Pydantic: validazione input/output API (distinti dai modelli ORM)
```

Regola: ogni layer chiama solo il layer immediatamente sotto. Niente skip.

---

## Modello dati (lingua: inglese — decisione L1+L2)

### Cinema (`cinemas`)
PK = **`slug`** (stringa), allineato a `cinemas.json[*].slug` dello scraper.

```
slug        PK string       "postmodernissimo"
name        string NOT NULL
city        string NOT NULL
address     string NOT NULL
region      string default "Umbria"
lat         float NOT NULL
lon         float NOT NULL
website     string nullable
phone       string nullable
```

### Film (`films`)
PK = **`id` intera autoincrement**. Dedup tramite `UNIQUE(title_normalized, year)`.

```
id                INTEGER PK AUTOINCREMENT
title             string NOT NULL
title_normalized  string NOT NULL                  -- lower, no punctuation, single spaces
original_title    string nullable
year              int nullable
runtime_minutes   int nullable
genres            string nullable                   -- CSV
director          string nullable
poster_url        string nullable
synopsis          text nullable
wikidata_id       string nullable UNIQUE            -- arricchimento Wikidata (D1)
created_at        datetime default now

UNIQUE(title_normalized, year)
INDEX  ix_film_title_normalized
```

> **Perché PK intera invece di stringa**: il titolo è fragile (em-dash, apostrofi, encoding) e può essere riutilizzato per remake (`Dune 1984` vs `Dune 2021`). PK artificiale + chiave naturale UNIQUE è il pattern standard.

### Showing (`showings`)
FK su `Film` (intera) e `Cinema` (slug stringa).

```
id            INTEGER PK AUTOINCREMENT
film_id       int  FK → films.id          ON DELETE CASCADE
cinema_slug   str  FK → cinemas.slug      ON DELETE CASCADE
date          date NOT NULL
times         string NOT NULL              -- JSON array '["18:30","21:00"]'
language      string nullable              -- "ITA"/"ENG"/"ORIG-SUB"
screen        string nullable
buy_url       string nullable              -- source_url nel JSON scraper
scraped_at    datetime default now

UNIQUE(film_id, cinema_slug, date)
INDEX  ix_showings_date, ix_showings_film, ix_showings_cinema
```

---

## Endpoint previsti

| Metodo | Path | Descrizione |
|--------|------|-------------|
| `GET`  | `/health` | Liveness probe |
| `GET`  | `/api/v1/cinemas` | Lista cinema |
| `GET`  | `/api/v1/cinemas/nearby?lat&lon&radius_km` | Cinema in un raggio (Haversine) |
| `GET`  | `/api/v1/cinemas/{slug}` | Dettaglio cinema + conteggio showings |
| `GET`  | `/api/v1/cinemas/{slug}/showings?date_from&date_to` | Programmazione del cinema |
| `GET`  | `/api/v1/films/today` | Films con almeno uno showing oggi |
| `GET`  | `/api/v1/films/search?q=...` | Ricerca per titolo (substring su `title_normalized`) |
| `GET`  | `/api/v1/films/{id}` | Dettaglio film + prossimi showings |
| `GET`  | `/api/v1/showings?date&cinema_slug&film_id` | Programmazione filtrata |
| `GET`  | `/api/v1/showings/today` | Scorciatoia per oggi |
| `POST` | `/api/v1/admin/reimport` | Rilegge JSON scraper (header `X-Admin-Token` richiesto) |
| `GET`  | `/api/v1/admin/dataset-info` | Conteggi e ultima data dataset (protetto) |

Tutti gli endpoint sono **sola lettura** salvo `/admin/reimport`. I dati arrivano dallo scraper, non da utenti.

---

## Seed da JSON scraper

I JSON dello scraper sono **single source of truth**. Il backend li legge e li importa nel DB.

```
scraper/output/cinemas.json  → tabella cinemas
scraper/output/films.json    → tabella films
scraper/output/showings.json → tabella showings
```

**Ordine di esecuzione obbligatorio** (vincoli FK):
1. cinemas → upsert per slug
2. films → upsert per (title_normalized, year); costruisci lookup `{titolo_stringa_JSON: id_intera_DB}`
3. showings → usa lookup per risolvere `film_id` intera; upsert per (film_id, cinema_slug, date)

Specifica completa in [schema-mapping.md](schema-mapping.md).

**Trigger del seed**:
- **Manualmente**: script `python -m app.seed` (al primo deploy / fix locale).
- **Periodicamente**: `cron` esterno o `systemd timer` invoca `POST /api/v1/admin/reimport` dopo che lo scraper ha aggiornato i JSON.

Nessuno scheduler interno al backend (decisione D2): lo scraper vive nel suo processo via systemd timer separato (vedi `scraper/deploy/cineposto-scraper.timer`).

---

## Tecnologie

| Cosa | Scelta | Motivo |
|------|--------|--------|
| Framework | FastAPI | Async, Pydantic integrato, Swagger auto |
| ORM | SQLAlchemy 2.0 sync | Sufficiente per la scala, più semplice di async |
| DB dev + prod | **SQLite** (D4) | Bassa concorrenza, lettura-pesante, zero ops |
| Migrations | Alembic | Standard de facto SQLAlchemy |
| Arricchimento dati | **Wikidata via scraper** (D1) | Già fatto a monte, gratis, niente API key |
| Scheduling | **Esterno** (systemd timer + `--once`) (D2/L3) | Backend resta stateless rispetto allo scraping |
| Identità Cinema | **PK slug stringa** (D3) | Allineato JSON, URL parlanti |
| Identità Film | **PK intera + UNIQUE(title_normalized, year)** (D3) | Robusto a remake e encoding fragile |
| Lingua codice/schema | **Inglese** (L1+L2) | Allineato JSON scraper, niente traduzione runtime |
| Sicurezza endpoint admin | Header `X-Admin-Token` | Sufficiente per MVP locale; in prod aggiungere HTTPS + IP allowlist |

---

## Status (2026-07-02)

- ✅ Struttura cartelle e file pronta
- ✅ `requirements.txt`, `.env.example`, `.gitignore` allineati
- ✅ Tutti i TODO nei file Python riflettono le decisioni D1-D5 + L1-L5 (lingua inglese)
- ✅ `schema-mapping.md` autorevole con nomi inglesi
- ✅ Scraper rebrandizzato + systemd timer pronto
- ✅ **`config.py`** implementato (Settings + `get_settings` con `lru_cache`)
- ✅ **`database.py`** implementato (Base, engine, SessionLocal, `get_db`, PRAGMA FK)
- ✅ **3 modelli SQLAlchemy** implementati (Cinema/Film/Showing con vincoli e indici)
- ✅ **Schemas Pydantic** implementati (CinemaOut/WithCount, FilmOut/Detail, ShowingOut/Detail; forward reference + `field_validator` su `times`)
- ✅ **Repositories** implementati (SQLAlchemy 2.0 `select()`, `joinedload` anti-N+1, `upsert_from_scraper`, `normalize_title` per dedup)
- 🔜 services (`get_films_today`, `get_cinema_with_count`, `search_films`)
- 🔜 routers (endpoint REST + Swagger auto)
- 🔜 `main.py` (`create_app` factory + CORS + lifespan)
- 🔜 `seed_from_json.py` (bootstrap DB da `scraper/output/*.json`)
- 🔜 tests (`conftest.py` + smoke test endpoint chiave)
- 🔜 Alembic init + migration iniziale
