# App — React Native + Expo

App mobile/web di CinePosto: mostra i film in programmazione nei cinema dell'Umbria,
con orari per data e cinema, ricerca, dettaglio film e mappa. Consuma il backend
FastAPI del monorepo.

Stato: **integrata e funzionante su web e smartphone**, agganciata al backend
(non più mock). Sostituisce la vecchia app placeholder basata su Expo Router.

---

## Stack

| Cosa | Versione / scelta |
|---|---|
| React Native | 0.81.5 |
| Expo | SDK 54 (massimo compatibile con Expo Go) |
| React | 19.1.0 |
| Navigazione | **React Navigation 7** (bottom-tabs + native-stack) — entry classico `App.js`, *non* Expo Router |
| Linguaggio | JavaScript `.js` |
| Web | `react-native-web` 0.21 (stessa codebase per il browser) |
| Mappa | Leaflet dentro `react-native-webview` (nativo) / `<iframe>` (web) |
| Storage locale | `@react-native-async-storage/async-storage` (preferiti) |

> **NON usare `npx create-expo-app`**: installa sempre l'SDK più recente (55+),
> incompatibile con Expo Go. Il progetto è già inizializzato: basta `npm install`.

---

## Struttura

```
app/
├── App.js                 ← root: splash + navigazione (tab + stack annidati)
├── index.js               ← registerRootComponent(App)
├── app.json               ← name "CinePosto", slug "cineposto", tema scuro
├── package.json           ← dipendenze SDK 54
├── babel.config.js        ← babel-preset-expo
├── metro.config.js        ← shim web per react-native-webview
├── shims/                 ← codegenNativeComponent.web.js (compat web WebView)
├── assets/                ← logo, icone, loghi cinema (post.jpg, uci.png, the-space.jpg)
└── src/
    ├── api/api.js         ← client HTTP verso il backend + preferiti locali
    ├── constants/
    │   ├── config.js      ← API_BASE (configurabile via env)
    │   ├── colors.js      ← palette tema scuro
    │   └── cinemas.js     ← dati statici dei 3 cinema (slug, colore, coordinate, logo)
    ├── utils/dates.js     ← date in ora locale (YYYY-MM-DD), prossimi 7 giorni
    ├── components/
    │   ├── SwipeableHero.js   ← carosello "hero" della Home
    │   ├── MovieGrid.js       ← griglia locandine adattiva
    │   ├── DateBar.js         ← barra date (oggi + 6 giorni)
    │   ├── PosterImage.js     ← poster con gestione immagini panoramiche
    │   ├── SplashScreen.js    ← animazione logo all'avvio
    │   ├── CinemaMap.js       ← mappa nativa (WebView)
    │   ├── CinemaMap.web.js   ← mappa web (iframe) — Metro sceglie in automatico
    │   └── mapHtml.js         ← HTML Leaflet condiviso dalle due mappe
    └── screens/
        ├── FilmsTab.js        ← Home "Films"
        ├── SearchTab.js       ← "Cerca"
        ├── LocationTab.js     ← "Località" (mappa)
        └── MovieDetailScreen.js ← dettaglio film
```

---

## Navigazione (`App.js`)

All'avvio parte lo `SplashScreen` animato; a fine animazione si passa alla
`NavigationContainer`. La navigazione è un **bottom-tab** con tre voci:

- **Films** e **Cerca** sono in realtà due piccoli *stack* (lista → dettaglio):
  così `MovieDetailScreen` si apre **dentro** la tab, mantenendo la barra in basso.
- **Località** è una schermata singola (la mappa).

```
SplashScreen
  └─ NavigationContainer
       └─ Bottom Tabs
            ├─ Films   → Stack(FilmsHome, MovieDetail)
            ├─ Cerca   → Stack(SearchHome, MovieDetail)
            └─ Località → LocationTab
```

---

## Schermate

- **FilmsTab** (Home): costruisce l'elenco film **dagli spettacoli della data
  selezionata** (ogni spettacolo del backend porta con sé il film annidato), quindi
  ogni giorno mostra esattamente ciò che è in cartellone. In cima un carosello
  `SwipeableHero` con i primi film; sotto la `DateBar` (7 giorni) e la `MovieGrid`.
  C'è un filtro per cinema (modal) e il pull-to-refresh.
