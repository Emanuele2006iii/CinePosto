# DOCS — Documentazione tecnica CinePosto Scraper

## Indice

1. [Architettura generale](#architettura-generale)
2. [Modulo config.py](#modulo-configpy)
3. [Modulo models.py](#modulo-modelspy)
4. [Connettori](#connettori)
   - [PostModernissimo](#postmodernissimo)
   - [The Space Cinema Corciano](#the-space-cinema-corciano)
   - [UCI Cinemas Perugia](#uci-cinemas-perugia)
5. [Helpers condivisi](#helpers-condivisi)
6. [Modulo normalizer.py](#modulo-normalizerpy)
7. [Modulo metadata.py — Wikidata enrichment](#modulo-metadatapy--wikidata-enrichment)
8. [Modulo delta.py — Merge e storico](#modulo-deltapy--merge-e-storico)
9. [Modulo errors.py](#modulo-errorspy)
10. [Modulo browser.py — CloakBrowser fallback](#modulo-browserpy--cloakbrowser-fallback)
11. [Modulo main.py — Orchestrazione](#modulo-mainpy--orchestrazione)
12. [Modello dati output](#modello-dati-output)
13. [Flusso completo di un run](#flusso-completo-di-un-run)
14. [Deploy e systemd](#deploy-e-systemd)

---

## Architettura generale

```
scraper/
├── main.py              # Entry point, orchestrazione sequenziale
├── config.py            # Costanti, URL, path, timezone
├── models.py            # Dataclass Film, Showing, CinemaError, ScrapeResult
├── delta.py             # Merge con run precedente, storico history
├── errors.py            # Scrittura errors.json accumulativo
├── metadata.py          # Enrichment Wikidata (poster, regista, durata)
├── normalizer.py        # Normalizzazione titoli, fuzzy match, Levenshtein
├── browser.py           # CloakBrowser singleton (Chromium anti-fingerprint)
└── connectors/
    ├── base.py          # BaseConnector ABC (scrape + fetch_film_detail)
    ├── postmodernissimo.py
    ├── thespace.py
    └── uci.py
```

**Pattern architetturale:** Strategy + ABC. Ogni cinema è un `BaseConnector` con metodo `scrape(today, dates) -> ScrapeResult`. L'orchestratore (`main.py`) chiama i connettori in sequenza, aggrega i risultati, deduplica, arricchisce con Wikidata e fonde con il run precedente.

**Flusso dati:**

```
Connettori (3x) → all_films: list[Film]
                ↓
         _deduplicate_films()    ← fuzzy match Levenshtein
                ↓
         enrich_film()           ← Wikidata per ogni film
                ↓
         merge_films()           ← delta con movies.json precedente
                ↓
         output_to_json()        → output/movies.json (scrittura atomica)
```

---

## Modulo config.py

Unica fonte di verità per costanti e path. Non contiene logica.

| Costante | Valore / Descrizione |
|---|---|
| `BASE_DIR` | Directory radice del progetto |
| `OUTPUT_DIR` | `output/` — file prodotti |
| `HISTORY_DIR` | `output/history/` — snapshot giornalieri |
| `CACHE_DIR` | `output/cache/` — cache per-cinema |
| `MOVIES_JSON` | `output/movies.json` |
| `ERRORS_JSON` | `output/errors.json` |
| `WIKIDATA_CACHE` | `.wikidata_cache.json` — cache persistente Wikidata |
| `FILMS_JSON` | `output/films.json` — tabella `films` DB-ready |
| `SHOWINGS_JSON` | `output/showings.json` — tabella `showings` DB-ready |
| `SCRAPER_TZ` | `ZoneInfo("Europe/Rome")` (override con `SCRAPER_TZ` env) |
| `DEFAULT_USER_AGENT` | UA browser-like condiviso tra connettori e healthcheck |
| `REQUEST_TIMEOUT` | 30s |
| `REQUEST_RETRY` | 3 tentativi |
| `RETRY_BACKOFF` | base 2 (esponenziale: 2s, 4s) |
| `SCHEDULE_INTERVAL_HOURS` | 24h |
| `REMOVAL_THRESHOLD_DAYS` | 7 giorni — soglia per marcare "rimosso" |
| `WIKIDATA_ENDPOINT` | `https://query.wikidata.org/sparql` |
| `WIKIDATA_TIMEOUT` | 15s |
| `CLOAKBROWSER_PAGE_TIMEOUT` | 30000ms |

**Funzioni helper:**
- `today_local() -> date` — data odierna nel fuso `Europe/Rome`
- `get_week_dates(ref_date?) -> list[str]` — 8 date ISO da oggi (oggi + 7)

Le directory `output/`, `output/history/`, `output/cache/` vengono create automaticamente all'import di `config.py`.

---

## Modulo models.py

Quattro dataclass che definiscono il modello dati interno.

### `Showing`

Una proiezione di un film in un cinema per una data specifica.

| Campo | Tipo | Descrizione |
|---|---|---|
| `cinema` | str | Nome del cinema |
| `cinema_slug` | str | Slug URL del cinema |
| `date` | str | Data ISO (`YYYY-MM-DD`) |
| `times` | list[str] | Orari (`HH:MM`) |
| `screen` | str\|None | Nome sala / formato (2D, 3D, IMAX…) |
| `source_url` | str\|None | URL pagina del film sul sito del cinema |
| `language` | str\|None | Lingua (ITA, OV…) |
| `session_attributes` | list[str] | Attributi aggiuntivi (e.g. "Dolby Atmos") |

### `Film`

Rappresentazione interna di un film durante il run.

| Campo | Tipo | Descrizione |
|---|---|---|
| `title` | str | Titolo originale (con HTML unescaped) |
| `title_normalized` | str | Titolo normalizzato (lowercase, senza suffissi) |
| `present_in` | list[Showing] | Tutte le proiezioni raccolte |
| `poster` | str\|None | URL poster finale (dopo enrichment) |
| `description` | str\|None | Trama |
| `genres` | list[str] | Generi |
| `status` | str | `"in_programmazione"` o `"rimosso"` |
| `history` | list[dict] | Log eventi: `{"date": "YYYY-MM-DD", "action": "added\|updated\|removed"}` |
| `source_poster` | str\|None | Poster dal sito del cinema (fallback se Wikidata non trova niente) |
| `duration` | str\|None | Durata (`"N min"`) |
| `director` | str\|None | Regista |

### `CinemaError`

Errore accumulato durante un run.

```python
@dataclass
class CinemaError:
    cinema: str
    timestamp: str   # ISO datetime
    exception: str   # nome della classe eccezione
    phase: str       # "scrape", "parse_...", "scrape_fallback"
    url: str | None
    detail: str | None
```

Nota: `to_dict()` non emette un campo `"date"` — solo `"timestamp"`.

### `ScrapeResult`

Contenitore restituito da ogni `connector.scrape()`.

```python
@dataclass
class ScrapeResult:
    films: list[Film]
    errors: list[CinemaError]
```

### Funzioni di serializzazione

- `film_to_dict(film) -> dict` — serializza un Film per l'output JSON:
  - chiama `_consolidate_showings()` per raggruppare Showing con stessa (cinema, date, language, screen)
  - chiama `normalize_duration()` sulla durata
  - chiama `html.unescape()` su titolo e descrizione
  - chiama `_clean_poster()` per estrarre l'URL reale dai proxy Next.js `/_next/image?url=...`
- `output_to_json(films, errors, city) -> dict` — produce la struttura finale di `movies.json`
- `films_to_json(films) -> dict` — produce `films.json` DB-ready (tabella `films`): id=title_normalized, campi anagrafici, first_seen/last_seen estratti da history
- `showings_to_json(films, date_from, date_to) -> dict` — produce `showings.json` DB-ready (tabella `showings`): film_id FK, cinema_slug FK, date, times JSON array
- `cinemas_to_json(locations) -> dict` — produce `cinemas.json` DB-ready (tabella `cinemas`): slug PK, nome, lat, lon, indirizzo, website

---

## Connettori

Tutti estendono `BaseConnector` (ABC in `connectors/base.py`) che impone:
```python
@property def cinema_name(self) -> str
@property def cinema_slug(self) -> str
def scrape(self, today: str, dates: list[str] | None = None) -> ScrapeResult
def fetch_film_detail(self, film_url: str) -> Optional[dict]
```

### PostModernissimo

**File:** `connectors/postmodernissimo.py`  
**Accesso:** HTML statico + parser RSC (Next.js 13+)  
**Anti-bot:** nessuno

PostModernissimo usa Next.js 13 con React Server Components. Il payload dati è embedded nella pagina HTML come sequenza di chunk:

```html
<script>self.__next_f.push([1,"...payload JSON escaped..."])</script>
```

**Flusso di scraping:**

1. `GET /` — scarica la homepage
2. `_parse_rsc_payload(html)` — estrae il chunk più grande dal pattern `self.__next_f.push([1,"..."])` e lo unescapa (solo `\"` e `\\`)
3. Regex `{"id":N,"title":"...","slug":"...","permalink":"..."}` trova tutti i film nel payload
4. Per ogni film: `_extract_shows(text, pos)` cerca il blocco `"shows":[...]` entro 5000 caratteri dall'inizio del film; `_extract_details(text, pos)` cerca `"details":{...}` entro 3000 caratteri
5. `_is_event_stub(movie)` filtra eventi non-film (parole chiave: "ospiti", "rassegna", "concerto", ecc.)
6. Filtra gli show per `target_date_ints` e `opzioni != "noprog"`
7. `_parse_film_cards(soup)` — parser HTML parallelo per poster (da `<img>` nei `<li class="movie-item">`)
8. `_reconcile_with_detail(film)` — per ogni film, fa GET sulla pagina di dettaglio e confronta gli show; se diversi, sostituisce (vince il dettaglio come fonte canonica)
9. Fallback: se RSC restituisce 0 film, usa `_fallback_from_html()` con le card HTML (senza orari)

**Formato date nel payload:** `YYYYMMDD` (intero, non ISO). Conversione: `f"{d[:4]}-{d[4:6]}-{d[6:8]}"`.

**Parsing dettaglio:** `fetch_film_detail(url)` cerca `<meta name="description">` o primo `<p>` in `article, .film-content, .description`.

**Finestre di ricerca hardcoded** (nota: possono causare dati incompleti su payload molto grandi):
- `details`: +3000 caratteri dalla posizione del film
- `shows index`: +5000 caratteri
- `shows array`: +20000 caratteri dall'inizio dell'array

### The Space Cinema Corciano

**File:** `connectors/thespace.py`  
**Accesso:** API REST proprietaria con OAuth2 `client_credentials`  
**Fallback:** CloakBrowser se API inaccessibile

**Autenticazione:** POST `{API_BASE}/auth/token` con body `{}` (JSON vuoto). Il token non è presente nella risposta — la sessione `requests.Session` mantiene i cookie impostati dal server. Non c'è un campo `access_token` da estrarre.

**URL API:**
- Films: `{API_BASE}/showings/cinemas/1027/films?showingDate={date}&includesSession=true&includeSessionAttributes=true`
- Auth: `{API_BASE}/auth/token`

**Struttura risposta:** `data["result"]` o `data["films"]` → lista film. Per ogni film:
- `filmTitle` o `title` → titolo
- `posterImageSrc` o `panelImageUrl` → poster
- `synopsisShort` o `synopsis` → descrizione
- `runningTime` → durata (minuti, intero)
- `genres` → lista stringa o lista dict con `"name"`
- `director` → regista (stringa diretta)
- `showingGroups` → lista di oggetti con `"date"` (ISO/Z), `"sessions"` con `"startTime"` (ISO/Z), `"screenName"`, `"attributes"` (lista con `"attributeType": "Language"`)

**Parsing date:** le date arrivano in formato ISO con timezone Z; vengono convertite con `dt.fromisoformat(str(d).replace("Z", "+00:00"))`.

**Fallback browser:** `_scrape_via_browser(today)` usa CloakBrowser per aprire `{BASE_URL}/cinema/corciano/al-cinema` e parsare le card HTML con selettori generici. Recupera solo titolo, poster e orari (senza dettagli).

**`fetch_film_detail`:** GET sulla pagina HTML del film, cerca `[data-test*='synopsis'], .synopsis, .film-description`. Se fallisce → CloakBrowser.

### UCI Cinemas Perugia

**File:** `connectors/uci.py`  
**Accesso:** API Cloud Run non documentata  
**Motivo:** il sito `ucicinemas.it` è protetto da Cloudflare WAF; il backend Cloud Run non lo è

**URL API:**
```
https://myuci---uci-backend-production-nfluwp7wga-oc.a.run.app/api/theatres/uci-cinemas-perugia/programming/{date}
```

**Struttura risposta:** `data["data"]` → lista film. Per ogni film:
- `title` → titolo
- `slug` → usato per costruire `detail_url`
- `poster` o `top_image` → poster (verificato che inizi con `http`)
- `genres` → lista dict con `"name"` o lista stringa
- `description` → HTML grezzo (pulito con `_strip_html`)
- `not_today: true` → film nel programma ma non oggi → skip
- `screens` → struttura annidata: `[{formato: [{language, screen, performances: [{day, actual_start_at}]}]}]`

**Campi NON presenti nell'API UCI:** `director`, `duration`. Arrivano solo da Wikidata (se trovati).

**`fetch_film_detail`:** attualmente stub — restituisce `{}`. Non usato dall'orchestratore.

---

## Helpers condivisi

Per evitare duplicazione tra i 3 connettori, alcuni helper sono centralizzati:

### `DEFAULT_USER_AGENT` (in `config.py`)

Stringa User-Agent browser-like usata da:
- `PostModernissimoConnector` (header `requests.Session`)
- `TheSpaceConnector` (sia API che fallback CloakBrowser)
- `UCIConnector` (chiamate all'API Cloud Run)
- `healthcheck.py` (ping endpoint)

Centralizzare l'UA in un'unica costante semplifica l'aggiornamento (e.g. quando un sito inizia a bloccare versioni Chrome vecchie) e garantisce coerenza tra connettori e healthcheck.

### `make_error(cinema, exc, phase, url=None, detail=None) -> CinemaError` (in `errors.py`)

Factory che costruisce un `CinemaError` riempiendo automaticamente `timestamp` (ISO now nel fuso `SCRAPER_TZ`) ed `exception` (nome della classe dell'eccezione).

```python
# Prima (duplicato in 3 connettori):
errors.append(CinemaError(
    cinema=self.cinema_name,
    timestamp=datetime.now(SCRAPER_TZ).isoformat(),
    exception=type(exc).__name__,
    phase="scrape",
    url=url,
    detail=str(exc),
))

# Dopo:
errors.append(make_error(self.cinema_name, exc, "scrape", url=url, detail=str(exc)))
```

Tutti e 3 i connettori (`postmodernissimo.py`, `thespace.py`, `uci.py`) usano `make_error`.

### `normalize_genres(raw) -> list[str]` (in `normalizer.py`)

Normalizza il campo `genres` proveniente dalle API in `list[str]`. Le API restituiscono formati eterogenei:

| Input | Output |
|---|---|
| `None` | `[]` |
| `"Drama"` | `["Drama"]` |
| `["Drama", "Thriller"]` | `["Drama", "Thriller"]` |
| `[{"name": "Drama"}, {"name": "Thriller"}]` | `["Drama", "Thriller"]` |
| `[{"name": ""}, "  Drama  "]` | `["Drama"]` (skip vuoti, strip whitespace) |

Usato da `TheSpaceConnector` (API restituisce talvolta lista stringhe, talvolta lista dict) e `UCIConnector` (lista dict con chiave `"name"`).

---

## Modulo normalizer.py

### `normalize_title(title: str) -> str`

Pipeline di normalizzazione applicata ai titoli per il confronto cross-cinema:

1. Strip spazi
2. Conversione smart quotes (`'`, `'`, `"`, `"`, `–`, `—`) in equivalenti ASCII
3. Rimozione suffissi tecnici (fino a 3 volte): `3D`, `IMAX`, `HFR`, `4DX`, `ScreenX`, `Dolby Atmos`, `OV`, `VOST`, `Sub ITA`, `F&S`, ecc.
4. Rimozione suffissi riedizione: `4K (RIED. 2024) C.A.`
5. Rimozione anno: `(2023)`, `[2023]`
6. Rimozione `C.A.` finale
7. Rimozione parola `AND`
8. Rimozione prefissi franchise: `STAR WARS:`, `MARVEL'S`, `DC`, `PIXAR`, `Disney`, `THE`, `IL`, `LA`
9. Collasso spazi multipli
10. Strip di punteggiatura finale
11. Rimozione cifre finali (se non seguite da `)`, `]`, `}`)

> Nota: `_ROMAN_NUM_SUFFIX` è compilato ma **non applicato** — bug noto, da implementare.

### `title_key(title: str) -> str`

`normalize_title` → lowercase → rimozione non-alfanumerici → rimozione spazi. Usato come chiave di lookup nei dict.

### `fuzzy_match(a: str, b: str) -> bool`

1. Se `title_key(a) == title_key(b)` → True
2. Se uno è sottostringa dell'altro → True
3. Se distanza di Levenshtein ≤ max(2, len(ka)//4) → True

### `normalize_duration(duration: str | None) -> str | None`

Normalizza qualsiasi formato di durata a `"N min"`:
- `HH:MM` o `HH:MM:SS` → conversione in minuti
- `Nh Mm` → N*60+M
- Fallback: primo numero trovato nella stringa

---

## Modulo metadata.py — Wikidata enrichment

**Scopo:** arricchire ogni `Film` con poster, descrizione, regista, durata, titolo originale, **anno di pubblicazione, wikidata_id** se non già presenti dal connettore.

### Strategia

1. Controlla se tutti i campi sono già presenti — in tal caso, skip
2. Cerca nel cache in-memory (`_cache: dict[str, dict]`) con chiave `normalize_title(title).lower()`
3. Se non in cache, chiama `_search_fuzzy(title)` → API `wbsearchentities` di Wikidata
4. Per ogni risultato, controlla se la descrizione contiene "film" o "movie"
5. Se trovato, chiama `_fetch_entity_details(entity_id)` → `EntityData/{id}.json`
6. **Estrae dalla entity Wikidata**:
   - `P18` (immagine) → `poster` (URL Commons)
   - `P57` (regista) → `director` (con secondo lookup per risolvere il nome)
   - `P2047` (durata) → `duration` ("109 min")
   - `P577` (data pubblicazione) → `year` (int, primi 4 char del `time` field)
   - `entity_id` stesso → `wikidata_id` (es. `"Q97154362"`)
   - `labels.it` / `labels.en` → `title`, `original_title`
   - `descriptions.it` / `descriptions.en` → `description`
7. Salva in cache e su disco (`.wikidata_cache.json`)

### Meccanismi di protezione

| Meccanismo | Valore | Descrizione |
|---|---|---|
| Rate limit interval | 5s | Pausa minima tra query SPARQL |
| Circuit breaker | 3 fallimenti consecutivi | Sospende tutte le query fino al run successivo |
| Rate limit 429 | Header `Retry-After` | Backoff adattivo |
| Pausa post-ricerca | 2s | Sleep dopo ogni ricerca con successo |

**Nota:** il campo `"genres"` non viene mai popolato da Wikidata — `_fetch_entity_details` non estrae questo dato. Wikidata arricchisce: poster, descrizione, regista, durata, titolo originale, anno, wikidata_id.

**Copertura effettiva** (misurata al 02/07 su 19 film del dataset attuale):
- `poster`, `description`: 100%
- `director`: 95%
- `runtime_minutes` (dopo parsing "X min"): 74%
- `genres`: 69% (viene dai connettori, non da Wikidata)
- **`year`, `wikidata_id`**: **37%** — molti film di nicchia (uscite piccole, sale d'essai) non sono su Wikidata → limite della fonte, non fixabile senza altra API.

**Nota:** la risoluzione del regista (P57) esegue un secondo `_fetch_entity_details(director_id)` che bypassa il rate limiter di `_sparql_query` (usa direttamente `requests.get`). Questo è accettabile dato che l'endpoint `/wiki/Special:EntityData/` è distinto da SPARQL.

### Cache negativa (mancante)

Se un titolo non viene trovato su Wikidata, la ricerca viene ripetuta ad ogni run. Con ~20 film per run, questo genera ~20 richieste HTTP inutili + 20 sleep da 1-2 secondi = 20-40 secondi sprecati per run. Bug noto: manca cache negativa.

---

## Modulo delta.py — Merge e storico

### `merge_films(new_films, previous_data, today) -> list[Film]`

Fonde i risultati del run corrente con quelli del run precedente per mantenere la continuità dello storico.

**Logica per film presenti nel run corrente:**
- Se già presente nel precedente (`title_key` match): preserva `history`, aggiunge `"updated"` se gli orari sono cambiati
- Se nuovo: inizializza `history` con `{"date": today, "action": "added"}`
- Preserva poster e description dal precedente se mancanti nel nuovo

**Logica per film assenti dal run corrente (erano nel precedente):**
- Se già marcato `"rimosso"` e sono passati >14 giorni dall'ultima rimozione: **purge** (eliminato permanentemente)
- Se già marcato `"rimosso"`: mantenuto nello stato rimosso
- Se era `"in_programmazione"` e l'ultimo orario è >7 giorni fa: marcato `"rimosso"` con evento in history
- Se era `"in_programmazione"` e l'ultimo orario è ≤7 giorni fa: stato limbo — `present_in=[]`, aggiunge `"removed"` in history se non già presente

**Filtro finale:**
```python
return [f for f in merged if f.status != "rimosso" and any(s.times for s in f.present_in)]
```
I film con `status="rimosso"` e i film con `present_in=[]` (grace period) vengono esclusi dall'output. Il contatore `removed` viene loggato prima del filtro per visibilità.

### `_showings_changed(old, new) -> bool`

Confronta due liste di showing tramite chiavi ordinate `cinema_slug:date:HH:MM,HH:MM,...`. Restituisce `True` se la firma è diversa.

### `save_snapshot(today)` / `load_previous_movies()`

- `save_snapshot`: copia `movies.json` in `output/history/movies_{today}.json` dopo ogni run
- `load_previous_movies`: carica `movies.json` esistente e restituisce `data["films"]`

---

## Modulo errors.py

Gestisce il file `output/errors.json` in modo accumulativo.

**Struttura `errors.json`:**
```json
{
  "errors": [
    {"cinema": "...", "timestamp": "...", "exception": "...", "phase": "...", "url": null, "detail": "..."}
  ],
  "last_error_date": "YYYY-MM-DD",
  "last_error_timestamp": "...",
  "last_clean_date": "YYYY-MM-DD"
}
```

**Comportamento:**
- Se ci sono errori: aggiunge al file esistente, rimuovendo prima gli errori già presenti per `today` (pulizia idempotente)
- Se non ci sono errori: rimuove gli errori di `today` e scrive `last_clean_date`

**Nota:** la pulizia usa `e.get("timestamp", "").startswith(today)` come condizione efficace; `e.get("date") == today` è redundante perché `to_dict()` non emette mai un campo `"date"`.

---

## Modulo browser.py — CloakBrowser fallback

**Scopo:** fornire un browser Chromium con anti-fingerprint per aggirare le protezioni dei siti web quando le API REST non sono disponibili.

**Pattern singleton:** `_browser_instance` globale — il browser viene lanciato una volta e riutilizzato per tutta la durata del run.

**Interfaccia pubblica:**
- `get_browser()` — restituisce il browser esistente o ne lancia uno nuovo
- `new_page(browser?)` — crea una nuova pagina con timeout configurato
- `close_browser()` — chiude il browser al termine del run
- `fetch_page_html(url, wait_for?, timeout?) -> str` — naviga all'URL, aspetta il selettore CSS, restituisce l'HTML della pagina

**Health check problematico:** `get_browser()` verifica se il browser è ancora vivo chiamando `_browser_instance.new_page()`. Questa pagina non viene mai chiusa — resource leak su ogni chiamata a `get_browser()` quando il browser è già aperto.

**Configurazione:**
- `CLOAKBROWSER_HEADLESS`: env var (default `true`)
- `CLOAKBROWSER_FINGERPRINT_SEED`: env var (default `42069`)
- `CLOAKBROWSER_PAGE_TIMEOUT`: 30000ms (hardcoded in config.py)

---

## Modulo main.py — Orchestrazione

### `run_scraper()`

Flusso principale:

1. Calcola `today` e `week_dates`
2. Chiama `connector.scrape(today, week_dates)` per i 3 connettori in sequenza
3. Per connettori falliti: attende `SCRAPER_RETRY_DELAY` secondi (default 300s) e riprova una volta
4. Per connettori falliti al retry: carica cache dal file `output/cache/{slug}.json` come fallback
5. `_deduplicate_films(all_films)` — fuzzy match cross-cinema, merge `present_in`
6. `enrich_film(film)` per ogni film — Wikidata (con try/except per continuare in caso di errore)
7. `merge_films(all_films, previous_data, today)` — delta con run precedente
8. Scrittura atomica (4 file):
   - `movies.json` — stato interno completo con `history[]` e `present_in[]`
   - `films.json` — tabella `films` DB-ready (solo film `in_programmazione`)
   - `showings.json` — tabella `showings` DB-ready
   - `cinemas.json` — tabella `cinemas` DB-ready
9. `save_snapshot(today)` — snapshot giornaliero
10. `write_errors(all_errors, today)` — aggiorna errors.json
11. `close_browser()` — cleanup CloakBrowser

### `_deduplicate_films(films) -> list[Film]`

Raggruppa film con lo stesso titolo (fuzzy match) provenienti da cinema diversi. Merge di `present_in`, poster, description, genres, director, duration (prende il primo non-None).

### Cache per-cinema

- **Salvataggio:** dopo ogni scrape riuscito → `output/cache/{slug}.json`
- **Caricamento:** solo come fallback quando il connettore fallisce entrambi i tentativi
- I dati in cache possono essere del giorno precedente — gli orari potrebbero non corrispondere alla data corrente

---

## Modello dati output

La pipeline produce 4 file in `output/`. I 3 DB-ready mappano 1:1 alle tabelle del backend.

### `output/movies.json` — stato interno

```json
{
  "generated_at": "2026-06-24T10:00:00.000000",
  "city": "Perugia",
  "films": [
    {
      "title": "Nome Film",
      "title_normalized": "nome film",
      "poster": "https://...",
      "description": "Trama",
      "genres": ["Drama"],
      "status": "in_programmazione",
      "director": "Nome Regista",
      "duration": "120 min",
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

Usato come stato tra un run e il successivo (delta). Non destinato al backend.

### `output/films.json` — tabella `films` DB-ready

```json
{
  "generated_at": "...",
  "films": [
    {
      "id": "nome-film",
      "title": "Nome Film",
      "title_normalized": "nome film",
      "original_title": "Original Title",
      "poster": "https://...",
      "description": "Trama",
      "genres": ["Drama"],
      "director": "Nome Regista",
      "duration": "120 min",
      "status": "in_programmazione",
      "first_seen": "2026-06-20",
      "last_seen": "2026-06-24"
    }
  ]
}
```

Solo film con `status="in_programmazione"`. `first_seen`/`last_seen` estratti da `history[]`.

### `output/showings.json` — tabella `showings` DB-ready

```json
{
  "generated_at": "...",
  "date_from": "2026-06-24",
  "date_to": "2026-07-01",
  "showings": [
    {
      "film_id": "nome-film",
      "cinema_slug": "uci-perugia",
      "date": "2026-06-24",
      "times": ["18:00", "20:30"],
      "screen": "2D",
      "language": "ITA"
    }
  ]
}
```

Una riga per combinazione (film, cinema, data). `film_id` FK→`films.id`, `cinema_slug` FK→`cinemas.slug`.

### `output/cinemas.json` — tabella `cinemas` DB-ready

```json
{
  "generated_at": "...",
  "cinemas": [
    {
      "slug": "uci-perugia",
      "name": "UCI Cinemas Perugia",
      "address": "Via Corcianese 200, 06073 Corciano PG",
      "city": "Corciano",
      "region": "Umbria",
      "lat": 43.0745,
      "lon": 12.2891,
      "website": "https://ucicinemas.it"
    }
  ]
}
```

**Campi nullable:** `poster`, `description`, `director`, `duration`, `genres` (può essere `null`), `screen`, `language`, `source_url`, `session_attributes`.

**Campi assenti:**
- `rating` — **decisione consapevole**: TMDb vieta l'uso commerciale senza licenza; OMDb vieta anch'esso l'uso commerciale; Wikidata non ha copertura affidabile per i film recenti. Campo scartato definitivamente.
- `price` — **decisione consapevole**: scartato. PostMod ha prezzo fisso ma The Space e UCI richiederebbero scraping aggiuntivo fragile.
- `original_title` — **implementato via Wikidata** (label EN quando differisce dal label IT). Null se Wikidata non ha il film.
- `language` su PostModernissimo showings — **non disponibile**: il payload RSC non espone la lingua per spettacolo. Limitazione del sito, non aggirabile senza scraping ulteriore.

**Fonte dei campi per cinema:**

| Campo | PostModernissimo | The Space | UCI |
|---|---|---|---|
| title | RSC payload | API `filmTitle` | API `title` |
| poster | HTML cards + RSC details | API `posterImageSrc` | API `poster` / `top_image` |
| description | `fetch_film_detail` | API `synopsisShort` | API `description` (HTML) |
| genres | RSC `details.genere` | API `genres` | API `genres` |
| director | RSC `details.regia` | API `director` | — (solo Wikidata) |
| duration | RSC `details.durata` | API `runningTime` | — (solo Wikidata) |
| language | — | API `attributes[Language]` | API `language.name` |
| screen | — | API `screenName` | API `screens` (formato chiave) |

---

## Flusso completo di un run

```
main.run_scraper()
│
├── PostModernissimoConnector.scrape(today, week_dates)
│   ├── GET postmodernissimo.com                    [_retry_get]
│   ├── _parse_rsc_payload(html)                   [regex + JSON.parse]
│   ├── _parse_film_cards(soup)                    [BeautifulSoup]
│   └── per ogni film: _reconcile_with_detail()    [GET pagina dettaglio]
│
├── TheSpaceConnector.scrape(today, week_dates)
│   ├── POST auth/token                            [OAuth2 no-token]
│   ├── per ogni data: GET films?showingDate=...   [_retry_request]
│   └── [se API fallisce] CloakBrowser fallback
│
├── UCIConnector.scrape(today, week_dates)
│   └── per ogni data: GET Cloud Run API           [_retry_request]
│
├── [retry dopo 300s per connettori falliti]
│
├── _deduplicate_films(all_films)                  [fuzzy match]
│
├── per ogni film: enrich_film(film)               [Wikidata API]
│   ├── _search_wikidata(title)                    [cache → wbsearchentities]
│   └── _fetch_entity_details(entity_id)           [EntityData JSON]
│
├── merge_films(all_films, previous_data, today)   [delta]
│
├── scrittura atomica → output/movies.json         [stato interno + history]
├── scrittura atomica → output/films.json          [tabella films DB-ready]
├── scrittura atomica → output/showings.json       [tabella showings DB-ready]
└── scrittura atomica → output/cinemas.json        [tabella cinemas DB-ready]
```

---

## Deploy e systemd

Il deploy è gestito da `deploy/setup.sh` che installa:
- Un **systemd timer** (`cineposto-scraper.timer`) con trigger giornaliero alle 03:00 + `Persistent=true` + `RandomizedDelaySec=10min`
- Un **systemd service** (`cineposto-scraper.service`, `Type=oneshot`) che lancia `python -m scraper.main --once`
- Un **logrotate** per `scraper.log` (config in `deploy/cineposto-scraper-logrotate`)

> Scelta architetturale (decisione L3): timer esterno + `--once` invece di `--schedule` interno con APScheduler.
> Vantaggi: ogni run è un processo isolato (no memory leak nel daemon), `systemctl status` mostra l'ultima esecuzione, log distinti per run, restart granulare con `Restart=on-failure` su una singola esecuzione invece che sull'intero scheduler.

### ⚠️ Miglioramento noto: reimport non automatizzato

Oggi `cineposto-scraper.service` lancia solo `python -m scraper.main --once` — non chiama `POST /admin/reimport` sul backend dopo la run. Risultato: alle 3:00 lo scraper aggiorna i JSON, ma il **database resta quello vecchio finché qualcuno non chiama manualmente l'endpoint admin** (oggi va bene per le demo, non per un servizio che deve aggiornarsi da solo ogni notte).

**Fix proposto**: aggiungere uno step (o una seconda unit systemd, `Type=oneshot`, `After=cineposto-scraper.service`) che, solo se lo scraper è terminato con successo, chiama:
```bash
curl -X POST http://localhost:8000/admin/reimport -H "X-Admin-Token: $ADMIN_TOKEN"
```
Non è un redesign, è un passo in più nella catena esistente.

### Logrotate: `copytruncate` vs `create`

La config di logrotate usa `copytruncate` (e NON `create`):

```text
/home/ubuntu/cineposto/scraper/scraper.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

**Perché `copytruncate`:** il processo Python apre `scraper.log` una volta (all'avvio del service) e mantiene il file descriptor aperto per tutta la durata del run / dello scheduler. Con `create` (default) logrotate rinominerebbe il file e ne creerebbe uno nuovo — ma il processo continuerebbe a scrivere sull'inode orfano del file rinominato, che viene poi compresso e perso. `copytruncate` invece copia il contenuto in `scraper.log.1` e poi tronca il file originale in-place (stesso inode): il processo Python continua a scrivere sul file giusto senza bisogno di reload del service.

Il path nel file di config deve corrispondere a `SCRAPER_LOG` in `scraper/config.py` (`BASE_DIR / "scraper.log"`).

**Comandi utili:**

```bash
sudo systemctl list-timers cineposto-scraper.timer            # prossima esecuzione
sudo systemctl status cineposto-scraper.service               # ultima run
sudo systemctl start cineposto-scraper.service                # forza run subito (one-shot)
sudo journalctl -u cineposto-scraper.service -f --since "1 hour ago"
python3 -m scraper.main --once     # run manuale immediato (no systemd)
python3 -m ruff check scraper/ tests/ && python3 -m pytest tests/ -q   # lint + test
```

**Variabili d'ambiente:**

| Variabile | Default | Descrizione |
|---|---|---|
| `SCRAPER_TZ` | `Europe/Rome` | Fuso orario per calcolo "oggi" |
| `SCRAPER_LOG_LEVEL` | `INFO` | Livello di log (`DEBUG`, `INFO`, `WARNING`) |
| `CLOAKBROWSER_HEADLESS` | `true` | Headless o meno per CloakBrowser |
| `CLOAKBROWSER_FINGERPRINT_SEED` | `42069` | Seed per fingerprint anti-detection |
