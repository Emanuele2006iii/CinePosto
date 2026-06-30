# CinePosto — Piano consegna 14 luglio 2026

> **T-14 giorni**. Oggi 2026-06-30, presentazione 2026-07-14.
> Documento operativo: cosa fare, in che ordine, con quale priorità. Aggiornare daily.

---

## 1. Decisioni cardine (fissate, non rinegoziabili)

| ID | Decisione | Motivo |
|----|-----------|--------|
| **L1** | **Lingua codice = inglese** (identificatori, schema DB, JSON, log). Commenti e doc in italiano. | Coerenza monorepo: lo scraper è già in inglese; il backend va allineato. Niente mapping italiano↔inglese in fase di seed. |
| **L2** | **Backend models in inglese**: `Cinema` (PK `slug`), `Film` (PK `id` int + UNIQUE(`title_normalized`, `year`)), `Showing` (FK su entrambi). | Mappatura 1:1 con i JSON dello scraper. Zero traduzione. |
| **L3** | **Scheduler scraper = systemd timer + `--once`** (NO `--schedule` con APScheduler interno). | Allinea a D2 monorepo. Ogni run isolata, log distinti, restart granulare. |
| **L4** | **Rebrand totale**: tutto "cinemascarper" → "cineposto-scraper". User-Agent Wikidata con email reale. | Igiene + policy WMF. |
| **L5** | **Scope congelato**: niente feature nuove dopo il 2026-07-07. Solo fix e polish. | Margine di 7 giorni per bug + deploy + demo. |

---

## 2. Scope MINIMO (must-have per la demo)

Senza questi 4 punti, la demo non c'è. Sono il **must-have**.

1. **Scraper funzionante in produzione** su VM Linux con systemd timer giornaliero. ✅ già è in produzione, manca solo il deploy.
2. **Backend REST con 5 endpoint readonly funzionanti**:
   - `GET /api/v1/cinemas`
   - `GET /api/v1/films/today`
   - `GET /api/v1/films/{id}`
   - `GET /api/v1/cinemas/{slug}/showings`
   - `GET /health`
3. **App che mostra dati reali** dal backend (Home "Film Oggi" + Cinema list).
4. **Demo deployabile** (anche solo via `expo start` su laptop + backend su laptop + ngrok temporaneo).

## 3. Scope NICE-TO-HAVE (se avanza tempo)

| Feature | Effort | Fallback se non fatto |
|---------|--------|------------------------|
| Mappa interattiva (RF-03) | 1g | Lista cinema con tap → apre sito |
| Schermata dettaglio film | 0.5g | Tap sul film mostra solo gli orari |
| TypeScript migration app | 0.5g | Resta in `.jsx` (basta sia coerente) |
| Endpoint search `/films?q=...` | 0.3g | Skip |
| Endpoint admin reimport | 0.3g | Re-seed manuale via script CLI |
| Deploy VM Linux + nginx + SSL | 1g | Laptop + ngrok per la demo |
| Coverage backend 75% | 0.5g | 50% va bene per MVP |

## 4. Roadmap operativa (gantt 14 giorni)

| Giorno | Data | Cosa | Owner |
|--------|------|------|-------|
| D1 | 06-30 lun | Decisioni L1-L5 + fix scraper urgenti (rebrand, UA) + backend skeleton in inglese | EC |
| D2 | 07-01 mar | Backend: `config.py`, `database.py`, `models/*.py`, `schemas/*.py` | EC |
| D3 | 07-02 mer | Backend: `repositories/*.py` (CRUD readonly + upsert per seed) | EC |
| D4 | 07-03 gio | Backend: `services/*.py`, `routers/*.py`, `main.py` (+ Swagger funzionante) | EC |
| D5 | 07-04 ven | Backend: `seed_from_json.py` + smoke test su JSON reali scraper | EC |
| D6 | 07-05 sab | Backend: test pytest base (3-5 endpoint chiave) + bugfix | EC |
| D7 | 07-06 dom | **MVP backend completo** → handover ai compagni per collegamento app | EC + compagni |
| D8 | 07-07 lun | App: fetch backend + mostra dati reali su Home e Cinema | compagni + EC |
| D9 | 07-08 mar | App: schermata dettaglio film + (se possibile) mappa | compagni + EC |
| D10 | 07-09 mer | App: polish UI (a carico compagni grafica) | compagni |
| D11 | 07-10 gio | **Code freeze** (no feature nuove) + bugfix giro completo | tutti |
| D12 | 07-11 ven | Deploy: VM Linux (scraper + backend systemd unit), oppure fallback ngrok | EC |
| D13 | 07-12 sab | Demo end-to-end provata 3 volte + slide check + script verbale | tutti |
| D14 | 07-13 dom | Buffer / contingency / ripasso | tutti |
| 🎯 | **07-14 lun** | **Presentazione** | tutti |

