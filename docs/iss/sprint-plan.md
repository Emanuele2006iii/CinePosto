---
aliases:
  - CinePosto — Piano degli Sprint e dei Rilasci
linter-yaml-title-alias: CinePosto — Piano degli Sprint e dei Rilasci
---

# CinePosto — Piano degli Sprint e dei Rilasci

| **Progetto**   | CinePosto                                                          |
| -------------- | ------------------------------------------------------------------ |
| **Team**       | RepCode                                                            |
| **Componenti** | Emanuele Ceccariglia, Elio Casciola, Andrea Cestelli, Yonas Burka |
| **Corso**      | Ingegneria del Software — ITS Umbria Academy, a.a. 2025/2026       |

> **Aggiornamento 2026-07-02**: Sprint 2 ✅ **completato** (data prevista era 01/07, chiuso il 02/07). Backend: 11 endpoint funzionanti + seed dai JSON + 26 test verdi. Scraper arricchito con `year` (P577 Wikidata) + `wikidata_id`. Sprint 3 (app + fetch reali) pronto a partire.

---

## User Stories di riferimento

Derivate dai Requisiti Funzionali dell'Analisi dei Requisiti.

| ID    | User Story                                                                                                       | RF collegato |
| ----- | ---------------------------------------------------------------------------------------------------------------- | ------------ |
| US-01 | Come utente voglio vedere la lista di tutti i cinema umbri con nome, indirizzo e link al sito ufficiale         | RF-01        |
| US-02 | Come utente voglio vedere la programmazione di ogni cinema (film, orari, giorni disponibili)                    | RF-02        |
| US-03 | Come utente voglio vedere i cinema su una mappa interattiva con marker cliccabili                               | RF-03        |
| US-04 | Come utente voglio filtrare la programmazione per data (oggi, domani, questa settimana)                         | RF-04        |
| US-05 | Come utente voglio filtrare cinema e spettacoli per comune o zona geografica                                    | RF-05        |
| US-06 | Come utente voglio vedere la scheda di un film (titolo, genere, durata, poster, sinossi)                        | RF-06        |
| US-07 | Come utente voglio accedere con un click al sito del cinema per acquistare il biglietto                         | RF-07        |
| US-08 | Come amministratore voglio che i dati vengano aggiornati ogni 24h rispettando robots.txt di ogni fonte          | RF-08, RF-09 |
| US-09 | Come utente voglio cercare un film per titolo                                                                   | RF-10        |
| US-10 | Come utente voglio essere avvisato quando i dati di un cinema non sono aggiornati da più di 48 ore              | RF-11        |

---

# PARTE 1 — Piano degli Sprint

## Sprint 1 — Scraper: raccolta dati dalla fonte

| Campo              | Valore                          |
| ------------------ | ------------------------------- |
| **Data inizio**    | 2026-06-02                      |
| **Data fine**      | 2026-06-15                      |
| **Stato**          | ✅ Completato                    |

**User stories implementate:**
- US-08 — Scraping automatico schedulato ogni 24h, con rispetto di robots.txt e rate limiting (max 1 req/s per dominio)

**Motivazione della scelta:**
Lo scraper è la fondamenta dell'intero sistema: senza dati aggiornati dalla fonte non esiste nulla da mostrare. È stato scelto come primo sprint per validare la fattibilità tecnica (i siti dei cinema sono scrapabili?) prima di costruire backend e app.

**Dipendenze:**
Nessuna — è il componente di partenza dell'architettura.

**Risultati:**
- Scraper funzionante per 3 cinema (PostModernissimo, The Space Corciano, UCI Perugia)
- Arricchimento dati via Wikidata (poster, regista, durata)
- Output JSON DB-ready: `movies.json` (stato interno), `films.json`, `showings.json`, `cinemas.json`
- 75 test, lint ruff pulito, deploy via systemd su Linux

---

## Sprint 2 — Backend: API REST

