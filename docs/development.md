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
python3 -m scraper.main --once      # run singolo
python3 -m scraper.main --schedule  # scheduling automatico ogni 24h
python3 healthcheck.py              # ping ai 3 endpoint
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
uvicorn app.main:app --reload --port 8000
```

Swagger UI disponibile su `http://localhost:8000/docs`.

---

## App (React Native)

SDK 54 installata, navigazione tab funzionante. **NON usare `create-expo-app`** — installa SDK 55+ incompatibile con Expo Go.

```bash
cd app
npx expo start           # avvia Metro bundler + QR code per Expo Go
npx expo start --web     # solo web build (browser)
npx expo export --platform web  # build statica per Cloudflare Pages
```

Vedi setup completo in [docs/app/overview.md](app/overview.md).

---

## Deploy scraper su Linux

```bash
./scraper/deploy/setup.sh   # installa systemd timer + service oneshot + logrotate

sudo systemctl list-timers cineposto-scraper.timer       # prossima esecuzione schedulata
sudo systemctl status cineposto-scraper.service          # ultima run
sudo systemctl start cineposto-scraper.service           # forza run manuale subito
sudo journalctl -u cineposto-scraper.service -f --since "1 hour ago"
```