> **Regola d'oro**: se al D7 il backend MVP non è pronto, taglia: niente mappa, niente migrazione TS, niente endpoint admin. Tieni solo i 5 endpoint must-have.

---

## 5. Fix scraper dettagliati (D1 mattina, ~3 ore)

### 5.1 Rebrand completo `cinemascarper` → `cineposto-scraper`

File da toccare:

| File | Modifica |
|------|----------|
| `scraper/pyproject.toml` | `name = "cinemascarper"` → `"cineposto-scraper"` |
| `scraper/scraper/config.py` | commento + `WIKIDATA_USER_AGENT` con URL reale del repo + email reale |
| `scraper/deploy/cinemascarper.service` | rinominare in `cineposto-scraper.service` + aggiornare `Description=` + `WorkingDirectory=` |
| `scraper/deploy/setup.sh` | `SERVICE_NAME="cineposto-scraper"` |
| `scraper/deploy/cinemascarper-logrotate` | rinominare in `cineposto-scraper-logrotate` + path interni |
| `scraper/README.md` | già fatto |
| `scraper/scraper/main.py` | `description="CinemaScarper - ..."` → `"CinePosto Scraper - Perugia cinema scraper"` |

User-Agent Wikidata target:
```
CinePosto/1.0 (https://github.com/<owner>/cineposto; <tua-email>)
```
Sostituire `<owner>` e `<tua-email>` con valori reali. Anche se il repo GitHub non esiste ancora, mettere un URL **plausibile e che intendi creare**. **L'email DEVE essere funzionante**.

### 5.2 Scheduler systemd timer (allineamento L3)

Sostituire l'attuale `cineposto-scraper.service` (che lancia `--schedule`) con due file:

**`/etc/systemd/system/cineposto-scraper.service`** (oneshot):
```ini
[Unit]
Description=CinePosto Scraper - Single run
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/cineposto/scraper
ExecStart=/home/ubuntu/cineposto/scraper/.venv/bin/python -m scraper.main --once
StandardOutput=journal
StandardError=journal
```

**`/etc/systemd/system/cineposto-scraper.timer`**:
```ini
[Unit]
Description=CinePosto Scraper - daily 03:00 trigger

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=10min

[Install]
WantedBy=timers.target
```

Comando di setup:
```bash
sudo systemctl enable --now cineposto-scraper.timer
sudo systemctl list-timers cineposto-scraper.timer
```

Conseguenza: rimuovere `apscheduler` dal `pyproject.toml` dello scraper (già nelle deps, ma a quel punto non serve più). La funzione `schedule()` in `main.py` può restare come `--schedule` per uso dev locale, ma non viene invocata in prod.

### 5.3 Verifiche dati cinema

In `scraper/scraper/config.py`:
- `uci-perugia` ha `city: "Corciano"`. Verificare con Google Maps:
  - se il cinema sta davvero a Corciano → mantenere slug `uci-perugia` solo come nome storico, oppure rinominare slug a `uci-corciano` per coerenza.
  - se sta a Perugia → correggere `city` e `address`.
- Tutte e 3 le `lat`/`lon` vanno verificate su Google Maps (15 min totali, owner: EC).

### 5.4 Test articoli italiani

