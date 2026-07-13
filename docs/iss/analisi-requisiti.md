---
aliases:
  - CinePosto — Analisi dei Requisiti e Risk Assessment
linter-yaml-title-alias: CinePosto — Analisi dei Requisiti e Risk Assessment
---

# CinePosto — Analisi dei Requisiti e Risk Assessment

| **Progetto**   | CinePosto                                                         |
| -------------- | ----------------------------------------------------------------- |
| **Team**       | RepCode                                                           |
| **Componenti** | Emanuele Ceccariglia, Elio Casciola, Andrea Cestelli, Yonas Burka |
| **Corso**      | Ingegneria del Software — ITS Umbria Academy, a.a. 2025/2026      |

---

# PARTE 1 — ANALISI DEI REQUISITI

## NOME SOFTWARE:

**CinePosto**

---

## DESCRIZIONE DI ALTO LIVELLO

CinePosto è un'applicazione mobile nativa (React Native / Expo) con backend Python che aggrega in un'unica interfaccia la programmazione di tutti i cinema dell'Umbria. Il sistema consente agli utenti di consultare film in programmazione, orari, sale e posizione geografica dei cinema tramite mappa interattiva, senza necessità di registrazione.

Il sistema si compone di due parti distinte: un **client mobile** (iOS e Android) per la consultazione da parte dell'utente finale, e un **backend** che raccoglie automaticamente i dati dai siti dei cinema tramite web scraping schedulato e li espone tramite API REST. I dati sui film (poster, sinossi, genere, durata) vengono arricchiti tramite API esterna.

**Scope:**
- **Incluso**: lista cinema umbri, programmazione con orari, mappa interattiva con marker, filtro per data/zona/film, scheda dettaglio film, link al sito originale per acquisto biglietti, aggiornamento automatico dati (scraping giornaliero).
- **Escluso**: acquisto biglietti in-app, recensioni utenti, account personali, notifiche push, cinema al di fuori dell'Umbria (MVP), contenuti video/trailer.

---

## STAKEHOLDER

| Stakeholder | Ruolo | Interesse |
|-------------|-------|-----------|
| **Utente residente** | Utente finale principale | Trovare velocemente film e orari nei cinema della propria zona senza consultare siti multipli |
| **Turista** | Utente occasionale | Scoprire cinema e programmazione della zona durante il soggiorno in Umbria |
| **Gestore cinema** | Fonte dati indiretta | Avere visibilità aggiuntiva sulla propria programmazione; link diretto per l'acquisto biglietti |
| **Team di sviluppo** | Sviluppatore / manutentore | Mantenere il sistema funzionante, aggiornare gli scraper al variare dei siti fonte |

---

## REQUISITI FUNZIONALI

| ID    | Requisito                                                                                                                                 | Priorità |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| RF-01 | Il sistema deve visualizzare la lista di tutti i cinema umbri attivi con nome, città, indirizzo e link al sito ufficiale                  | Alta     |
| RF-02 | Il sistema deve visualizzare la programmazione di ciascun cinema: lista film, orari e giorni disponibili                                  | Alta     |
| RF-03 | Il sistema deve mostrare i cinema su mappa interattiva con marker cliccabili che aprono il dettaglio del cinema                           | Alta     |
| RF-04 | Il sistema deve consentire di filtrare la programmazione per data (oggi, domani, questa settimana)                                        | Alta     |
| RF-05 | Il sistema deve consentire di filtrare cinema e spettacoli per comune o zona geografica                                                   | Media    |
| RF-06 | Il sistema deve mostrare la scheda dettaglio di un film: titolo, genere, durata, poster, sinossi breve                                    | Media    |
| RF-07 | Il sistema deve fornire un link diretto al sito del cinema per l'acquisto dei biglietti                                                   | Alta     |
| RF-08 | Il backend deve aggiornare automaticamente i dati di programmazione tramite scraping schedulato (frequenza: almeno una volta ogni 24 ore) | Alta     |
| RF-09 | Il sistema deve rispettare il file robots.txt di ogni fonte scrapata e non accedere a pagine protette da autenticazione                   | Alta     |
| RF-10 | Il sistema deve consentire la ricerca per titolo                                                                                          | Media    |
| RF-11 | Il sistema deve segnalare all'utente quando i dati di un cinema non sono aggiornati da più di 48 ore                                      | Bassa    |

---

## REQUISITI NON FUNZIONALI

