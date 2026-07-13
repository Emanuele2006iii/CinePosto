# CinePosto — Contratto API (v1)

> **Contratto autorevole degli endpoint**: URL, forma delle risposte, affidabilità
> dei dati, CORS. L'app è ora costruita e integrata — per il **client reale** vedi
> [app/overview.md](../app/overview.md) e [app/integrazione-e-fix.md](../app/integrazione-e-fix.md).
> Gli snippet lato-app qui sotto (config, client, checklist) restano come **riferimento storico**.
>
> ⚠️ **La §9 "Affidabilità dei dati" resta obbligatoria**: molti campi arrivano `null`
> perché lo scraper dipende da fonti esterne (siti cinema + Wikidata).

**API version**: `v1`

---

## 1. Base URL e configurazione

| Ambiente | Base URL | Note |
|---|---|---|
| **Dev locale (backend nel tuo Mac)** | `http://localhost:8000/api/v1` | avvia backend con `uvicorn app.main:app --reload --port 8000` |
| **Dev su VM Linux del team** | `http://<vm-ip>:8000/api/v1` | Yonas condivide l'IP nel canale team |
| **Prod (dopo deploy)** | `https://api.cineposto.it/api/v1` | placeholder — da definire prima della consegna |

Nell'app RN, metti la base URL in un file di config:

```js
// app/config.js
export const API_BASE_URL = __DEV__
  ? 'http://localhost:8000/api/v1'
  : 'https://api.cineposto.it/api/v1';
```

