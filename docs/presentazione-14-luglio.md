# Guida all'esposizione — 14 luglio 2026

> Materiale di preparazione per l'esposizione ISS (prof. Montecchiani, ITS Umbria Academy). Team RepCode: Emanuele, Elio, Andrea, Yonas.
> Prerequisito: aver letto [panoramica.md](panoramica.md).

---

## 1. Scaletta suggerita (15 minuti, 4 persone)

| # | Blocco | Tempo | Contenuto | Documento di appoggio |
|---|---|---|---|---|
| 1 | Problema e soluzione | 2' | "Per sapere cosa danno stasera a Perugia devi aprire 3 siti diversi" → demo del problema, poi CinePosto | [iss/analisi-requisiti.md](iss/analisi-requisiti.md) §descrizione |
| 2 | Processo ISS | 3' | Requisiti → matrice importanza-difficoltà → risk assessment → 5 sprint Scrum con release incrementali | [iss/analisi-requisiti.md](iss/analisi-requisiti.md) + [iss/sprint-plan.md](iss/sprint-plan.md) |
| 3 | Architettura | 4' | Pipeline a 3 stadi (diagramma deployment), architettura layered del backend, modello dati (class diagram + ER) | [iss/progettazione-uml.md](iss/progettazione-uml.md) |
| 4 | Demo live | 4' | Vedi §2 sotto | — |
| 5 | Qualità e chiusura | 2' | 101 test, CI, decisioni di design difese (SQLite, Wikidata), cosa faremmo dopo (Release 1.1) | [panoramica.md](panoramica.md) §6-7 |

Chi dice cosa: decidetelo in base a chi ha fatto cosa — chi ha scritto un componente risponde alle domande su quel componente.

## 2. Demo live — flusso consigliato

Preparare **prima** (la mattina stessa): backend avviato, DB seedato con dati freschi, app su Expo Go, Swagger aperto in un tab.

1. **App**: Home "Film Oggi" → card di un film → orari → tap sul link acquisto (si apre il sito del cinema). Poi tab Cinema.
2. **Swagger** (`localhost:8000/docs`): `GET /film/oggi` → si vede il JSON che alimenta la schermata appena mostrata. Colpo d'occhio sugli 11 endpoint.
3. **La pipeline dal vivo** (se il tempo regge): `python -m scraper.main --once` in un terminale → alla fine, `POST /admin/reimport` da Swagger col token → `GET /admin/dataset-info` mostra i conteggi aggiornati. Racconta l'idempotenza: "possiamo rilanciarlo cento volte, il DB resta corretto".

**Piani B**: se la rete dell'aula è inaffidabile → scraper già lanciato a casa, mostrare i JSON in `scraper/output/` e fare solo reimport locale. Se Expo Go dà problemi → web build o screen-recording di riserva registrato il giorno prima.

## 3. Domande probabili del prof — con la risposta breve

**Architettura e design**

- *Perché un'architettura layered e non un monolite a script?* — Ogni layer ha una responsabilità sola e si testa in isolamento: nei 26 test del backend i repository si testano senza HTTP e i router si testano con un DB in-memory iniettato al posto di quello vero (dependency injection su `get_db`). È Sommerville §6.3 applicato.
- *Perché SQLite in produzione e non PostgreSQL?* — Carico: 3 cinema, ~250 spettacoli, sola lettura dall'app. Un DB server aggiungerebbe amministrazione senza benefici misurabili. Il layer repository isola la scelta: migrare a PostgreSQL cambierebbe la stringa di connessione, non il codice sopra. (Decisione D4, documentata.)
- *Perché la PK di Film è un intero ma quella di Cinema è uno slug?* — I cinema sono 3, stabili, con nomi univoci: lo slug è leggibile negli URL e nei log. I film sono centinaia e i titoli sono fragili (apostrofi tipografici, trattini, remake con lo stesso titolo): PK artificiale + vincolo UNIQUE su (titolo normalizzato, anno). (D3.)
- *Che design pattern avete usato?* — Tabella completa con file e motivazione in [iss/progettazione-uml.md](iss/progettazione-uml.md) §6: layered, Repository, Service layer, DTO, Dependency Injection, Factory, Strategy nei connettori.

**Dati e scraping**

- *Cosa succede se un cinema rifà il sito e lo scraper si rompe?* — È il rischio n.1 del nostro risk assessment (R-01). Mitigazioni: un connettore per cinema (si rompe solo quello), errori raccolti in `errors.json` senza bloccare gli altri, delta tracking che tiene i dati vecchi marcandoli, 75 test che fissano il comportamento atteso di ogni parser.
- *Lo scraping è legale/etico?* — Requisito esplicito RF-09: rispetto di robots.txt, rate limiting, run notturna per non caricare i server, User-Agent con contatto reale, link diretto al sito del cinema per l'acquisto (portiamo traffico, non lo togliamo). App gratuita e didattica.
- *Perché Wikidata e non TMDB?* — Nessuna API key, nessun limite commerciale, licenza aperta, query SPARQL con cache locale. (D1.)
- *Come evitate i duplicati se lo scraping gira ogni notte?* — Upsert idempotente a ogni livello: vincoli UNIQUE sul DB + lookup applicativo prima di ogni insert. Re-importare gli stessi JSON non cambia nulla.

**Processo**

- *Come avete diviso il lavoro?* — Sprint per componente con dipendenze esplicite: prima lo scraper (valida la fattibilità: "i siti sono scrapabili?"), poi il backend (sblocca il frontend con dati reali), poi l'app. User story tracciate sui requisiti (US-xx → RF-xx).
- *Come testate?* — 75 test scraper (parser con HTML/JSON fixture registrate) + 26 backend (unit sui repository + end-to-end sugli endpoint con TestClient e DB in-memory). CI GitHub Actions a 2 job su ogni push.
- *Cosa NON avete fatto e perché?* — Scope escluso dichiarato nell'analisi requisiti (account, acquisto in-app, notifiche) + funzionalità rimandate a Release 1.1 (ricerca nell'app, avviso dati obsoleti). Scope congelato il 07/07 (L5): ultima settimana solo stabilizzazione.

**Onestà tecnica** (se chiede i limiti — ammetterli fa punti)

- La UNIQUE su (titolo, anno) non protegge a livello DB quando l'anno è NULL (in SQL `NULL ≠ NULL`): la dedup lì è garantita dal codice. Limite noto, documentato in [backend/schema-mapping.md](backend/schema-mapping.md).
- L'API UCI non è documentata: può cambiare senza preavviso. È il motivo del design "un connettore per cinema".
- SQLite serializza le scritture: va bene perché scrive solo il seed notturno, mentre l'app legge.

## 4. Checklist pre-esposizione

- [ ] Scraper lanciato la mattina stessa → dati del giorno
- [ ] Backend su, seed fatto, Swagger raggiungibile
- [ ] App su Expo Go collegata al backend (Sprint 3 completato) — altrimenti demo su web build
- [ ] Video di riserva della demo registrato
- [ ] Diagrammi UML pronti da mostrare ([iss/progettazione-uml.md](iss/progettazione-uml.md))
- [ ] Ogni membro sa rispondere sulle parti degli altri almeno a livello di panoramica