Aggiungere a `tests/test_normalizer.py`:
```python
def test_fuzzy_handles_italian_articles():
    assert not fuzzy_match("Il Pianeta del Tesoro", "Il Cavaliere Oscuro")
    assert fuzzy_match("Il Cavaliere Oscuro", "Cavaliere Oscuro")  # con articolo dropping ok
    assert not fuzzy_match("Il Cavaliere Oscuro", "Il Cavaliere Oscuro - Il Ritorno")
```
Se questo terzo test fallisce, regolare `_TITLE_SUFFIXES` per non strippare il sottotitolo dopo `-` quando il sottotitolo inizia per articolo.

### 5.5 Coverage gate 60 → 75

In `scraper/pyproject.toml` e `.github/workflows/ci.yml`:
```yaml
run: pytest tests/ --cov --cov-report=term-missing --cov-fail-under=75
```
Verificare prima che `pytest --cov` vada sopra 75 con i test attuali. Se no, aggiungere i 2 file mancanti (`test_browser.py`, `test_errors.py` — mock leggeri).

---

## 6. Fix backend skeleton (D1 pomeriggio, ~2 ore)

Riallineare i TODO Python all'inglese (decisione L1+L2). I file da toccare sono **solo metadati/specifiche**, non codice eseguibile (i TODO restano TODO).

| File | Modifica |
|------|----------|
| `backend/app/models/cinema.py` | `class Cinema`, campi `slug/name/city/address/region/lat/lon/website/phone` |
| `backend/app/models/film.py` | `class Film`, campi `id/title/title_normalized/original_title/year/runtime_minutes/genres/director/poster_url/synopsis/wikidata_id/created_at` |
| `backend/app/models/spettacolo.py` | **rinominare in `showing.py`**, `class Showing`, campi `id/film_id/cinema_slug/date/times/language/screen/buy_url/scraped_at` |
| `backend/app/schemas/cinema.py` | `CinemaOut`, `CinemaWithCount` (campi inglesi) |
| `backend/app/schemas/film.py` | `FilmOut`, `FilmDetail` |
| `backend/app/schemas/spettacolo.py` | rinominare in `showing.py`, `ShowingOut`, `ShowingDetail` |
| `backend/app/repositories/spettacolo_repo.py` | rinominare in `showing_repo.py` |
| `backend/app/routers/spettacoli.py` | rinominare in `showings.py`, `prefix="/showings"` |
| `backend/app/services/cinema_service.py` | metodi inglesi (`list_cinemas`, `find_nearby`, `get_schedule`) |
| `backend/app/services/film_service.py` | metodi inglesi (`search_films`, `films_today`, `get_detail`) |
| `docs/backend/schema-mapping.md` | aggiornare tabelle con nomi colonna inglesi |
| `backend/.env.example` | nessun cambio (è già in inglese) |
| `docs/backend/architecture.md` | aggiornare schema DB e endpoint con nomi inglesi |

Endpoint definitivi (post-rename):

```
GET  /api/v1/cinemas
GET  /api/v1/cinemas/nearby?lat&lon&radius_km
GET  /api/v1/cinemas/{slug}
GET  /api/v1/cinemas/{slug}/showings
GET  /api/v1/films/today
GET  /api/v1/films/search?q=...
GET  /api/v1/films/{id}
GET  /api/v1/showings?date&cinema_slug&film_id
GET  /api/v1/showings/today
POST /api/v1/admin/reimport
GET  /api/v1/admin/dataset-info
GET  /health
```

Path completi: `cinemas` (plural), `films` (plural), `showings` (plural).

---

## 7. Backend MVP — checklist task (D2-D7)

Ogni task ha un **DoD** (Definition of Done) verificabile.

### D2 (07-01) — Foundation

