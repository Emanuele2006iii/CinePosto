# CinePosto

Aggregatore cinema dell'Umbria — app mobile React Native + backend FastAPI + scraper Python.

> **Stato (2026-07-02)**:
> - **Scraper** ✅ produzione (75 test, ruff pulito, 3 connettori). Ora arricchisce anche `year` (P577 Wikidata) e `wikidata_id`.
> - **Backend** ✅ **Sprint 2 completato**: FastAPI attiva con 11 endpoint funzionanti, seed dai JSON scraper, 26 test verdi.
> - **App mobile** 🟡 2 schermate con dati hardcoded (Sprint 3 non iniziato — fetch al backend + mappa da aggiungere).
> - **Worker Cloudflare** 🟡 stub (Sprint 4).
>
> 📖 **Panoramica completa del sistema** → [`docs/panoramica.md`](docs/panoramica.md) (architettura, decisioni di design, qualità)
> 📱 **Guida integrazione frontend** → [`docs/backend/api.md`](docs/backend/api.md) (contratto API + tipi JSDoc + esempi fetch)

---

## Struttura monorepo

```
cineposto/
├── scraper/     # Pipeline dati: raccoglie programmazione da 3 cinema → JSON
├── backend/     # API FastAPI (SQLite): serve i dati all'app
├── worker/      # Cloudflare Pages: hosting web build React Native
└── app/         # App React Native (Expo) — mobile + web da unica codebase
```

---

## Componenti

### `scraper/`
Pipeline Python autonoma. Produce 4 file JSON in `scraper/output/`:
- `movies.json` — stato interno con history (usato tra run)
- `films.json` — tabella `films` DB-ready (ora include `year`, `wikidata_id`, `duration`)
- `showings.json` — tabella `showings` DB-ready
- `cinemas.json` — tabella `cinemas` DB-ready

```bash
cd scraper
pip install -e ".[dev]"          # installa scraper + dipendenze dev
python3 -m scraper.main --once
```

Vedi `scraper/README.md` per dettagli.

### `backend/` ✅
FastAPI + SQLite. Legge i JSON prodotti dallo scraper e li espone via REST.

**Architettura layered** (Sommerville §6.3):
```
routers/ → services/ → repositories/ → models/
```

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Seed DB dai JSON scraper
python -m app.seed_from_json

# Avvia API
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: `http://localhost:8000/docs`
- Test: `pytest tests/` (26 test)

### `worker/`
Cloudflare Pages — distribuisce la web build di React Native (gratis, CDN globale).

### `app/`
React Native Expo SDK 54 — navigazione tab funzionante con **2 schermate a dati hardcoded** (`MOCK_FILMS`, `CINEMAS`). Nessun fetch verso il backend, mappa interattiva (RF-03) ancora da aggiungere (`react-native-maps`). TypeScript installato ma codice in `.jsx`. Vedi `docs/backend/api.md` per il contratto API e la roadmap di collegamento.

```bash
cd app
npx expo start
```

---

## Roadmap

- [x] Scraper 3 cinema funzionante (PostModernissimo, The Space, UCI)
- [x] Arricchimento Wikidata (poster, regista, titolo originale, durata, **year, wikidata_id**)
- [x] Output JSON separato (cinemas / films / showings)
- [x] **Sprint 2**: backend FastAPI completo — models SQLAlchemy + schemas Pydantic + repositories CRUD + services + 11 endpoint REST + seed da JSON + 26 test
- [x] Inizializzare app React Native (Expo SDK 54, navigazione tab, schermate mock)
- [ ] **Sprint 3**: collegare app al backend + aggiungere mappa (RF-03)
- [ ] **Sprint 4**: deploy web build su Cloudflare Pages + backend su VM Linux

---

## Documentazione

Tutta la documentazione è in [`docs/`](docs/index.md), organizzata per componente.

| Documento | Descrizione |
|---|---|
| [`docs/index.md`](docs/index.md) | Catalogo navigabile di tutta la documentazione |
| [`docs/development.md`](docs/development.md) | Testing, lint, setup locale, variabili d'ambiente |
| [`docs/backend/api.md`](docs/backend/api.md) | **Contratto API per il team frontend** (endpoint, tipi JSDoc, esempi) |
| [`docs/scraper/architecture.md`](docs/scraper/architecture.md) | Architettura tecnica scraper |
| [`docs/backend/architecture.md`](docs/backend/architecture.md) | Architettura tecnica backend |
| [`docs/backend/schema-mapping.md`](docs/backend/schema-mapping.md) | Mapping JSON scraper → tabelle DB |
| [`docs/app/overview.md`](docs/app/overview.md) | Overview app React Native |
