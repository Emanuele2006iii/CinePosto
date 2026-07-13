# App — Integrazione nel monorepo e fix applicati

Racconta come l'app (sviluppata a parte da un membro del team come progetto Expo
autonomo) è stata **integrata nel monorepo** e agganciata al backend, e quali
problemi sono stati risolti per renderla funzionante su web e smartphone.

Il codice ricevuto era di buona qualità: i problemi erano soprattutto di
**allineamento** tra app e backend e un **bug nel seed del backend**, non difetti
dell'app in sé.

---

## 1. Integrazione nel monorepo

- L'app arrivava come progetto Expo standalone (entry classico `App.js` +
  React Navigation), diverso dal placeholder `app/` presente nel repo (Expo Router).
  Il placeholder è stato **sostituito** con l'app reale sotto `app/`.
- **Rebrand** a CinePosto: `package.json` (`name: cineposto-app`) e `app.json`
  (`name: CinePosto`, `slug: cineposto`).
- Rimosso il superfluo dal sorgente versionato: `node_modules`, `.expo`, `.idea`,
  `Memory.md`, `movies.json`/`backup_movies.json` (dati locali non usati),
  duplicati dei loghi in root. Aggiunto un `.gitignore` Expo.

## 2. Riconciliazione del contratto API

L'app era stata scritta contro un backend con nomi/forme diversi. Adattata **lato
app** (il backend ha 26 test verdi, si preferisce non toccarlo):

**URL** — l'app usava plurale inglese, il backend usa singolare:

| Prima (app) | Backend reale |
|---|---|
| `/films/today`, `/films/search`, `/films/{id}` | `/film/oggi`, `/film/search`, `/film/{id}` |
| `/cinemas`, `/cinemas/{slug}/showings` | `/cinema`, `/cinema/{slug}/showings` |

**Forma dei dati** — gli spettacoli del backend (`ShowingDetail`) hanno film e
cinema **annidati**; l'app leggeva campi piatti inesistenti:

- `showing.film_id` → **`showing.film.id`**
- `showing.cinema_slug` → **`showing.cinema.slug`**

**Indirizzo backend** — l'IP era hardcoded. Ora `config.js` usa
`process.env.EXPO_PUBLIC_API_BASE` (con default `localhost`), così si punta all'IP
LAN del Mac senza modificare il codice.

## 3. Pipeline dati (dati freschi)

I dati erano vecchi (fermi a inizio luglio). Rilanciato lo scraper
(`python -m scraper.main --once`) e ri-seedato il DB da zero → dati correnti che
coprono la settimana della demo.

## 4. Bug e correzioni

### 4.1 Orari mancanti — bug del seed (il più importante)

**Sintomo**: nel dettaglio, un film di The Space mostrava **un solo orario** invece
dei ~13 reali del sito.

**Causa**: The Space pubblica lo stesso film in più sale; lo scraper produceva
correttamente **un record per sala** (ognuno con i suoi orari). Ma la tabella
`showings` ha `UNIQUE(film_id, cinema_slug, date)`: il seed faceva un upsert per
record, quindi **l'ultima sala sovrascriveva le precedenti**, perdendo gli orari.

**Fix** (`backend/app/seed_from_json.py`): il seed ora **pre-aggrega** gli
spettacoli per `(film, cinema, data)` e **unisce tutti gli orari** in un'unica
riga (lo `screen` si conserva solo se proviene da un'unica sala). Verifica: Odissea
16/07 @ The Space passa da **1 a 12 orari**. 26 test backend ancora verdi.

### 4.2 Film duplicati in ricerca

Un primo seed aveva unito dati vecchi e nuovi, lasciando **12 film "stale"** senza
orari (es. *"BACKROOMS"* vecchio + *"BACKROOMS – EVERYTHING MUST GO EDITION"* nuovo).
Risolto con un **re-seed pulito** (drop tabelle + seed dei soli film correnti).

### 4.3 Giorni "vuoti" nella Home

La Home partiva dai *"film di oggi"* e li filtrava per data: nelle date diverse da
oggi perdeva dei film. Ora `FilmsTab` costruisce la lista **dagli spettacoli della
data selezionata**, così ogni giorno mostra il proprio cartellone.
(Nota: i giorni molto avanti restano scarni perché i cinema pubblicano il palinsesto
~3 giorni prima — è dato reale, non un bug.)

### 4.4 Dettaglio senza orari

Il dettaglio si apriva sempre su *oggi*; molti film sono programmati in un solo
giorno, quindi risultavano senza orari. Ora `MovieDetailScreen` si apre sulla data
da cui arrivi (passata dalla Home) e, se lì non ci sono orari, **salta alla prima
data utile** del film.

### 4.5 Carosello Home (hero)

- Rimosso l'**auto-scroll** (scattava e "girava da solo").
- I poster dei cinema sono a **bassa risoluzione**: a schermo pieno e nitidi erano
  sgranati, e con aspect ratio diversi davano banner disuniformi. Soluzione:
  **locandina piccola e nitida** (dimensione fissa) su **sfondo sfocato** dello
  stesso poster — uniforme per ogni film.
- Sfocatura cross-platform: `blurRadius` su iOS/Android, **CSS `filter: blur()`**
  su web (dove `blurRadius` non ha effetto).
- Indicatore a pallini reso robusto (ignora offset di scroll spuri sul web).

## 5. Pulizia codice

- Rimosso `CinemaTab.js` (schermata mai collegata alla navigazione).
- Rimossa la dipendenza `expo-file-system` (non più usata).
- Aggiunto in testa a ogni file sorgente un commento che ne descrive lo scopo.

## 6. Verifica finale

- **Compilazione**: tutti i 19 file JS passano il transform di Babel.
- **Backend**: 26 test verdi.
- **Smoke end-to-end** su tutti gli endpoint usati dall'app: `/film/oggi` (17 film,
  17/17 con poster), `/cinema` (3), `/film/search`, `/cinema/{slug}/showings`
  (Odissea 16/07 → 12 orari), `/film/{id}`.

## 7. Limite noto

La **mappa** (Località) carica Leaflet da CDN e le tile da CARTO → **richiede
internet**. Alla demo serve connessione di rete.