- [ ] `config.py` → `Settings(BaseSettings)` con `database_url`, `scraper_output_dir`, `cors_origins`, `admin_token`. **DoD**: `python -c "from app.config import get_settings; print(get_settings())"` stampa i valori dal `.env`.
- [ ] `database.py` → `Base`, `engine`, `SessionLocal`, `get_db()`. PRAGMA `foreign_keys=ON`. **DoD**: importazione senza errori; `engine.connect()` apre file `cineposto.db`.
- [ ] `models/cinema.py`, `models/film.py`, `models/showing.py` (rinominato). Tutti con `Mapped[]` di SQLAlchemy 2.0. Vincoli UNIQUE. **DoD**: `Base.metadata.create_all(engine)` crea le 3 tabelle nel DB.
- [ ] `schemas/cinema.py`, `schemas/film.py`, `schemas/showing.py` con `ConfigDict(from_attributes=True)`. **DoD**: `FilmOut.model_validate(film_orm_instance)` non solleva.

### D3 (07-02) — Data access

- [ ] `repositories/cinema_repo.py`: `get_by_slug`, `list_all`, `upsert`. **DoD**: 3 cinema seedati ritornati da `list_all`.
- [ ] `repositories/film_repo.py`: `get_by_id`, `get_by_natural_key`, `search_by_title`, `list_in_programming`, `upsert_from_scraper`. **DoD**: test idempotenza upsert (chiamarlo 2 volte non duplica).
- [ ] `repositories/showing_repo.py`: `list_by_date`, `list_by_cinema`, `list_by_film`, `upsert`, `delete_old`. **DoD**: 310 showing seedati ritornati per date corrette.

### D4 (07-03) — API surface

- [ ] `services/film_service.py` con `normalize_title()` (la stessa logica dello scraper, copiata per indipendenza).
- [ ] `services/cinema_service.py` con `haversine_km()` per `find_nearby`.
- [ ] Tutti i `routers/*.py` con `Depends(get_db)`. CORS middleware. `/health` endpoint.
- [ ] `main.py` con `create_app()` factory.
- [ ] **DoD**: `uvicorn app.main:app` parte, `/docs` mostra tutti gli endpoint, `curl /health` ritorna `{"status":"ok"}`.

### D5 (07-04) — Seed

- [ ] `app/seed.py`: legge `scraper_output_dir/{cinemas,films,showings}.json`, fa upsert in ordine FK, costruisce lookup titolo→id. **DoD**: `python -m app.seed` su JSON reali → DB con 3 cinema, 22 film, 310 showing. Eseguito 2 volte di seguito → stessi numeri (idempotenza).
- [ ] Smoke end-to-end: `curl /api/v1/cinemas` → 3 record. `curl /api/v1/films/today` → ≥1 record con `showings` popolato.

### D6 (07-05) — Test

- [ ] `tests/conftest.py` con TestClient FastAPI + SQLite in-memory + fixture `seeded_db`.
- [ ] `tests/test_cinemas.py`: GET list, GET by slug, 404 su slug inesistente.
- [ ] `tests/test_films.py`: GET today, GET by id, search.
- [ ] `tests/test_seed.py`: seed da fixture JSON minimale → conteggi corretti + idempotenza.
- [ ] **DoD**: `pytest backend/tests/` verde, coverage ≥50%.

### D7 (07-06) — Handover

- [ ] README backend con quickstart **funzionante** (provarlo da venv pulito).
- [ ] OpenAPI export: `curl http://localhost:8000/openapi.json > openapi.json` → committed in repo per i compagni che fanno l'app.
- [ ] Postman/Bruno collection o file `requests.http` per testing rapido.
- [ ] **DoD**: un compagno apre il repo, segue il README, in 10 minuti ha il backend in piedi e fa curl agli endpoint.

---

## 8. App task (D8-D10) — supporto ai compagni

Owner: compagni (grafica). EC supporto tecnico.

- [ ] Aggiungere `axios` o usare `fetch` nativo per chiamate API.
- [ ] Variabile `API_BASE_URL` letta da `process.env.EXPO_PUBLIC_API_URL` (oppure hardcoded inizialmente).
- [ ] `app/src/app/(tabs)/index.jsx`: sostituire `MOCK_FILMS` con `useEffect + fetch('/api/v1/films/today')`. Loading state + errore.
- [ ] `app/src/app/(tabs)/cinema.jsx`: stesso pattern con `/api/v1/cinemas`.
- [ ] (Opzionale) `app/src/app/film/[id].jsx` route dinamica per dettaglio.
- [ ] (Opzionale) `app/src/app/(tabs)/map.jsx` con `react-native-maps` (3 marker).

