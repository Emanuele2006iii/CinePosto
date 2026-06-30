# CinePosto — Piano di continuazione completo

> **Documento**: pianificazione end-to-end per portare CinePosto dallo stato attuale (scraper ✅, resto skeleton) al rilascio v1.0 e oltre.
> **Audience**: io stesso + team RepCode (Emanuele, Elio, Andrea, Yonas) + prof. ISS.
> **Data redazione**: 2026-06-30.
> **Stato del documento**: vivo — aggiornare a ogni sprint chiuso.

---

## 1. Sommario esecutivo

Lo **scraper è in produzione** (75 test, ruff pulito, CI GitHub Actions, 3 connettori funzionanti, output JSON DB-ready aggiornato al 2026-06-25 con 22 film, 310 spettacoli, 3 cinema). Il **backend è solo documentazione**: ogni file Python contiene esclusivamente docstring + commenti TODO, zero righe eseguibili. L'**app React Native** ha 2 schermate funzionanti ma con dati hardcoded (`MOCK_FILMS`, `CINEMAS`), nessun fetch, nessuna mappa. Il **worker Cloudflare** è uno stub.

I documenti ISS (analisi requisiti, sprint plan) sono **ben fatti** e formali, ma il sprint plan non riflette lo stato reale del backend (lo descrive come "scheletro pronto").

