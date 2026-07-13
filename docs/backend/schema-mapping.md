# Schema mapping — JSON scraper → DB backend

> **Riferimento autorevole** per lo script di seed e per qualsiasi futura modifica al mapping.
> Aggiornato: 2026-06-30. Allineato alle decisioni L1-L5 e D1-D5 (tabella in [`panoramica.md`](../panoramica.md) §6).

---

## Premessa

Schema completamente in **inglese** (decisione L1+L2): tabelle DB e chiavi JSON usano gli stessi nomi. Niente traduzione runtime.

| Lato | Lingua | Esempio |
|------|--------|---------|
| Scraper JSON output | inglese | `films`, `showings`, `cinemas`, `title`, `year` |
| Backend DB / ORM | inglese | `films` (tabella), `Showing` (classe), `title`, `year` |
| Commenti nel codice | italiano | `# Lookup titolo→id intera per il seed` |

---

## 1. `cinemas.json` → tabella `cinemas`

**File**: `scraper/output/cinemas.json`
**Struttura JSON**:

```json
{
  "generated_at": "2026-06-25T12:56:35.086878+02:00",
  "cinemas": [
    {
      "slug": "postmodernissimo",
      "name": "PostModernissimo",
      "address": "Via del Milite Ignoto 1, 06121 Perugia PG",
      "city": "Perugia",
      "region": "Umbria",
      "lat": 43.1107,
      "lon": 12.3882,
      "website": "https://www.postmodernissimo.com"
    },
    ...
  ]
}
```

**Mapping** (1:1, nessuna traduzione):

| JSON | DB column | Note |
|------|-----------|------|
| `slug` | `slug` (PK) | Chiave primaria |
| `name` | `name` | |
| `address` | `address` | |
| `city` | `city` | |
| `region` | `region` | default `"Umbria"` se mancante |
| `lat` | `lat` | float |
| `lon` | `lon` | float |
| `website` | `website` | nullable |
| — | `phone` | non presente nel JSON; sempre null al seed |

**Strategia seed**: per ogni record nel JSON → `cinema_repo.upsert(data)` (SELECT by slug, UPDATE o INSERT).

---

## 2. `films.json` → tabella `films`

**File**: `scraper/output/films.json`
**Struttura JSON**:

```json
{
  "generated_at": "2026-06-25T12:56:35.080884+02:00",
  "films": [
    {
      "id": "Ricchi…da morire - Delitti in famiglia",
      "title": "Ricchi…da morire – Delitti in famiglia",
      "title_normalized": "Ricchi…da morire - Delitti in famiglia",
      "original_title": null,
      "poster": "https://...",
      "description": "Trama...",
      "year": 2026,
      "duration": "95 min",
      "genres": ["Commedia"],
      "director": "Nome Regista",
      "wikidata_id": "Q123456"
    },
    ...
  ]
}
```

**Mapping**:

| JSON | DB column | Note |
|------|-----------|------|
| `"id"` (stringa) | ❌ NON usato come PK | Serve solo come **chiave di join** con `showings.json` |
| `title` | `title` | |
| `title_normalized` | `title_normalized` | ⚠️ **rinormalizzare nel backend** — la normalizzazione dello scraper può differire (em-dash). Meglio NON fidarsi del campo del JSON e ricalcolare via `normalize_title()`. |
| `original_title` | `original_title` | nullable |
| `year` | `year` | int, nullable. ⚠️ In SQL `NULL ≠ NULL`: con `year` NULL la `UNIQUE(title_normalized, year)` **non blocca duplicati a livello DB** — la dedup è garantita dal lookup applicativo in `get_by_natural_key` (che usa `IS NULL`). Limite noto e accettato per l'MVP. |
| `duration` (stringa "X min") | `runtime_minutes` | parsing: estrai int da `"95 min"` → `95` |
| `genres` (array) | `genres` (string CSV) | `",".join(genres)` |
| `director` | `director` | nullable |
| `poster` | `poster_url` | |
| `description` | `synopsis` | |
| `wikidata_id` | `wikidata_id` | UNIQUE, nullable |
| — | `id` (DB) | PK autoincrement, generato dal DB |
| — | `created_at` | default `now()` |

**Strategia seed**:

```pseudo
per ogni record film nel JSON:
    title_norm = normalize_title(record["title"])      # NON usare title_normalized del JSON
    year = record.get("year")
    runtime = parse_minutes(record.get("duration"))    # "95 min" → 95
    record_norm = {
        "title": record["title"],
        "title_normalized": title_norm,
        "year": year,
        "runtime_minutes": runtime,
        "genres": ",".join(record.get("genres") or []),
        "director": record.get("director"),
        "poster_url": record.get("poster"),
        "synopsis": record.get("description"),
        "original_title": record.get("original_title"),
        "wikidata_id": record.get("wikidata_id"),
    }

    film = film_repo.upsert_from_scraper(db, record_norm)
        # internamente:
        #   exist = SELECT by (title_normalized, year)
        #   if exist: UPDATE solo campi non-null in record
        #   else: INSERT
        #   return film  (con id intera popolata)

    # COSTRUISCI lookup per il prossimo step:
    title_to_id[record["id"]] = film.id    # mappa "titolo stringa JSON" → id intera DB
```