Comando per installare la mappa quando serve:
```bash
cd app && npx expo install react-native-maps
```

---

## 9. Deploy (D12) — 2 strade

### Strada A — VM Linux (preferibile)

Prerequisiti: VM Ubuntu 22.04+ accessibile via SSH.

1. `git clone` del monorepo (o rsync di scraper/ e backend/).
2. Scraper: `python3 -m venv scraper/.venv && source scraper/.venv/bin/activate && pip install -e ".[dev]"`.
3. Systemd timer scraper installato (vedi §5.2).
4. Backend: `python3 -m venv backend/venv && pip install -r backend/requirements.txt`, seed iniziale, systemd unit `cineposto-backend.service` (vedi sotto).
5. Nginx reverse proxy con SSL via Let's Encrypt (1 ora di setup).

**`cineposto-backend.service`**:
```ini
[Unit]
Description=CinePosto Backend FastAPI
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cineposto/backend
EnvironmentFile=/home/ubuntu/cineposto/backend/.env
ExecStart=/home/ubuntu/cineposto/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Strada B — Fallback: laptop + ngrok (per demo emergenza)

Se la VM non si fa in tempo:

```bash
# Terminal 1: scraper standalone
cd cineposto/scraper && source .venv/bin/activate && python -m scraper.main --once

# Terminal 2: backend
cd cineposto/backend && source venv/bin/activate && python -m app.seed && uvicorn app.main:app --port 8000

# Terminal 3: ngrok per esporre il backend
ngrok http 8000  # copia l'URL https://xxx.ngrok-free.app