**Conseguenze pratiche per la presentazione del 14/07/2026**:
- Senza un backend funzionante l'app non ha dati reali, quindi la demo cade.
- Lo scraper da solo non è "il prodotto" promesso (l'app mobile lo è).
- Bisogna concentrare 100% delle energie del team su backend + collegamento app.

---

## 2. Stato per componente (audit dettagliato)

### 2.1 Scraper ✅ produzione

| Aspetto | Valore |
|---------|--------|
| LOC Python | 4448 |
| Test | 75 (`tests/test_*.py` — 11 file) |
| Coverage gate | ≥60% (CI fallisce sotto) |
| Lint | ruff pulito |
| Connettori | PostModernissimo (HTML+RSC), The Space (API OAuth2 + fallback CloakBrowser), UCI (API Cloud Run) |
| Output | `movies.json` (stato interno), `films.json`, `showings.json`, `cinemas.json` |
| Arricchimento | Wikidata (poster, regista, titolo originale, durata) |
| CI | GitHub Actions su push/PR a `main` |
| Scheduling | `--schedule` interno o systemd esterno |
| Bug noti | nessuno bloccante |

**Punti di attenzione**:
- Test reali (Wikidata live, mitmproxy verso i siti) **da eseguire su VM Linux** quando si prepara il deploy (memo già in wiki).
- Cartelle artefatte sporche: `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/` ancora nella working copy. Non sono nel git del monorepo ma vanno aggiunte al `.gitignore` se non già presenti.

### 2.2 Backend 🔴 documentazione vestita da codice

**Realtà oggettiva**: i 14 file Python di `backend/app/` contengono esclusivamente docstring + commenti TODO. Nessun `import`, nessuna classe, nessuna funzione eseguibile. Conseguenza:

```bash
cd backend && uvicorn app.main:app --reload --port 8000
# → ImportError: cannot import name 'app' from 'app.main'
```

| File | Contenuto reale |
|------|-----------------|
| `app/main.py` | docstring + TODO con esempio in commento |
| `app/database.py` | docstring + TODO con esempio in commento |
| `app/config.py` | docstring + TODO |
| `app/models/{cinema,spettacolo,film}.py` | docstring + TODO descrittivo dei campi attesi |
| `app/schemas/{cinema,spettacolo,film}.py` | docstring + TODO |
| `app/repositories/{cinema_repo,spettacolo_repo,film_repo}.py` | docstring + TODO |
| `app/services/{cinema_service,film_service,tmdb_client}.py` | docstring + TODO |
| `app/routers/{cinema,spettacoli,film}.py` | docstring + TODO |
| `app/scrapers/{base,scheduler}.py` | docstring + TODO (sezione 4: probabilmente da rimuovere) |
| `tests/__init__.py` | vuoto |

**Cosa c'è di pronto realmente**:
- `requirements.txt` ben curato (FastAPI 0.115, SQLAlchemy 2.0.36, Pydantic 2.10, APScheduler 3.10.4, pytest 8.3.3, ruff 0.8.0, alembic 1.14.0).
- `.env.example` con tutti i campi previsti (`DATABASE_URL`, `TMDB_API_KEY`, `SCRAPE_CRON`, `CORS_ORIGINS`, `ENV`, `LOG_LEVEL`).
- `.gitignore` corretto (esclude `.env`, `*.db`, `*.log`, `__pycache__`).
- Architettura mentale **ben pensata** (layered Sommerville §6.3).
- README documenta l'intento di design correttamente.

### 2.3 App React Native 🟡 mock only

| Aspetto | Valore |
|---------|--------|
| LOC | 151 (2 file JSX) |
| Stack | Expo SDK 54, React 19.1, React Native 0.81.5, expo-router 6 |
| Schermate | `(tabs)/index.jsx` "Film Oggi", `(tabs)/cinema.jsx` "Cinema" |
| Dati | hardcoded `MOCK_FILMS`, `CINEMAS` |
| HTTP client | **assente** (no fetch, no axios, no react-query) |
| Mappa | **assente** (no react-native-maps) — ma RF-03 la richiede |
| State management | nessuno (solo state locale di FlatList) |
| TypeScript | tsconfig presente ma codice in `.jsx` puro |
| Test | nessuno |

### 2.4 Worker Cloudflare 🟡 stub

- `pages-public/index.html` (placeholder), `src/index.js`, `functions/api/proxy.js`, `Makefile`.
- Manca `_routes.json`, `_headers`, deploy script `wrangler.toml`.
- Nessuna documentazione su come l'app web build di Expo viene servita né su CORS.

### 2.5 Documentazione ISS ✅ ottima

- `docs/iss/analisi-requisiti.md`: 11 RF (RF-01..RF-11), 10 user story (US-01..US-10), stakeholder, risk assessment, matrice importanza/difficoltà.
- `docs/iss/sprint-plan.md`: 5 sprint, mapping US ↔ sprint, Sprint 1 ✅.
- Mancanza: sprint 2-5 non riflettono lo stato attuale dei componenti (presumono backend "scheletro pronto" che in realtà è solo doc).

---

## 3. Problemi strutturali e progettuali identificati

### 🔴 Critici (bloccano la consegna)

| # | Problema | Dove | Impatto |
|---|----------|------|---------|
| C1 | Backend ha 0 righe eseguibili | `backend/app/**` | App non può funzionare; demo impossibile |
| C2 | Discrepanza schema scraper ↔ backend: `films.json[*].id` è **stringa (titolo)**, modello backend prevede **`int PK`** | `scraper/output/films.json` vs `backend/app/models/film.py` | Il seed dei JSON in DB non funziona senza mappatura ID stringa→int |
| C3 | Stessa discrepanza per `cinemas[*].slug` (string) vs `Cinema.id` (int PK previsto) | `cinemas.json` vs `models/cinema.py` | idem |
| C4 | Doppia fonte di arricchimento dati (Wikidata nello scraper, TMDB nel backend) | `scraper/scraper/metadata.py` + `backend/app/services/tmdb_client.py` | Costo gratuito (Wikidata già funziona) vs API key TMDB; possibili discrepanze su poster/durata; sforzo duplicato |
| C5 | Doppio scheduler previsto (scraper standalone con `--schedule` + APScheduler nel backend `scrapers/scheduler.py`) | `scraper/scraper/main.py` + `backend/app/scrapers/scheduler.py` | Confusione architetturale; README backend dice "single source of truth: JSON" ma poi prevede `run_all_scrapers()` nel backend |

### 🟡 Importanti (rallentano)

| # | Problema | Dove |
|---|----------|------|
| W1 | Naming italiano/inglese misto: scraper emette `films/showings/cinemas` (en), backend modella `film/spettacolo/cinema` (it) | scraper output + `backend/app/{models,routers,schemas}` |
| W2 | `backend/tests/` ha solo `__init__.py` vuoto. Nessun `conftest.py`, nessun TestClient setup | `backend/tests/` |
| W3 | Alembic in requirements ma nessun `alembic init` né cartella `alembic/` | `backend/` |
| W4 | App ha TypeScript installato ma codice in `.jsx` (incoerenza) | `app/` |
| W5 | App non ha `react-native-maps` ma RF-03 (mappa interattiva) è funzionale obbligatoria | `app/package.json` |
| W6 | Worker non ha `wrangler.toml` né deploy script documentato | `worker/` |
| W7 | Sprint plan ISS descrive Sprint 1 ✅ ma gli sprint successivi non riflettono "backend = 0 codice" | `docs/iss/sprint-plan.md` |
| W8 | README principale dice "backend scheletro 🟡" che è ambiguo — sembra "skeleton di codice" non "skeleton di doc" | `README.md` |

### 🟢 Minori (cosmetici)

| # | Problema | Dove |
|---|----------|------|
| L1 | `.DS_Store` sparsi (root, scraper) | monorepo |
| L2 | `app/.expo/` versionato? Verificare `.gitignore` | `app/` |
| L3 | Scraper README usa nome "CinemaScarper" (typo storico), monorepo si chiama "CinePosto" | `scraper/README.md` |
| L4 | `cineposto/.DS_Store` non escluso dal gitignore root | `cineposto/.gitignore` |

---

## 4. Decisioni di design da prendere (URGENTI)

Queste decisioni vanno prese **prima** di scrivere una sola riga di backend, altrimenti il codice nascerà già con debiti.

### D1 — Arricchimento dati: Wikidata o TMDB?

**Status quo**: scraper arricchisce con Wikidata (poster, regista, originalTitle, runtime).

**Proposta**: **mantenere Wikidata, eliminare TMDB**. Motivazione:
- Wikidata è gratuita, senza API key, già funzionante.
- TMDB è ottima ma duplica funzionalità, richiede API key, aggiunge dipendenza esterna a runtime del backend.
- Il backend diventa più semplice: legge solo i JSON, non chiama API esterne.

**Conseguenze**:
- Eliminare `backend/app/services/tmdb_client.py`.
- Eliminare `TMDB_API_KEY` da `.env.example`.
- Rimuovere `arricchisci_da_tmdb` da `film_service.py` (era TODO).
- README backend: rimuovere sezione TMDB.

### D2 — Scheduler: scraper standalone o nel backend?

**Status quo**: ambiguo. Scraper ha `--schedule` interno, backend ha `scrapers/scheduler.py` che richiama `run_all_scrapers()`.

**Proposta**: **scraper standalone via systemd su VM Linux** (timer giornaliero). Il backend NON ri-scrapa.

**Motivazione**:
- Separazione netta delle responsabilità (Sommerville §6.2, principio di "single responsibility").
- Lo scraper può girare anche se il backend è giù.
- Più semplice da debuggare (un log file per componente).
- Il backend può rimanere stateless rispetto allo scraping: legge i JSON da disco condiviso o li importa una volta.

**Conseguenze**:
- Eliminare `backend/app/scrapers/scheduler.py` e tutta la cartella `backend/app/scrapers/`.
- Backend ottiene una rotta `POST /api/v1/admin/reimport` (protetta) che rilegge i JSON da `scraper/output/`.
- Rimuovere `apscheduler` da `backend/requirements.txt`.
- Aggiornare `backend/app/main.py`: niente lifespan startup scheduler.

### D3 — ID nel database: stringa o intero?

**Status quo**: scraper emette ID stringa (`film_id = "Titolo del film"`, `cinema_slug = "postmodernissimo"`).

**Opzione A**: Tenere PK intere nel DB e generare la mappatura al seed (un dict `{titolo: id}`).
**Opzione B**: Usare la stringa direttamente come PK (`film.titolo_norm` PK, `cinema.slug` PK).

**Proposta**: **Opzione B (PK stringa per Cinema, PK intera per Film con `tmdb_id` o `titolo_norm` UNIQUE)**.

Motivazione:
- `cinema.slug` è naturalmente univoco e parlante (`postmodernissimo`, `the-space-corciano`, `uci-perugia`). Usarlo come PK è elegante e l'app può linkarlo senza join.
- `film` invece può avere lo stesso titolo in anni diversi (remake): meglio PK intera + UNIQUE(`titolo_norm`, `anno`).
- `Spettacolo.cinema_slug` FK → `cinema.slug`. `Spettacolo.film_id` FK → `film.id` (intero).

### D4 — Database: SQLite o PostgreSQL?

**Status quo**: README dice "SQLite dev, PostgreSQL prod".

**Proposta**: **SQLite anche in prod per MVP** (a.k.a. v1.0 ISS). Migrazione a PostgreSQL solo se serve.

Motivazione:
- Traffico atteso: studenti che visualizzano la programmazione cinema di 1 città. Bassissimo.
- SQLite supporta tutto quello che serve (read-heavy, JOIN, GIN-like FTS5 per ricerca testo).
- Zero overhead operativo (no Docker, no porte, no utenze).
- Se davvero un giorno servirà PostgreSQL, SQLAlchemy permette la migrazione cambiando `DATABASE_URL`.

### D5 — Test fixtures: dati reali o sintetici?

**Proposta**: **fixtures sintetiche minime + test E2E con seed del JSON reale**.

- Unit test repositories: `Cinema(slug="test", nome="Test", ...)` in-memory SQLite.
- Test endpoint: TestClient + DB pulito + insert fixture.
- E2E test (1-2): carica `scraper/output/cinemas.json` in DB temp, chiama `GET /api/v1/cinema`, verifica 3 risultati.

---

## 5. Architettura target (post-decisioni)

```
┌────────────────────────────────────────────────────┐
│  VM Linux (cron giornaliero)                       │
│  ─ scraper/  (standalone, systemd timer 03:00)     │
│    → produce scraper/output/*.json                 │
└────────────────┬───────────────────────────────────┘
                 │ JSON files su disco condiviso o
                 │ rsync/scp al backend
                 ▼
┌────────────────────────────────────────────────────┐
│  Backend FastAPI (uvicorn su porta 8000)           │
│  ┌──────────────────────────────────────────────┐ │
│  │ POST /api/v1/admin/reimport                  │ │
│  │   → seed_from_json(): legge JSON, upsert DB  │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │ GET  /api/v1/cinema                          │ │
│  │ GET  /api/v1/cinema/{slug}                   │ │
│  │ GET  /api/v1/cinema/{slug}/spettacoli        │ │
│  │ GET  /api/v1/film/oggi                       │ │
│  │ GET  /api/v1/film/{id}                       │ │
│  │ GET  /api/v1/film/search?q=...               │ │
│  │ GET  /api/v1/spettacoli?data=YYYY-MM-DD      │ │
│  │ GET  /health                                 │ │
│  └──────────────────────────────────────────────┘ │
│  SQLite single-file (cineposto.db)                 │
└────────────────┬───────────────────────────────────┘
                 │ HTTPS / CORS
                 ▼
┌────────────────────────────────────────────────────┐
│  App React Native (Expo SDK 54)                    │
│  ─ Schermate: Home, Cinema, Mappa, Dettaglio Film  │
│  ─ Fetch: lib axios o nativo fetch                 │
│  ─ Cache: AsyncStorage + react-query (opzionale)   │
│  ─ Mappa: react-native-maps                        │
└────────────────────────────────────────────────────┘
```

---

## 6. Schema DB target (post-D3)

```sql
-- Cinema: PK = slug (string)
CREATE TABLE cinemas (
  slug       TEXT PRIMARY KEY,        -- es. "postmodernissimo"
  nome       TEXT NOT NULL,
  citta      TEXT NOT NULL,
  indirizzo  TEXT NOT NULL,
  lat        REAL NOT NULL,
  lon        REAL NOT NULL,
  sito_web   TEXT,
  telefono   TEXT,
  regione    TEXT DEFAULT 'Umbria'
);

-- Film: PK intera, ricerca per titolo normalizzato
CREATE TABLE films (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  titolo            TEXT NOT NULL,
  titolo_norm       TEXT NOT NULL,   -- snake-case lower, usato per dedup
  titolo_originale  TEXT,
  anno              INTEGER,
  durata_minuti     INTEGER,
  generi            TEXT,            -- CSV o JSON array
  poster_url        TEXT,
  sinossi           TEXT,
  regista           TEXT,
  wikidata_id       TEXT UNIQUE,     -- es. Q123456
  created_at        TEXT DEFAULT (datetime('now')),
  UNIQUE(titolo_norm, anno)
);
CREATE INDEX idx_films_titolo_norm ON films(titolo_norm);

-- Spettacolo: FK su entrambe le tabelle
CREATE TABLE spettacoli (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  film_id      INTEGER NOT NULL REFERENCES films(id) ON DELETE CASCADE,
  cinema_slug  TEXT NOT NULL REFERENCES cinemas(slug) ON DELETE CASCADE,
  data         TEXT NOT NULL,        -- ISO YYYY-MM-DD
  orari        TEXT NOT NULL,        -- JSON array di "HH:MM"
  lingua       TEXT,                 -- "ITA", "ENG", "ORIG-SUB"
  sala         TEXT,
  url_acquisto TEXT,
  scraped_at   TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_spettacoli_data ON spettacoli(data);
CREATE INDEX idx_spettacoli_film ON spettacoli(film_id);
CREATE INDEX idx_spettacoli_cinema ON spettacoli(cinema_slug);
```

**Nota**: questa è la specifica, non il codice da scrivere. Il team la usa come riferimento autorevole.

---

## 7. Roadmap operativa (sprint dettagliati)

### Sprint 2 — Backend MVP (priorità massima)

**Durata stimata**: 5-7 giorni di lavoro effettivo.
**Obiettivo**: backend funzionante che serve i dati dei JSON scraper.

**Task ordinati**:

1. **Setup ambiente** (1h)
   - `python3 -m venv backend/venv && source backend/venv/bin/activate`
   - `pip install -r backend/requirements.txt`
   - `cp backend/.env.example backend/.env`

2. **Eliminare componenti non necessari** post-decisioni D1/D2 (30min)
   - Rimuovere `backend/app/services/tmdb_client.py`.
   - Rimuovere `backend/app/scrapers/` (tutta la cartella).
   - Rimuovere `apscheduler` da `requirements.txt`.
   - Rimuovere `TMDB_API_KEY` e `SCRAPE_CRON` da `.env.example`.

3. **Implementare config.py** (30min) — Pydantic Settings con `database_url`, `cors_origins`, `env`, `log_level`.

4. **Implementare database.py** (30min) — engine SQLAlchemy, SessionLocal, Base, `get_db()` dependency.

5. **Implementare models** (1h) — `Cinema`, `Film`, `Spettacolo` (vedi §6).

6. **Implementare schemas Pydantic** (1h) — `CinemaOut`, `FilmOut`, `FilmDetail`, `SpettacoloOut`.

7. **Implementare repositories** (2h) — query con SQLAlchemy 2.0 (`session.scalars(select(...))`).

8. **Implementare services** (2h) — logica "film con almeno uno spettacolo nel range" + ricerca.

9. **Implementare routers** (2h) — endpoint REST con `Depends(get_db)`.

10. **Implementare main.py** (30min) — `FastAPI()`, CORS middleware, include router, `/health`.

11. **Script seed_from_json.py** (1.5h) — Legge `scraper/output/{cinemas,films,showings}.json` e popola DB. Crea mappatura `{titolo_norm: int_id}` per Film.

12. **Test base** (2h) — `conftest.py` con TestClient + in-memory SQLite. 3-4 test per endpoint principali.

13. **Alembic setup** (30min) — `alembic init alembic`, generate iniziale da modelli.

14. **README backend aggiornato** (30min) — sezione "Quick start funzionante", esempi `curl`.

**Definition of Done**:
- `uvicorn app.main:app --port 8000` parte senza errori.
- `curl http://localhost:8000/api/v1/cinema` ritorna 3 cinema.
- `curl http://localhost:8000/api/v1/film/oggi` ritorna ≥1 film.
- `pytest backend/tests/` verde.
- Swagger UI `/docs` mostra tutti gli endpoint.

### Sprint 3 — App collegamento backend (parallelizzabile con fine Sprint 2)

**Durata stimata**: 3-4 giorni.

1. Aggiungere dipendenze: `npx expo install react-native-maps` + scegliere HTTP (suggerito `axios` o nativo).
2. Sostituire `MOCK_FILMS` con `useEffect+fetch('http://<backend>/api/v1/film/oggi')`.
3. Sostituire `CINEMAS` con fetch da `/api/v1/cinema`.
4. Aggiungere terza tab "Mappa" con `react-native-maps` e 3 marker.
5. Schermata dettaglio film (router dinamico `app/film/[id].jsx`): fetch `/api/v1/film/{id}`, lista spettacoli.
6. Gestione errori + stato di caricamento (spinner + retry).
7. Configurare `app.json` con permessi geolocalizzazione (per centrare la mappa).

**Definition of Done**:
- App su Expo Go mostra dati REALI dal backend.
- Mappa funzionante con 3 marker cliccabili.
- Dettaglio film accessibile dalla home.
- Funziona sia su iOS Expo Go che web build.

### Sprint 4 — Polish + Deploy

1. Migrare codice app da `.jsx` a `.tsx` (TypeScript già installato).
2. Worker Cloudflare: configurare `wrangler.toml`, deploy della web build.
3. Backend deploy su VM Linux (systemd unit + Nginx reverse proxy + Let's Encrypt).
4. Scraper su stessa VM con systemd timer giornaliero.
5. CI: aggiungere job per backend (pytest + ruff) e app (eslint + tsc).
6. Aggiornare `sprint-plan.md` con stato reale.

### Sprint 5 — Extra / nice to have

- Push notifications (RNF, opzionale).
- Ricerca full-text con FTS5 SQLite.
- Filtro geografico (cinema entro X km dalla posizione utente).
- Tema chiaro/scuro.
- Estensione a Terni, Foligno, altri comuni umbri.

---

## 8. Divisione del lavoro (proposta team RepCode)

| Persona | Ownership | Responsabilità Sprint 2-3 |
|---------|-----------|----------------------------|
| **Emanuele** | Scraper (già fatto) + Backend lead | models, repositories, services, seed, deploy |
| **Elio** | Backend co-dev | routers, schemas, test |
| **Andrea** | App lead | fetch, mappa, schermate |
| **Yonas** | DevOps + Worker | Cloudflare, CI, systemd, docs deploy |

> **Memo**: questa è una proposta, da concordare al team meeting prossimo.

---

## 9. Rischi residui e mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Backend non finito per 14/07 | media | alto | Sprint 2 in solitario su Emanuele se team non disponibile; minimum viable = 3 endpoint readonly + seed |
| Mappa non funziona su Expo Go (limitazioni native modules) | bassa | medio | Test precoce; fallback a libreria web `react-native-maps` solo per web build |
| Scraper si rompe (sito target cambia) | media | medio | Già coperto: 75 test + healthcheck + cache + fallback CloakBrowser |
| Wikidata SPARQL rate limit | bassa | basso | Cache locale aggressiva (già implementata); fallback a campi vuoti |
| TMDB scelta poi rivelatasi necessaria | bassa | basso | Decisione D1 reversibile in 1h se servisse |

---

## 10. Checklist pre-presentazione 14/07/2026

- [ ] Backend: tutti endpoint Sprint 2 verdi su `/docs`.
- [ ] App: 3 schermate complete con dati reali (Home, Cinema, Mappa, Dettaglio).
- [ ] Deploy: backend raggiungibile su URL pubblico (anche `http://<vm-ip>:8000` accettabile per demo).
- [ ] Sprint plan ISS aggiornato.
- [ ] Analisi requisiti: ogni RF tracciato a un endpoint o schermata.
- [ ] README principale aggiornato con stato reale.
- [ ] Demo script: 5 min di walkthrough (utente apre app → vede film oggi → tap su mappa → seleziona cinema → vede spettacoli).
- [ ] Slide presentazione (separate da questo doc).

---

## 11. Riferimenti incrociati al wiki

- Architettura layered: [[10 - Fondamenti di progettazione architetturale]] e [[11 - Architectural styles classici]]
- Pattern MVC/MVP/MVVM: [[12 - MVC MVP MVVM]]
- Microservizi vs monolite: [[17 - Microservizi Event-driven CQRS]]
- Test fondamenti: [[18 - Testing fondamenti unit integration system acceptance]]
- CI/CD: [[22 - CI-CD pipeline Jenkins GitHub Actions]]
- Containerizzazione: [[23 - Containerizzazione e IaC Docker Terraform]]
- React Native: [[00 - MOC Mobile]] (MOC RN completo 20/20 ✅)
- FastAPI: [[fastapi]]
- SQLAlchemy: cercare in [[python]] sottocartelle Avanzato/Web-API

---

## 12. Cambiamenti rispetto al piano originale (sprint-plan.md)

Il sprint plan attuale ipotizza un backend "scheletro pronto" che in realtà è solo documentazione. Questo documento sostituisce l'ottimismo con dati misurati:

- Sprint 2 (era "Backend setup + scraper integration") → ora "Backend MVP **da zero** + seed".
- Sprint 3 (era "App skeleton") → ora "App **collegamento al backend + mappa**" (skeleton già fatto come mock).
- Sprint 4 (era "Polish + presentation") → invariato concettualmente, contenuto da aggiornare.

Suggerimento: aggiornare `docs/iss/sprint-plan.md` per rispecchiare la realtà entro la prossima riunione di team.