- **SearchTab** (Cerca): ricerca per titolo con **debounce 300 ms** e annullamento
  delle risposte obsolete (`requestId`): se digiti in fretta conta solo l'ultima query.
- **LocationTab** (Località): mappa Leaflet con i tre cinema (marker con logo) e
  l'elenco con indirizzi; il tap apre il cinema in Google Maps. I dati dei cinema
  qui sono statici (`constants/cinemas.js`), incluse le coordinate.
- **MovieDetailScreen** (dettaglio): poster, durata, regista, generi, trama con
  "leggi di più", link al trailer (ricerca YouTube) e **orari raggruppati per cinema**
  nella data scelta. Si apre sulla data da cui arrivi (passata dalla Home) e, se quel
  film in quella data non ha orari, salta alla prima data utile.

## Componenti chiave

- **SwipeableHero**: carosello a **scorrimento manuale** (niente auto-scroll) con
  indicatore a pallini. Ogni slide ha una **locandina piccola e nitida** più lo
  stesso poster **sfocato** come sfondo (i poster dei cinema sono a bassa risoluzione:
  a schermo pieno e nitidi risulterebbero sgranati).
- **PosterImage**: se un poster è panoramico (16:9) invece che verticale (2:3), lo
  mostra intero sopra una versione sfocata e scurita di sé stesso, senza deformarlo.
- **CinemaMap**: usa `react-native-webview` sul telefono e un `<iframe>` sul web (Metro
  carica `CinemaMap.web.js` da solo). L'HTML Leaflet è condiviso (`mapHtml.js`).

---

## Client API (`src/api/api.js`)

Chiama il backend via `fetch`; l'indirizzo base è in `constants/config.js`.

| Funzione | Endpoint backend |
|---|---|
| `getFilmsToday()` | `GET /film/oggi` |
| `searchFilms(q)` | `GET /film/search?q=` |
| `getFilmById(id)` | `GET /film/{id}` |
| `getCinemas()` | `GET /cinema` |
| `getCinemaShowings(slug, from, to)` | `GET /cinema/{slug}/showings?date_from=&date_to=` |

I preferiti (`addFavorite`, `getFavorites`, …) sono **locali**, salvati in AsyncStorage.

> **Forma dei dati**: gli spettacoli del backend (`ShowingDetail`) hanno il film e il
> cinema **annidati** → si leggono `s.film.id` e `s.cinema.slug` (non campi piatti).

### Indirizzo del backend — `config.js`

```js
export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';
```

Si sovrascrive a runtime con la variabile d'ambiente **`EXPO_PUBLIC_API_BASE`**, che
Expo inserisce nel bundle all'avvio. `localhost` va bene su web e simulatore iOS; su un
**telefono reale** (Expo Go) serve l'**IP di rete locale** del computer che esegue il backend.

---

## Come si avvia (backend + app)

L'app da sola non basta: serve il backend acceso con dati seedati.

### 1. Backend

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate   # Python 3.12 OBBLIGATORIO
pip install -r requirements.txt
python -m app.seed_from_json                          # popola cineposto.db dai JSON scraper
uvicorn app.main:app --host 0.0.0.0 --port 8000       # 0.0.0.0 = raggiungibile dal telefono
```

### 2. App

```bash
cd app
npm install
# IP LAN del Mac (macOS): ipconfig getifaddr en0
EXPO_PUBLIC_API_BASE="http://<IP-LAN>:8000/api/v1" npx expo start
```

- **Web** → apri `http://localhost:8081` (o premi `w`).
- **Telefono** → apri **Expo Go** e scansiona il QR (telefono e Mac sulla **stessa Wi-Fi**;
  se macOS chiede di consentire connessioni in entrata, accetta).

### Build web statica

```bash
npx expo export --platform web    # output in dist/
```

---

## Note tecniche (dietro le scelte)

- **Sfocatura poster**: `blurRadius` (prop React Native) funziona su iOS/Android ma
  **non** su `react-native-web`; sul web la sfocatura è fatta con la CSS `filter: blur()`.
- **Mappa**: le tile arrivano dal CDN CARTO e Leaflet da unpkg → **la mappa richiede
  internet** (non è offline). Alla demo serve connessione.
- **Date in ora locale**: `utils/dates.js` evita `toISOString()` (UTC), che tra
  mezzanotte e le 2 avrebbe restituito la data di ieri.