# App: aggiornare API_BASE_URL all'URL ngrok
```

Funziona per la demo, NON è una soluzione duratura.

---

## 10. Checklist pre-demo (D13)

- [ ] Provare la demo end-to-end **3 volte di seguito** (variazioni: device fisico, device emulato, web).
- [ ] Verificare che lo scraper abbia girato di recente (`ls -la scraper/output/*.json`).
- [ ] Verificare che il DB sia popolato (`sqlite3 backend/cineposto.db "SELECT COUNT(*) FROM films"`).
- [ ] Backup `.env` e `cineposto.db` su una chiavetta o cloud.
- [ ] Slide deck pronto (a cura di chi se ne occupa).
- [ ] Script verbale demo: chi parla quando, ordine degli step.
- [ ] Battery laptop carica + caricabatterie + cavo HDMI/USB-C → proiettore.
- [ ] Connessione internet stabile (hotspot di backup pronto).
- [ ] Una persona del team con il backend in locale come fallback se quello demo schianta.

---

## 11. Rischi e mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Backend non finito al D7 | media | alto | Scope congelato al §2; tagliare nice-to-have aggressivamente |
| Scraper si rompe in settimana (sito cambia HTML) | bassa | alto | I JSON attuali sono freschi (25/06); se domani lo scraper fallisce, **commit dei JSON correnti come "demo dataset" e seedare quelli** |
| Mappa non funziona su Expo Go | media | medio | Fallback: lista cinema con tap → apre sito |
| Deploy VM non pronto | media | medio | Strada B (ngrok) come fallback |
| Bug demo durante la presentazione | bassa | alto | Avere uno screenshot/video di backup di ogni schermata |
| Compagni grafica in ritardo | media | basso | UI brutta è meglio di nessuna UI — non bloccarli, demo va avanti |

---

## 12. Log decisioni / aggiornamenti daily

> Aggiornare ogni sera con 2 righe: cosa fatto, cosa pendente.

### 2026-06-30 (D1) — completato

**Scraper rebrand**:
- ✅ `pyproject.toml`: `name = "cineposto-scraper"`
- ✅ `config.py`: commento + `WIKIDATA_USER_AGENT` aggiornato (con TODO email/repo reali da finalizzare)
- ✅ `main.py`: argparse description + commento `--schedule` (dev only)
- ✅ Deploy files: `cineposto-scraper.{service,timer,logrotate}` + `setup.sh` riscritti per systemd timer + `--once` (L3)
- ✅ Vecchi `cinemascarper.*` rimossi
- ✅ 75/75 test verdi dopo rebrand

**Backend riallineamento inglese (L1+L2)**:
- ✅ Rinominati: `spettacolo.py` → `showing.py` (in models, schemas, repositories, routers)
- ✅ Tutti i TODO Python aggiornati con campi inglesi (`title/year/runtime_minutes/director/synopsis/showings/buy_url`)
- ✅ `schema-mapping.md` riscritto con nomi inglesi
- ✅ `docs/backend/architecture.md` riscritto con nomi inglesi + decisioni L1-L5
- ✅ `main.py` import aggiornati a `showings` (era `spettacoli`)

**Pendente per finalizzazione**:
- ⚠️ `WIKIDATA_USER_AGENT` ha placeholder `<GH_OWNER>`: sostituire con username GitHub reale (`Emanuele2006iii`) prima del deploy
- ⚠️ Coordinate UCI da verificare su Google Maps
- ⚠️ Test articoli IT in `test_normalizer.py` (vedi §5.4)

### 2026-06-30 (D1 SERA) — completato anche D2 parziale

**Setup ambiente backend**:
- ✅ venv Python 3.12 (era 3.14 di default, incompatibile con pydantic-core 2.27)
- ✅ Tutte le dipendenze installate (fastapi 0.115, sqlalchemy 2.0.36, pydantic 2.10, ecc.)
- ✅ `.env` creato da `.env.example`, CORS_ORIGINS in formato JSON array

**`config.py` implementato**:
- ✅ Settings(BaseSettings) con `database_url`, `scraper_output_dir`, `cors_origins`, `env`, `log_level`, `admin_token`
- ✅ `get_settings()` con `@lru_cache`
- ✅ Smoke test verde: legge .env correttamente

**`database.py` implementato**:
- ✅ `Base(DeclarativeBase)` SQLAlchemy 2.0
- ✅ `engine` con `check_same_thread=False` per SQLite
- ✅ `SessionLocal` + `get_db()` dependency
- ✅ PRAGMA `foreign_keys=ON` via event listener (testato: FK abilitate)
- ✅ Smoke test verde: `SELECT 1` ritorna 1, foreign_keys ON

**3 modelli SQLAlchemy implementati**:
- ✅ `Cinema` (PK = slug stringa)
- ✅ `Film` (PK intera + UNIQUE(title_normalized, year) + UNIQUE(wikidata_id))
- ✅ `Showing` (FK su film_id intera + cinema_slug string + UNIQUE(film_id, cinema_slug, date) + 3 indici)
- ✅ Smoke test verde: `Base.metadata.create_all` crea 3 tabelle con tutti vincoli e indici

**Git setup monorepo CinePosto (bonus, non era nel piano)**:
- ✅ `scraper/.git` interno rimosso (lo scraper ora è parte del monorepo)
- ✅ `.gitignore` triplo audit (root + backend + scraper): zero file pericolosi
- ✅ Init repo cineposto/ su branch `main`
- ✅ Remote configurati: `origin` = fork (Emanuele2006iii), `upstream` = repo Yonas
- ✅ Primo commit: 122 file, 28310 inserzioni (root-commit f097086)
- ✅ GitHub CLI (`gh`) installato + autenticazione OAuth
- ✅ Push --force sul fork riuscito
- ✅ Audit post-commit: 0 segreti, 0 cache, 0 file temporanei, 2.1 MB di repo

### 2026-07-01 (D2) — TODO

**Backend — completare layer dati**:
- [ ] schemas/{cinema,film,showing}.py (DTO Pydantic)
- [ ] repositories/{cinema,film,showing}_repo.py (CRUD readonly + upsert)

### 2026-07-02 (D3) — TODO
- [ ] services/{cinema,film}_service.py
- [ ] routers/{cinema,film,showings,admin}.py
- [ ] main.py (`create_app()` + CORS + Swagger)
- [ ] Smoke: `uvicorn app.main:app` → `/docs` mostra endpoint
