# CinePosto

Aggregatore della programmazione dei cinema dell'Umbria. Uno scraper Python raccoglie ogni notte i film in cartellone da tre cinema — PostModernissimo, The Space Corciano, UCI Perugia — un backend FastAPI li serve via API REST e un'app React Native li mostra su web e smartphone dalla stessa codebase. Nessuna registrazione: apri e vedi cosa danno stasera.

Progetto di gruppo per il corso di Ingegneria del Software (ITS Umbria Academy, a.a. 2025/2026, prof. Montecchiani). Team RepCode: Emanuele, Elio, Andrea, Yonas.

## Com'è fatto

```
cineposto/
├── scraper/   pipeline Python: legge i siti dei 3 cinema → 3 file JSON
├── backend/   API FastAPI su SQLite: importa i JSON e li espone via REST
├── app/       app React Native (Expo): consuma l'API, gira su web e mobile
└── docs/      documentazione tecnica e del corso
```

È una pipeline in tre stadi collegati da contratti espliciti: file JSON tra scraper e backend, API REST tra backend e app. Ogni stadio è indipendente e si testa da solo — 101 test in tutto, 75 sullo scraper e 26 sul backend.

## Avvio rapido

### Backend

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate   # serve Python 3.12
pip install -r requirements.txt
cp .env.example .env
python -m app.seed_from_json          # popola il DB dai JSON dello scraper
uvicorn app.main:app --reload --port 8000
```

Swagger su `http://localhost:8000/docs` (11 endpoint). Test: `pytest tests/`.

### App

```bash
cd app
npm install
# IP LAN del Mac: ipconfig getifaddr en0
EXPO_PUBLIC_API_BASE="http://<IP-LAN>:8000/api/v1" npx expo start
```

Web su `http://localhost:8081`, telefono con Expo Go sulla stessa Wi-Fi. Non usare `create-expo-app`: installa un SDK troppo recente per Expo Go.

### Scraper

```bash
cd scraper
pip install -e ".[dev]"
python3 -m scraper.main --once
```

Produce i JSON in `scraper/output/`. In produzione gira con un systemd timer (file pronti in `scraper/deploy/`).

## Documentazione

Tutto in [`docs/`](docs/index.md). Da dove partire:

| Documento | A cosa serve |
|---|---|
| [`docs/panoramica.md`](docs/panoramica.md) | Il sistema spiegato da cima a fondo |
| [`docs/presentazione-14-luglio.md`](docs/presentazione-14-luglio.md) | Scaletta, script della demo e domande del prof per l'esposizione |
| [`docs/development.md`](docs/development.md) | Setup, test, lint, variabili d'ambiente |
| [`docs/backend/api.md`](docs/backend/api.md) | Contratto API completo |

## Stato

Scraper, backend e app sono completi e funzionano end-to-end. Fuori dallo scope dell'MVP, e quindi non realizzati per scelta: account utente, acquisto in-app, notifiche. Ricerca in-app e avviso "dati non aggiornati" sono rimandati alla Release 1.1.