| ID | Categoria | Requisito |
|----|-----------|-----------|
| RNF-01 | **Portabilità** | L'app deve funzionare su iOS 16+ e Android 10+ tramite un unico codebase React Native/Expo |
| RNF-02 | **Aggiornamento dati** | I dati di programmazione devono essere aggiornati entro 24h dalla variazione sulla fonte originale |
| RNF-03 | **Privacy** | L'app non raccoglie dati personali degli utenti; nessun account, nessun tracciamento |
| RNF-04 | **Compliance scraping** | Il backend rispetta robots.txt, applica rate limiting (max 1 req/s per dominio) e opera in orario notturno per ridurre il carico sui server delle fonti |
| RNF-05 | **Performance** | Le schermate principali (lista cinema, mappa) devono caricarsi in meno di 2 secondi con connessione 4G |
| RNF-06 | **Disponibilità** | Il backend deve avere disponibilità minima del 95% nelle fasce 10:00–23:00 |
| RNF-07 | **Scalabilità** | L'architettura deve consentire l'estensione ad altre regioni italiane senza modifiche strutturali al codice |

---

## MATRICE IMPORTANZA-DIFFICOLTÀ

> Asse X: POCO / MOLTO IMPORTANTE — Asse Y: FACILE / DIFFICILE

| Requisito                        | Importanza       | Difficoltà | Decisione                  |
| -------------------------------- | ---------------- | ---------- | -------------------------- |
| RF-01 Lista cinema               | MOLTO IMPORTANTE | FACILE     | **Priorità massima**       |
| RF-02 Programmazione cinema      | MOLTO IMPORTANTE | MEDIA      | **Priorità massima**       |
| RF-03 Mappa interattiva          | MOLTO IMPORTANTE | MEDIA      | **Priorità massima**       |
| RF-07 Link acquisto biglietti    | MOLTO IMPORTANTE | FACILE     | **Priorità massima**       |
| RF-08 Scraping schedulato        | MOLTO IMPORTANTE | DIFFICILE  | **Pianificazione critica** |
| RF-04 Filtro per data            | MOLTO IMPORTANTE | FACILE     | **Priorità massima**       |
| RF-06 Scheda dettaglio film      | MOLTO IMPORTANTE | MEDIA      | **Pianificazione critica** |
| RF-09 Compliance robots.txt      | MOLTO IMPORTANTE | FACILE     | **Priorità massima**       |
| RF-05 Filtro per zona            | MEDIA IMPORTANZA | FACILE     | **Da valutare**            |
| RF-10 Ricerca per titolo         | MEDIA IMPORTANZA | FACILE     | Da valutare                |
| RF-11 Avviso dati non aggiornati | POCO IMPORTANTE  | FACILE     | **Rilascio successivo**    |

---

# PARTE 2 — RISK ASSESSMENT

| # | TITOLO | LIVELLO SEVERITÀ | ASSET COINVOLTO | IMPATTO | PROBABILITÀ | AZIONE |
|---|--------|-----------------|-----------------|---------|-------------|--------|
| R-01 | Cambiamento struttura HTML dei siti cinema (scraper si rompe) | ALTO | Modulo scraping | Dati non aggiornati, programmazione obsoleta | ALTA | Architettura scraper modulare (un file per cinema); alerting automatico in caso di scraping fallito; revisione manuale periodica |
| R-02 | Cinema con robots.txt che vieta il crawling | MEDIO | Modulo scraping | Cinema non copribile, gap nella copertura regionale | MEDIA | Verificare robots.txt prima di ogni nuovo scraper; per i cinema bloccati, contattare il gestore per accordo diretto |
| R-03 | Siti cinema con rendering JavaScript (SPA) non scrapabili con BeautifulSoup | ALTO | Modulo scraping | Cinema non scrapabili con stack base | MEDIA | Integrare Playwright come fallback per siti JS-rendered; prioritizzare cinema con HTML statico nel MVP |
| R-04 | Dati Wikidata non disponibili per film italiani di nicchia | BASSO | Modulo arricchimento dati film | Scheda film incompleta (solo titolo e orari) | MEDIA | Gestire gracefully l'assenza dei dati di arricchimento; mostrare dati disponibili senza bloccare la visualizzazione |
| R-05 | Scope creep: aggiunta di funzionalità non pianificate (account, recensioni, notifiche) | MEDIO | Pianificazione e tempistiche | Ritardi nel rilascio dell'MVP | ALTA | Questo documento costituisce il riferimento di scope per l'MVP. Funzionalità extra vanno in backlog per versioni successive |
| R-06 | Piano gratuito cloud insufficiente per volume richieste | BASSO | Deploy backend | Downtime o rallentamenti nelle ore serali | BASSA | Monitorare i limiti del piano free (Railway/Render); implementare caching aggressivo lato API per ridurre le query al DB |
| R-07 | Diffida legale da parte di un cinema per scraping non autorizzato | MEDIO | Operatività del progetto | Rimozione del cinema dalla copertura | BASSA | Rispettare robots.txt e rate limiting; includere attribuzione e link al sito originale; app gratuita esclude parassitismo commerciale |