Su Android, se il backend gira sul PC (non sull'emulatore), invece di `localhost` usa `10.0.2.2` (Android emulator) o l'IP LAN del Mac (iOS device fisico).

---

## 2. Convenzioni

| Cosa | Convenzione |
|---|---|
| **Content-Type richiesta** | `application/json` (solo su POST admin, GET non richiede body) |
| **Content-Type risposta** | `application/json; charset=utf-8` |
| **Formato date** | `YYYY-MM-DD` (ISO 8601), es. `"2026-07-02"` |
| **Formato orari** | Array di stringhe `"HH:MM"`, es. `["18:30", "21:00"]` |
| **Encoding** | UTF-8 (accenti, caratteri speciali gestiti) |
| **Timezone** | Europe/Rome (dati sono locali umbri) |
| **Paginazione** | Nessuna nella v1 (dataset piccolo: max ~500 record) |
| **CORS** | Backend accetta origini configurate in `.env`; per dev locale già configurato per `localhost:*` ed Expo Go |

---

## 3. Shape delle risposte (JSDoc — copia in `app/api/schemas.js`)

Il progetto è **JavaScript** (`.jsx`), non TypeScript. Per avere comunque **autocomplete** e **type-checking** nell'editor (VS Code), usa JSDoc: sono commenti che VS Code capisce.

```js
// app/api/schemas.js
// Documentazione degli oggetti restituiti dall'API — solo commenti JSDoc,
// niente runtime overhead. VS Code offre autocomplete su tutti questi tipi.

/**
 * @typedef {Object} Cinema
 * @property {string} slug           - PK, es. "postmodernissimo". Usalo come key nelle liste.
 * @property {string} name           - es. "PostModernissimo"
 * @property {string} city           - es. "Perugia"
 * @property {string} address
 * @property {string} region         - es. "Umbria"
 * @property {number} lat
 * @property {number} lon
 * @property {string|null} website
 * @property {string|null} phone
 */

/**
 * @typedef {Cinema & { showings_count: number }} CinemaWithCount
 */

/**
 * @typedef {Object} Film
 * @property {number} id             - PK intero
 * @property {string} title
 * @property {number|null} year
 * @property {number|null} runtime_minutes
 * @property {string|null} genres    - CSV: "Drama,Thriller" — parseLo con .split(',')
 * @property {string|null} poster_url
 */

/**
 * @typedef {Object} FilmDetail
 * @property {number} id
 * @property {string} title
 * @property {number|null} year
 * @property {number|null} runtime_minutes
 * @property {string|null} genres
 * @property {string|null} poster_url
 * @property {string|null} original_title
 * @property {string|null} director
 * @property {string|null} synopsis
 * @property {string|null} wikidata_id
 * @property {Showing[]} showings    - prossimi spettacoli, ordinati per data
 */

/**
 * @typedef {Object} Showing
 * @property {number} id
 * @property {string} date           - "2026-07-02" — parseLo con new Date(date)
 * @property {string[]} times        - ["18:30", "21:00"]
 * @property {string|null} language  - "ITA" | "ENG" | "ORIG-SUB" | null
 * @property {string|null} screen    - "Sala 1"
 * @property {string|null} buy_url   - link diretto per acquisto biglietto
 */

/**
 * @typedef {Showing & { cinema: Cinema, film: Film }} ShowingDetail
 */

/**
 * @typedef {Object} ApiError
 * @property {string} detail         - es. "Cinema non trovato"
 */

// Non c'e' nulla da esportare: questi sono solo commenti per l'IDE.
export {};
```

**Come usare i tipi nei tuoi file `.jsx`**:

```jsx
// app/(tabs)/index.jsx
import { apiGet } from '../api/client';

/**
 * @param {import('../api/schemas').Film[]} films
 */
function FilmList({ films }) {
  return films.map(f => (
    <View key={f.id}>
      <Text>{f.title}</Text>
    </View>
  ));
}

// Dentro il componente
/** @type {import('../api/schemas').Film[]} */
const films = await apiGet('/film/oggi');
```

VS Code darà autocomplete su `f.title`, `f.poster_url`, ecc., e ti avvisa se scrivi `f.titel` (typo).

---

## 4. Endpoint disponibili

### 4.1 `GET /cinema` — Lista tutti i cinema

**URL**: `GET /api/v1/cinema`
**Query params**: nessuno
**Response**: `Cinema[]` (ordinati per name)

**Esempio richiesta**:
```bash
curl http://localhost:8000/api/v1/cinema
```

**Esempio risposta** (200 OK):
```json
[
  {
    "slug": "postmodernissimo",
    "name": "PostModernissimo",
    "city": "Perugia",
    "address": "Via del Milite Ignoto 1, 06121 Perugia PG",
    "region": "Umbria",
    "lat": 43.1107,
    "lon": 12.3882,
    "website": "https://www.postmodernissimo.com",
    "phone": null
  },
  { "slug": "the-space-corciano", "...": "..." },
  { "slug": "uci-perugia", "...": "..." }
]
```

**Snippet fetch** (RN/Expo):
```js
/**
 * @returns {Promise<import('./schemas').Cinema[]>}
 */
async function fetchCinemas() {
  const res = await fetch(`${API_BASE_URL}/cinema`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

---

### 4.2 `GET /cinema/{slug}` — Dettaglio cinema

**URL**: `GET /api/v1/cinema/{slug}`
**Path params**: `slug` (string, es. `postmodernissimo`)
**Response**: `CinemaWithCount`

**Esempio risposta** (200 OK):
```json
{
  "slug": "postmodernissimo",
  "name": "PostModernissimo",
  "city": "Perugia",
  "address": "...",
  "region": "Umbria",
  "lat": 43.1107,
  "lon": 12.3882,
  "website": "...",
  "phone": null,
  "showings_count": 42
}
```

**Errori**: `404 Not Found` se `slug` non esiste.

---

### 4.3 `GET /cinema/{slug}/showings` — Programmazione di un cinema

**URL**: `GET /api/v1/cinema/{slug}/showings?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
**Path params**: `slug`
**Query params** (entrambi opzionali):
- `date_from` (default: oggi)
- `date_to` (default: +7 giorni)

**Response**: `ShowingDetail[]` — include il film per ogni spettacolo (niente N+1 lato client).

**Esempio richiesta**:
```bash
curl "http://localhost:8000/api/v1/cinema/postmodernissimo/showings?date_from=2026-07-02&date_to=2026-07-08"
```

**Esempio risposta**:
```json
[
  {
    "id": 128,
    "date": "2026-07-02",
    "times": ["18:30", "21:00"],
    "language": "ITA",
    "screen": "Sala 1",
    "buy_url": "https://www.postmodernissimo.com/...",
    "film": {"id": 7, "title": "Dune", "year": 2021, ...},
    "cinema": { "...": "..." }
  }
]
```

**Errori**: `404` se `slug` non esiste; **NON** ritorna 404 se semplicemente non ci sono showings → ritorna `[]`.

---

### 4.4 `GET /film/oggi` — Film in programmazione oggi

**URL**: `GET /api/v1/film/oggi`
**Response**: `Film[]` (versione "card", senza sinossi/regista)

Uso principale: **schermata Home**, l'app la chiama al mount.

**Esempio risposta**:
```json
[
  {
    "id": 7,
    "title": "Dune",
    "year": 2021,
    "runtime_minutes": 155,
    "genres": "Drama,Sci-Fi",
    "poster_url": "https://..."
  }
]
```

---

### 4.5 `GET /film/settimana` — Film nei prossimi 7 giorni

**URL**: `GET /api/v1/film/settimana`
**Response**: `Film[]`

Uguale a `oggi` ma range più ampio (oggi → +6 giorni).

---

### 4.6 `GET /film/{id}` — Dettaglio film

**URL**: `GET /api/v1/film/{id}`
**Path params**: `id` (integer)
**Response**: `FilmDetail` — versione completa con sinossi + `showings[]`

**Esempio risposta**:
```json
{
  "id": 7,
  "title": "Dune",
  "year": 2021,
  "runtime_minutes": 155,
  "genres": "Drama,Sci-Fi",
  "poster_url": "https://...",
  "original_title": "Dune",
  "director": "Denis Villeneuve",
  "synopsis": "Un giovane uomo si ritrova coinvolto in una lotta...",
  "wikidata_id": "Q97154362",
  "showings": [
    { "id": 128, "date": "2026-07-02", "times": ["18:30"], "..." : "..."}
  ]
}
```

**Errori**: `404` se `id` non esiste.

---

### 4.7 `GET /film/search?q=...` — Ricerca per titolo

**URL**: `GET /api/v1/film/search?q=dune&limit=20`
**Query params**:
- `q` (obbligatorio, min 2 caratteri; sotto → `[]`)
- `limit` (default 20)

**Response**: `Film[]`

Ricerca case-insensitive, ignora punteggiatura/accenti (es. "citta" trova "città").

Uso principale: **barra ricerca** con debounce lato app (300ms) per non spammare.

---

### 4.8 `GET /showings?date=YYYY-MM-DD` — Spettacoli di una data

**URL**: `GET /api/v1/showings?date=YYYY-MM-DD`
**Query params**: `date` (opzionale, default: oggi)

**Response**: `ShowingDetail[]` — include cinema e film per ogni showing.

Uso: **schermata "cosa danno oggi in tutti i cinema"**.

---

### 4.9 `GET /health` — Liveness probe

**URL**: `GET /health` (NB: no `/api/v1` prefix)
**Response**: `{"status": "ok"}`

Usato da UptimeRobot / monitoring. L'app **non** lo chiama.

---

## 5. Codici HTTP che devi gestire

| Codice | Significato | Cosa fai nell'app |
|---|---|---|
| **200** | OK | Mostra dati |
| **404** | Risorsa non esiste (film_id o cinema_slug errato) | Mostra schermata "non trovato" |
| **422** | Query param malformato (es. `date=pippo`) | Mostra errore "parametri non validi" — bug tuo, non del backend |
| **500** | Errore server | Mostra "riprova più tardi" |
| **Network error** | Backend giù o offline | Cache locale se disponibile, altrimenti "offline" |

---

## 6. CORS (per l'app web build)

Il backend accetta richieste da questi origin (lista in `.env`):
- `http://localhost:8081` (Metro bundler)
- `http://localhost:19006` (Expo web)
- `https://cineposto.pages.dev` (Cloudflare Pages prod)

Se aggiungi un altro origin, chiedi a Emanuele/Yonas di aggiornare `.env` e riavviare il backend.

---

## 7. Client HTTP consigliato

**Nella v1**: nativo `fetch` va benissimo. Non serve axios.

Client centralizzato consigliato (`app/api/client.js`):

```js
import { API_BASE_URL } from '../config';

export class ApiError extends Error {
  constructor(status, detail) {
    super(`API ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

/**
 * GET generico verso l'API. Ritorna il JSON parsato.
 * Lancia ApiError se lo status non e' 2xx.
 *
 * @param {string} path - path relativo, es. "/film/oggi"
 * @returns {Promise<any>}
 */
export async function apiGet(path) {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch { /* body non JSON, tengo il default */ }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}
```

Uso:
```jsx
import { apiGet } from './api/client';

/** @type {import('./api/schemas').Film[]} */
const films = await apiGet('/film/oggi');
```

---

## 8. Suggerimenti operativi per l'app

### Quando caricare cosa

| Schermata | Endpoint |
|---|---|
| Home "Film oggi" | `GET /film/oggi` al mount |
| Home filtro "settimana" | `GET /film/settimana` al cambio filtro |
| Lista cinema | `GET /cinema` al mount |
| Dettaglio cinema | `GET /cinema/{slug}` + `GET /cinema/{slug}/showings` |
| Dettaglio film | `GET /film/{id}` (contiene già `showings[]`) |
| Ricerca | `GET /film/search?q=...` con debounce 300ms |
| Mappa | `GET /cinema` (usa lat/lon di ogni cinema per i marker) |

### Cache lato client

Il dataset è piccolo (~500 record totali) e cambia ogni 24h. Puoi:
- Fare cache in memoria durante la sessione (state React)
- Usare `AsyncStorage` per persistere la lista cinema (raramente cambia)
- **Non** serve react-query in v1; se in futuro serve refetch complesso, si valuterà

### Poster mancanti

`poster_url` può essere `null` per film di nicchia. Preparate un placeholder image nell'app.

### Buy URL

`buy_url` in `Showing` può essere `null` per PostModernissimo (che non ha e-commerce). Se null → nascondi il bottone "Acquista".

---

## 9. Affidabilità dei dati (LEGGERE PRIMA DI PROGETTARE L'UI)

⚠️ **La sorgente dati è fragile**: lo scraper prende i film dai siti dei cinema e li arricchisce con Wikidata. Molti film di nicchia o appena usciti **non sono su Wikidata** → alcuni campi arrivano `null`. Se l'UI dà per scontato che siano sempre presenti, si rompe.

Le percentuali qui sotto sono **misurate al 2026-07-02 sul dataset reale** (19 film, 241 spettacoli, 3 cinema).

### 🟢 SEMPRE presenti (100%) — usa senza `if`

| Campo | Dove | Uso tipico UI |
|---|---|---|
| `title` | `Film` | Titolo mostrato |
| `poster_url` | `Film` | Locandina in card e dettaglio |
| `synopsis` | `Film` | Testo descrittivo |
| `cinema.slug` `name` `city` `address` `region` `lat` `lon` `website` | `Cinema` | Card cinema, marker mappa, link sito |
| `date` `times` | `Showing` | Data + array orari |
| `buy_url` | `Showing` | Bottone "Acquista biglietto" |

### 🟡 QUASI sempre (89-95%) — controlla ma affidati

| Campo | Copertura | Se null → azione UI |
|---|---|---|
| `film.director` | 95% (1/19 null) | Nascondi la riga *"Regia:"* |
| `showing.language` | 89% | Nascondi il tag lingua (ITA/ENG/…) |
| `showing.screen` | 89% | Nascondi "Sala X" |

### 🟠 SPESSO ma non sempre (69-74%) — SEMPRE fallback

| Campo | Copertura | Se null → azione UI |
|---|---|---|
| `film.runtime_minutes` | 74% | Non mostrare "durata", oppure "—" |
| `film.genres` | 69% | Non mostrare chip generi. **Formato**: CSV `"Drama,Thriller"` → `.split(',')` |

### 🔴 META' delle volte (37%) — assumi che sia null

| Campo | Copertura | Se null → azione UI |
|---|---|---|
| `film.year` | 37% | Non mostrare `"(2024)"` accanto al titolo |
| `film.original_title` | 16% | Nascondi la riga *"Titolo originale:"* |
| `film.wikidata_id` | 37% | **Uso interno**, l'app non lo mostra |

### ⚫ SEMPRE null (0%) — non usare proprio

| Campo | Perché |
|---|---|
| `cinema.phone` | Non presente nella config sorgente. Ignora nell'UI. |

### 6 regole d'oro per l'app

1. **Optional chaining ovunque**: `film?.director`, `showing?.language`
2. **Null coalescing** con placeholder: `film.runtime_minutes ?? '—'`
3. **`genres` è CSV, non array**: `film.genres?.split(',') ?? []` (già scritto qui per non sbagliare)
4. **`times` invece è già array**: `showing.times[0]` funziona direttamente, no parse
5. **`date` è stringa ISO** `"2026-07-02"`: parsa con `new Date(showing.date)` per formattare
6. **`year`, `original_title`, `phone`** → considerali sempre null di default, mostra solo se presenti

### Esempio pattern React Native

```jsx
// ✅ FilmCard difensivo
function FilmCard({ film }) {
  const genres = film.genres?.split(',') ?? [];

  return (
    <View>
      <Image source={{ uri: film.poster_url }} />
      <Text style={styles.title}>
        {film.title}{film.year && ` (${film.year})`}
      </Text>
      {film.director && <Text>Regia: {film.director}</Text>}
      {film.runtime_minutes && <Text>{film.runtime_minutes} min</Text>}
      {genres.length > 0 && (
        <View style={styles.chips}>
          {genres.map(g => <Chip key={g}>{g.trim()}</Chip>)}
        </View>
      )}
      <Text>{film.synopsis}</Text>
    </View>
  );
}
```

### Cosa NON promettere all'utente

- ❌ Filtro "anno" — solo 37% dei film ha `year`, il filtro funzionerebbe male
- ❌ Filtro "genere" con menu di tutti i generi — parte dei film non ha genres
- ❌ "Ricerca avanzata regista/durata" — coperture troppo variabili
- ✅ Ricerca per titolo → `title` è sempre presente, funziona bene
- ✅ Filtro per data → sempre presente sui showings
- ✅ Filtro per cinema → tutti i cinema hanno slug

---

## 10. Errori comuni da evitare

| ❌ Errore | ✅ Fix |
|---|---|
| Chiamare `/api/v1/cinemas` (plurale) | È `/cinema` (singolare in URL, plurale nella response) |
| Chiamare `film_id` come stringa (`"7"`) | È **numero** intero, cast prima di passare in URL |
| Parse `times` con `JSON.parse` | Già array, `times[0]` diretto |
| Non gestire `null` sui campi opzionali | Molti campi possono essere `null` — usa `??` o optional chaining |
| Non escapare `q` nella search | Usa `encodeURIComponent(q)` nell'URL |
| Hardcode `http://localhost:8000` | Usa `API_BASE_URL` da config |

---

## 11. Cosa NON esiste ancora (non chiedeteci)

- **Autenticazione utente**: non esiste, app pubblica read-only
- **Preferiti**: fuori scope MVP
- **Notifiche push**: RNF opzionale, non priorità
- **Recensioni utenti**: fuori scope
- **Trailer video**: fuori scope
- **Acquisto biglietti in-app**: rimandiamo al `buy_url`

---

## 12. Contatti per problemi

- **Backend rotto o dati sbagliati** → Emanuele
- **CORS o deploy** → Yonas
- **Struttura API cambia** → si aggiorna QUESTO documento + si notifica in canale team

---

## 13. Checklist per il team frontend (Andrea)

- [ ] Ho copiato `app/api/schemas.js` (JSDoc types)
- [ ] Ho creato `app/config.js` con `API_BASE_URL`
- [ ] Ho creato `app/api/client.js` con `apiGet`
- [ ] Sostituito `MOCK_FILMS` con `apiGet('/film/oggi')` nella Home
- [ ] Sostituito `CINEMAS` con `apiGet('/cinema')` nella tab Cinema
- [ ] Gestito loading state (spinner) + error state (retry)
- [ ] Installato `react-native-maps` (per la mappa, Sprint 4)
- [ ] Testato con backend locale
- [ ] Testato con backend su VM Linux (endpoint remoto)
