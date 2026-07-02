# CinePosto — Scraper

Scraper Python che raccoglie la programmazione di 3 cinema di Perugia e produce JSON statici aggiornati ogni 24 ore. Componente del monorepo CinePosto.

## Cinema supportati

| Cinema | Metodo accesso | Note |
|---|---|---|
| PostModernissimo | HTML + parser RSC (Next.js) | Nessun anti-bot |
| The Space Cinema Corciano | API REST OAuth2 | Fallback CloakBrowser se API giù |
| UCI Cinemas Perugia | API Cloud Run (non documentata) | Il sito principale è bloccato da Cloudflare |

## Installazione

```bash
# Installazione minima (runtime)
pip install -e .

# Installazione con dipendenze dev
pip install -e ".[dev]"
```

Il progetto usa **solo `pyproject.toml`** come fonte di verità — non esistono più `requirements.txt` / `requirements-dev.txt`.

## Sviluppo

```bash
# Lint + test (comando canonico)
python3 -m ruff check scraper/ tests/ && python3 -m pytest tests/ -q

# Test con coverage
python3 -m pytest tests/ --cov --cov-report=term-missing
```

## Utilizzo

```bash
# Esecuzione singola
python3 -m scraper.main --once

# Con scheduling automatico ogni 24h
python3 -m scraper.main --schedule

# Test offline (non richiede rete)
python3 -m pytest tests/ -v

# Healthcheck endpoint dei 3 cinema (no scraping completo)
python3 healthcheck.py
```

`healthcheck.py` esegue una ping rapida ai 3 endpoint (PostModernissimo home, The Space auth, UCI programming API) e ritorna exit code 0 se tutti rispondono, 1 in caso contrario. Utile per monitoring esterno (cron, Uptime Kuma, ecc.).

## Output

### File prodotti

| File | Contenuto |
|---|---|
| `output/movies.json` | Stato interno: film con `present_in` e `history[]` (usato tra run) |
| `output/films.json` | Tabella `films` DB-ready (id, title, poster, genres, director…) |
| `output/showings.json` | Tabella `showings` DB-ready (film_id FK, cinema_slug FK, date, times[]) |
| `output/cinemas.json` | Tabella `cinemas` DB-ready (slug PK, name, lat, lon, website) |
| `output/errors.json` | Errori accumulati per cinema |
| `output/cache/{slug}.json` | Cache per-cinema (fallback se il sito è giù) |
| `output/history/movies_{date}.json` | Snapshot giornaliero |
| `scraper.log` | Log testuale di ogni esecuzione |

### Struttura `movies.json`

```json
{
  "generated_at": "2026-06-24T10:00:00",
  "city": "Perugia",
  "films": [
    {
      "title": "Nome Film",
      "title_normalized": "nome film",
      "poster": "https://...",
      "description": "Trama del film",
      "genres": ["Drama", "Thriller"],
      "director": "Nome Regista",
      "original_title": "Original English Title",
      "duration": "120 min",
      "status": "in_programmazione",
      "present_in": [
        {
          "cinema": "UCI Cinemas Perugia",
          "cinema_slug": "uci-perugia",
          "date": "2026-06-24",
          "times": ["18:00", "20:30"],
          "screen": "2D",
          "language": "ITA"
        }
      ],
      "history": [
        {"date": "2026-06-20", "action": "added"}
      ]
    }
  ],
  "errors": []
}
```

**Campi che possono essere `null`:** `poster`, `description`, `director`, `original_title`, `duration`, `genres`, `screen`, `language`, `year`, `wikidata_id` — dipende dalla fonte e dalla disponibilità su Wikidata.

**Nuovi campi dal 2026-07-02** (nel JSON `films.json`):
- `year` (int) — estratto da Wikidata P577 (data pubblicazione)
- `wikidata_id` (string) — entity_id Wikidata (es. `"Q97154362"`), utile per future re-importazioni di metadati e come UNIQUE nel DB backend

Copertura misurata su 19 film del dataset attuale: `poster` 100%, `description` 100%, `director` 95%, `duration` 74%, `genres` 69%, `year`/`wikidata_id` 37% (film di nicchia non su Wikidata).

**Campi non presenti per scelta:** `rating` (API commerciali non usate), `price` (richiederebbe scraping aggiuntivo fragile su ogni cinema).

## Architettura

```
scraper/
├── main.py              # Entry point e orchestrazione
├── config.py            # Costanti, URL, path, timezone
├── models.py            # Dataclass Film, Showing, CinemaError, ScrapeResult
├── delta.py             # Merge con run precedente, storico history
├── errors.py            # Scrittura errors.json
├── metadata.py          # Enrichment Wikidata (poster, regista, durata)
├── normalizer.py        # Normalizzazione titoli, fuzzy match, Levenshtein
├── browser.py           # CloakBrowser fallback (Chromium anti-fingerprint)
└── connectors/
    ├── base.py          # BaseConnector ABC
    ├── postmodernissimo.py
    ├── thespace.py
    └── uci.py
```

## Finestra temporale

Lo scraper raccoglie orari per **oggi + 7 giorni** (8 giorni totali, rolling). La data "oggi" è sempre calcolata nel fuso `Europe/Rome` — indipendente dalla TZ del server.

## Deploy su server Linux

```bash
# Setup automatico (installa systemd service + timer + logrotate)
./deploy/setup.sh

# Comandi utili post-deploy
sudo systemctl list-timers cineposto-scraper.timer    # prossima esecuzione
sudo systemctl status cineposto-scraper.service       # ultima run
sudo journalctl -u cineposto-scraper.service -f       # follow log
python3 -m scraper.main --once                        # run manuale (dev/troubleshoot)
```

### Logrotate (`deploy/cineposto-scraper-logrotate`)

La rotazione del log usa `copytruncate` invece di `create`: il file `scraper.log` viene copiato e poi troncato in-place senza essere rinominato. Questo evita che il processo Python (che ha aperto `scraper.log` con un file descriptor persistente) continui a scrivere su un inode orfano dopo la rotazione, senza richiedere reload del service.

Il path nel file logrotate (`/home/ubuntu/cineposto/scraper/scraper.log`) deve corrispondere a `SCRAPER_LOG` in `scraper/config.py` (`BASE_DIR / "scraper.log"`).

## Vincoli importanti

- **Nessuna fonte commerciale**: non usare TMDb, OMDb o altre API con restrizioni commerciali.
- **Nessun browser per UCI**: il sito è bloccato da Cloudflare, usare solo l'API Cloud Run.
- **Nessuna SPARQL complessa su Wikidata**: le query con `CONTAINS` causano timeout sistematici. Usare solo la Search API + fuzzy.
- **Non estrarre director/duration da UCI**: quei campi non esistono nell'API. Arrivano solo da Wikidata.

## Documentazione tecnica

| File | Contenuto |
|---|---|
| `../docs/scraper/architecture.md` | Architettura dettagliata, connettori, modello dati, flusso completo |
| `../docs/index.md` | Indice di tutta la documentazione del progetto |
