# Guida allo sviluppo

## Prerequisiti

- Python 3.12+
- Node.js 20+ (solo per app React Native)

---

## Scraper

### Setup

```bash
cd scraper
pip install -e ".[dev]"    # installa scraper + dipendenze dev (pytest, ruff, responses)
```

### Lint + test (comando canonico)

```bash
python3 -m ruff check scraper/ tests/ && python3 -m pytest tests/ -q
```

### Test con coverage

```bash
python3 -m pytest tests/ --cov --cov-report=term-missing
```

### Esecuzione manuale

```bash
python3 -m scraper.main --once      # run singolo (è quello che usa systemd in produzione — L3)
python3 -m scraper.main --schedule  # SOLO DEV: loop APScheduler ogni 24h (richiede extra [dev])
python3 healthcheck.py              # ping ai 3 endpoint
```

### Modifiche ai metadati o alle costanti cinema

Se cambi:
- `scraper/scraper/config.py` → `CINEMA_LOCATIONS` (nomi/indirizzi/coordinate)
- `scraper/scraper/metadata.py` → estrazione Wikidata (nuovi campi, nuove property)

...ricordati di **invalidare la cache Wikidata** prima di rilanciare, altrimenti riusa i vecchi risultati senza i nuovi campi:

```bash
rm scraper/.wikidata_cache.json
python3 -m scraper.main --once
```

Poi rigenera i JSON e reseed backend:

```bash
cd ../backend && source venv/bin/activate
rm cineposto.db
python -m app.seed_from_json
```

### Variabili d'ambiente

| Variabile | Default | Descrizione |
|---|---|---|
| `SCRAPER_TZ` | `Europe/Rome` | Fuso orario per calcolo "oggi" — importante se server è in UTC |
| `SCRAPER_LOG_LEVEL` | `INFO` | Livello di log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CLOAKBROWSER_HEADLESS` | `true` | CloakBrowser in modalità headless |
| `CLOAKBROWSER_FINGERPRINT_SEED` | `42069` | Seed fingerprint anti-detection |

---

## Backend

### Setup

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Seed del DB (una volta al primo avvio)

```bash
# Legge i JSON prodotti dallo scraper e popola cineposto.db
python -m app.seed_from_json
```

Da rilanciare **ogni volta che lo scraper aggiorna i JSON** (o via endpoint
admin `POST /api/v1/admin/reimport` col token in `X-Admin-Token`).

### Avvio server

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`.

### Test

```bash
python -m pytest tests/ -q       # 26 test (~0.15s)
python -m pytest tests/ -v       # verbose
```

Setup dei test:
- `conftest.py` — SQLite in-memory + `StaticPool` + override di `get_db`
- `test_repositories.py` — 14 unit test sui repository
- `test_routers.py` — 12 end-to-end via TestClient FastAPI

### Variabili d'ambiente (`.env`)

| Variabile | Default | Descrizione |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./cineposto.db` | Path DB. In dev SQLite locale, in prod idem (D4) |
| `SCRAPER_OUTPUT_DIR` | `../scraper/output` | Cartella JSON scraper (risolto a path assoluto) |
| `CORS_ORIGINS` | *(dev defaults)* | JSON array; se vuoto usa `localhost:8081/19006/3000` |
| `ENV` | `development` | `development` → SQL echo + `create_all` in lifespan |
| `LOG_LEVEL` | `INFO` | |
| `ADMIN_TOKEN` | *(auto-generato)* | Se vuoto o `"change-me-before-deploy"`, il backend genera un token random e lo stampa una volta al boot |

---

## App (React Native)

App integrata e collegata al backend (React Navigation, Expo SDK 54). **NON usare
`create-expo-app`** — installa SDK 55+ incompatibile con Expo Go.

```bash
cd app
npm install
# IP LAN del Mac (macOS): ipconfig getifaddr en0
EXPO_PUBLIC_API_BASE="http://<IP-LAN>:8000/api/v1" npx expo start
```

- **Web**: apri `http://localhost:8081` (o premi `w`).
- **Telefono**: Expo Go → scansiona il QR (telefono e backend sulla stessa Wi-Fi).
- **Build web statica**: `npx expo export --platform web` → `dist/`.

Il backend dev'essere in esecuzione su `0.0.0.0:8000` con il DB seedato. Setup
completo in [docs/app/overview.md](app/overview.md).

---

## Deploy scraper su Linux

```bash
./scraper/deploy/setup.sh   # installa systemd timer + service oneshot + logrotate

sudo systemctl list-timers cineposto-scraper.timer       # prossima esecuzione schedulata
sudo systemctl status cineposto-scraper.service          # ultima run
sudo systemctl start cineposto-scraper.service           # forza run manuale subito
sudo journalctl -u cineposto-scraper.service -f --since "1 hour ago"
```