| Campo              | Valore                          |
| ------------------ | ------------------------------- |
| **Data inizio**    | 2026-06-16                      |
| **Data fine**      | 2026-07-02                      |
| **Stato**          | ✅ Completato                    |

**User stories implementate:**
- US-01 — `GET /api/v1/cinema` (lista cinema) + `GET /api/v1/cinema/{slug}` (dettaglio con count spettacoli)
- US-02 — `GET /api/v1/showings?date=YYYY-MM-DD` (spettacoli per data, denormalizzato con film + cinema)
- US-04 — `GET /api/v1/film/oggi` e `GET /api/v1/film/settimana` (filtri di data)
- US-07 — `buy_url` incluso in ogni Showing (link diretto acquisto)
- US-08 — Seed idempotente dai JSON scraper (`python -m app.seed_from_json` + endpoint admin `POST /api/v1/admin/reimport`)
- US-10 — `GET /api/v1/film/search?q=...` (ricerca case-insensitive, ignora accenti)

**Motivazione della scelta:**
Il backend è il collante tra scraper e app mobile. Implementato prima di Sprint 3 (app) per permettere ad Andrea di lavorare con dati reali dal giorno 1.

**Dipendenze:**
- Sprint 1 completato ✅

**Architettura implementata**:
```
routers/ → services/ → repositories/ → models/
                    ↘ schemas/ (Pydantic DTO)
```
- Stack: FastAPI + SQLAlchemy 2.0 sync + SQLite + Pydantic v2
- 11 endpoint funzionanti (Swagger auto su `/docs`)
- 26 test verdi (unit su repositories + end-to-end su TestClient)
- Seed dai JSON scraper con parsing `duration: "109 min"` → `runtime_minutes: 109`
- Sicurezza config: `admin_token` auto-generato se non in `.env` (no default insicuro)
- Nuovo doc: [`docs/backend/api.md`](../backend/api.md) per il team frontend

---

## Sprint 3 — App: prima schermata e integrazione backend

| Campo              | Valore                          |
| ------------------ | ------------------------------- |
| **Data inizio**    | 2026-07-03                      |
| **Data fine**      | 2026-07-07                      |
| **Stato**          | 🔴 Non iniziato (backend pronto, si può partire) |

**User stories implementate:**
- US-02 — App mostra la programmazione del giorno corrente (Home screen "Film oggi")
- US-04 — Filtro per data: oggi / domani / questa settimana
- US-07 — Link diretto al sito del cinema per acquisto biglietti

**Motivazione della scelta:**
La Home screen con "cosa danno stasera" è il core value dell'app — è la funzionalità che risolve il problema principale dell'utente. Implementata prima della mappa (più complessa) per consegnare valore immediatamente verificabile.

**Dipendenze:**
- Sprint 2 completato (endpoint `/spettacoli` e `/cinema` funzionanti)

---

## Sprint 4 — App: lista cinema e mappa interattiva

| Campo              | Valore                          |
| ------------------ | ------------------------------- |
| **Data inizio**    | 2026-07-08                      |
| **Data fine**      | 2026-07-14                      |
| **Stato**          | 🔴 Non iniziato                 |

**User stories implementate:**
- US-01 — Lista cinema con nome, indirizzo, link al sito
- US-03 — Mappa interattiva con marker cliccabili
- US-05 — Filtro per comune / zona geografica
- US-06 — Scheda dettaglio film (poster, sinossi, genere, durata)

**Motivazione della scelta:**
La mappa è il secondo pilastro dell'esperienza utente (RF-03 priorità "massima" dalla matrice). Separata dallo Sprint 3 perché richiede l'integrazione di `react-native-maps` e la gestione delle coordinate dei cinema — una dipendenza tecnica aggiuntiva rispetto alla sola lista.

**Dipendenze:**
- Sprint 3 completato (navigazione tab e connessione al backend funzionante)
- Coordinate cinema verificate (già presenti in `scraper/output/cinemas.json`)