⚠️ **Punto critico**: la chiave del dict `title_to_id` è la stringa **originale** del JSON (campo `"id"` non normalizzato), perché è esattamente quella che ritroverò come `film_id` dentro `showings.json`. NON normalizzare la chiave del lookup.

---

## 3. `showings.json` → tabella `showings`

**File**: `scraper/output/showings.json`
**Struttura JSON**:

```json
{
  "generated_at": "2026-06-25T12:56:35...",
  "date_from": "2026-06-25",
  "date_to": "2026-07-02",
  "showings": [
    {
      "film_id": "Ricchi…da morire - Delitti in famiglia",
      "cinema_slug": "postmodernissimo",
      "date": "2026-06-25",
      "times": ["18:30"],
      "source_url": "https://www.postmodernissimo.com/films/ricchi-..."
    },
    ...
  ]
}
```

**Mapping**:

| JSON | DB column | Note |
|------|-----------|------|
| `film_id` (string title) | `film_id` (int) | **lookup obbligatorio**: `title_to_id[record["film_id"]]` (vedi §2). Se non trovato → log + skip record. |
| `cinema_slug` | `cinema_slug` (string FK) | 1:1, identico |
| `date` (ISO string) | `date` (date) | `date.fromisoformat(...)` |
| `times` (array di "HH:MM") | `times` (string JSON) | `json.dumps(times, separators=(",",":"))` |
| `source_url` | `buy_url` | |
| — | `language`, `screen` | non presenti nel JSON; null al seed |
| — | `scraped_at` | default `now()` |

**Strategia seed**:

```pseudo
per ogni record showing nel JSON:
    film_db_id = title_to_id.get(record["film_id"])
    if film_db_id is None:
        log.warning(f"Film '{record['film_id']}' non trovato nel lookup, skip")
        continue

    payload = {
        "film_id":     film_db_id,
        "cinema_slug": record["cinema_slug"],
        "date":        date.fromisoformat(record["date"]),
        "times":       json.dumps(record["times"]),
        "buy_url":     record.get("source_url"),
    }
    showing_repo.upsert(db, payload)
        # SELECT by (film_id, cinema_slug, date) → UPDATE times/buy_url, oppure INSERT
```

---

## 4. Ordine d'esecuzione del seed

L'ordine è vincolato dalle FK. **Sempre questo ordine**:

```
1. cinemas.json   →  upsert in `cinemas`          (PK slug)
2. films.json     →  upsert in `films`,
                     COSTRUISCI title_to_id        (lookup string → int)
3. showings.json  →  upsert in `showings`,
                     USA title_to_id per film_id intero
4. cleanup       →  showings con date < oggi (opzionale, configurabile)
```

---

## 5. Cosa fare se i JSON sono incompleti o malformati

| Scenario | Comportamento |
|----------|---------------|
| File JSON mancante | abort: errore esplicito, exit code != 0 |
| Cinema con slug duplicato dentro lo stesso JSON | log warning, ultima vince |
| Film senza `title` o senza `id` | skip record + log error |
| Showing con `film_id` che non matcha `title_to_id` | skip record + log warning (può capitare se films.json e showings.json sono incoerenti) |
| Showing con `cinema_slug` non in tabella `cinemas` | skip record + log error (segnala disallineamento) |

---

## 6. Esempi pratici (un giro completo)

**Input scraper**:

```json
// films.json
{ "films": [
  { "id": "Dune Parte 2", "title": "Dune — Parte 2", "year": 2024,
    "wikidata_id": "Q97154362", "director": "Denis Villeneuve", "duration": "166 min", ... }
]}

// showings.json
{ "showings": [
  { "film_id": "Dune Parte 2", "cinema_slug": "uci-perugia",
    "date": "2026-06-30", "times": ["18:00", "21:30"], ... }
]}
```

**Stato DB dopo seed**:

```sql
SELECT * FROM films WHERE wikidata_id = 'Q97154362';
-- id=42, title='Dune — Parte 2', title_normalized='dune parte 2',
-- year=2024, director='Denis Villeneuve', runtime_minutes=166, ...

SELECT * FROM showings WHERE film_id = 42 AND date = '2026-06-30';
-- id=789, film_id=42, cinema_slug='uci-perugia', times='["18:00","21:30"]'
```

**Risposta endpoint `GET /api/v1/films/42`**:

```json
{
  "id": 42,
  "title": "Dune — Parte 2",
  "year": 2024,
  "runtime_minutes": 166,
  "director": "Denis Villeneuve",
  "showings": [
    { "id": 789, "date": "2026-06-30", "times": ["18:00", "21:30"], "cinema_slug": "uci-perugia" }
  ]
}
```

---

## 7. Checklist prima di scrivere `seed.py`

- [ ] Tutti e 3 i JSON disponibili in `SCRAPER_OUTPUT_DIR` (config).
- [ ] Funzione `normalize_title(s: str) -> str` definita in `film_service.py` (vedi TODO lì).
- [ ] Helper `parse_minutes(s: str | None) -> int | None` (es. `"95 min"` → `95`).
- [ ] Repository `upsert(...)` per tutti e 3 i modelli.
- [ ] Logger configurato per warning/error con record context.
- [ ] Idempotenza: rieseguire il seed N volte sullo stesso JSON deve produrre lo stesso DB.
- [ ] Smoke test: dopo seed verifica `SELECT COUNT(*) FROM cinemas/films/showings` con i numeri attesi (oggi: 3 cinema, ~22 film, ~310 showings).
