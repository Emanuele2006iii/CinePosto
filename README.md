# CinePosto

Aggregatore cinema dell'Umbria — app mobile React Native + backend FastAPI + scraper Python.

> **Stato (2026-06-30)**:
> - **Scraper** ✅ produzione (75 test, ruff pulito, 3 connettori, output JSON aggiornato 25/06/2026 — 22 film, 310 spettacoli, 3 cinema)
> - **Backend** 🔴 solo struttura di file e documentazione (i sorgenti Python contengono esclusivamente docstring + TODO, nessuna riga eseguibile)
> - **App mobile** 🟡 2 schermate con dati hardcoded (nessun fetch al backend, mappa assente)
> - **Worker Cloudflare** 🟡 stub
>
> 📖 **Piano completo di continuazione** → [`docs/CONTINUAZIONE-PROGETTUALE.md`](docs/CONTINUAZIONE-PROGETTUALE.md) (decisioni di design, sprint, divisione lavoro, schema DB target)

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
- `films.json` — tabella `films` DB-ready
- `showings.json` — tabella `showings` DB-ready
- `cinemas.json` — tabella `cinemas` DB-ready

```bash
cd scraper
pip install -e ".[dev]"          # installa scraper + dipendenze dev
python3 -m scraper.main --once
```

Vedi `scraper/README.md` per dettagli.

### `backend/`
FastAPI + SQLite. Una volta implementato, leggerà i JSON prodotti dallo scraper e li esporrà via REST.

**Architettura layered prevista** (Sommerville §6.3):
```
routers/ → services/ → repositories/ → models/
```

> ⚠️ **Avviso**: ad oggi i file Python del backend contengono solo docstring + commenti `TODO`. Il comando `uvicorn app.main:app` fallisce con `ImportError`. Vedi `docs/CONTINUAZIONE-PROGETTUALE.md` §2.2 e §7 per lo stato dettagliato e la roadmap.

```bash
# Comandi previsti DOPO l'implementazione (Sprint 2):
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Swagger UI (post-implementazione): `http://localhost:8000/docs`

### `worker/`
Cloudflare Pages — distribuisce la web build di React Native (gratis, CDN globale).

### `app/`
React Native Expo SDK 54 — navigazione tab funzionante con **2 schermate a dati hardcoded** (`MOCK_FILMS`, `CINEMAS`). Nessun fetch verso il backend, mappa interattiva (RF-03) ancora da aggiungere (`react-native-maps`). TypeScript installato ma codice in `.jsx`. Vedi `docs/CONTINUAZIONE-PROGETTUALE.md` §7 Sprint 3 per la roadmap di collegamento.

```bash
cd app
npx expo start
```

---

## Roadmap

- [x] Scraper 3 cinema funzionante (PostModernissimo, The Space, UCI)
- [x] Arricchimento Wikidata (poster, regista, titolo originale, durata)
- [x] Output JSON separato (cinemas / films / showings)
- [x] Struttura cartelle backend FastAPI (routers, services, repositories, models, schemas) — **solo struttura, sorgenti = TODO**
- [ ] **Sprint 2**: implementare backend (models SQLAlchemy + repositories CRUD + endpoint REST + seed da JSON) — vedi `docs/CONTINUAZIONE-PROGETTUALE.md` §7
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
| [`docs/scraper/architecture.md`](docs/scraper/architecture.md) | Architettura tecnica scraper |
| [`docs/backend/architecture.md`](docs/backend/architecture.md) | Architettura tecnica backend |
| [`docs/app/overview.md`](docs/app/overview.md) | Overview app React Native |