---

## Sprint 5 — Deploy, ricerca e rifinitura

| Campo              | Valore                                   |
| ------------------ | ---------------------------------------- |
| **Data inizio**    | post 2026-07-14 (dopo esposizione)       |
| **Data fine**      | TBD                                      |
| **Stato**          | 🔴 Ipotetico — non critico per MVP       |

**User stories implementate:**
- US-09 — Ricerca film per titolo
- US-10 — Avviso visivo quando i dati di un cinema non sono aggiornati da oltre 48h
- Deploy backend su Railway (o Render), web build su Cloudflare Pages

**Motivazione della scelta:**
Ricerca e avviso dati obsoleti hanno priorità "media" e "bassa" nella matrice importanza-difficoltà: vengono lasciati all'ultimo sprint per non bloccare il rilascio del MVP. Il deploy viene fatto in questo sprint perché richiede il sistema completo.

**Dipendenze:**
- Sprint 4 completato (app funzionante end-to-end)

---

# PARTE 2 — Piano dei Rilasci

## Release 0.1 — Alpha (fine Sprint 2 · 2026-07-02) ✅ rilasciata

**Funzionalità presenti:**
- API REST funzionante: `/api/v1/cinema`, `/api/v1/showings`, `/api/v1/film/{id}`
- Database popolato dallo scraper (3 cinema, dati aggiornati ogni 24h)
- Documentazione Swagger auto-generata (`/docs`)

**Chi può usare il sistema:**
Solo il team di sviluppo — nessuna interfaccia utente disponibile. Verifica tramite Swagger UI e client HTTP (curl, Postman).

**Funzionalità rimandate:**
- App mobile (US-01 … US-07 lato frontend)
- Mappa interattiva (US-03)
- Ricerca per titolo (US-09)
- Avviso dati obsoleti (US-10)

---

## Release 0.5 — Beta (fine Sprint 3 · 2026-07-07)

**Funzionalità presenti:**
- App mobile (iOS + Android + web) con Home screen "Film oggi"
- Lista film in programmazione con orari, cinema, durata, genere
- Filtro per data (oggi / domani / settimana)
- Link diretto al sito del cinema per acquisto biglietti

**Chi può usare il sistema:**
Beta tester interni (team RepCode) — distribuzione tramite Expo Go o build TestFlight/internal track.

**Funzionalità rimandate:**
- Lista cinema e mappa (US-01, US-03, US-05)
- Scheda dettaglio film (US-06)
- Ricerca per titolo (US-09)
- Avviso dati obsoleti (US-10)

---

## Release 1.0 — MVP (fine Sprint 4 · 2026-07-14, giorno dell'esposizione)

**Funzionalità presenti:**
- Tutte le funzionalità della Release 0.5
- Lista cinema con nome, indirizzo, link al sito (US-01)
- Mappa interattiva con marker cliccabili (US-03)
- Filtro per zona/comune (US-05)
- Scheda dettaglio film con poster, sinossi, durata (US-06)

**Chi può usare il sistema:**
Tutti gli utenti — app disponibile su iOS, Android e web. Distribuzione tramite Expo EAS Build + Cloudflare Pages (web).

**Funzionalità rimandate:**
- Ricerca per titolo (US-09) — Release 1.1
- Avviso dati non aggiornati (US-10) — Release 1.1

---

## Release 1.1 (fine Sprint 5 · data TBD, post-esposizione)

**Funzionalità presenti:**
- Tutte le funzionalità della Release 1.0
- Ricerca film per titolo (US-09)
- Avviso visivo quando i dati di un cinema sono obsoleti da oltre 48h (US-10)
- Sistema in produzione su cloud (Railway + Cloudflare Pages)

**Chi può usare il sistema:**
Tutti gli utenti — sistema completo, stabile e deployato.

**Funzionalità rimandate:**
Nessuna — tutte le US del documento di analisi sono coperte.
