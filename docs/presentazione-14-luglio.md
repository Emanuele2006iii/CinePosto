# Esposizione del 14 luglio — guida

Materiale di preparazione per l'esposizione di Ingegneria del Software (prof. Montecchiani, ITS Umbria Academy). Team RepCode: Emanuele, Elio, Andrea, Yonas. Prima di leggerla conviene aver letto [panoramica.md](panoramica.md).

In ordine: la scaletta dei 15 minuti, come preparare la demo la mattina, lo script di cosa mostrare, il piano B se la rete fa i capricci, le domande probabili del prof con le risposte e la checklist finale.

## 1. Scaletta (15 minuti, 4 persone)

| # | Blocco | Tempo | Contenuto | Appoggio |
|---|---|---|---|---|
| 1 | Problema e soluzione | 2' | "Per sapere cosa danno stasera a Perugia devi aprire tre siti diversi" → poi CinePosto | [iss/analisi-requisiti.md](iss/analisi-requisiti.md) |
| 2 | Processo | 3' | Requisiti → matrice importanza-difficoltà → risk assessment → cinque sprint Scrum con release incrementali | [iss/analisi-requisiti.md](iss/analisi-requisiti.md), [iss/sprint-plan.md](iss/sprint-plan.md) |
| 3 | Architettura | 4' | Pipeline a tre stadi (deployment diagram), backend a layer, modello dati (class diagram + ER) | [iss/progettazione-uml.md](iss/progettazione-uml.md) |
| 4 | Demo dal vivo | 4' | Lo script della sezione 3 | — |
| 5 | Qualità e chiusura | 2' | 101 test, CI, decisioni di design difese (SQLite, Wikidata), cosa faremmo dopo (Release 1.1) | [panoramica.md](panoramica.md) §6-7 |

Chi dice cosa: decidetelo in base a chi ha scritto cosa — chi ha fatto un componente risponde alle domande su quel componente.

## 2. Preparazione (la mattina del 14, ~10 minuti)

I cinema pubblicano il palinsesto pochi giorni prima, quindi conviene ri-scrapare la mattina stessa per avere dati del giorno.

1. Dati freschi:
   ```bash
   cd cineposto/scraper && .venv/bin/python -m scraper.main --once
   cd ../backend && venv/bin/python -c "from app.database import Base, engine; import app.models; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
   venv/bin/python -m app.seed_from_json
   ```
2. Avvia il backend e lascialo aperto in un terminale:
   ```bash
   cd cineposto/backend && source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. IP LAN del Mac: `ipconfig getifaddr en0`.
4. Avvia l'app in un altro terminale:
   ```bash
   cd cineposto/app
   EXPO_PUBLIC_API_BASE="http://<IP-LAN>:8000/api/v1" npx expo start
   ```
5. Apri `http://localhost:8081` nel browser del Mac (la pagina già pronta sul proiettore).
6. Sul telefono: Expo Go già connesso alla stessa Wi-Fi, pronto in mano.
7. Salvagente: fai quattro o cinque screenshot e una breve registrazione schermo dell'app che funziona (Home, dettaglio con orari, ricerca, mappa). Se la rete muore del tutto, mostri quelli.

Controllo prima di iniziare: `curl http://localhost:8000/api/v1/film/oggi` deve restituire dei film. Se sì, sei pronto.

Regola: la demo principale falla **sul web del Mac** collegato al proiettore — è la più affidabile, niente QR e niente pairing, la rete la controlli tu. Il telefono lo mostri alla fine, come "gira identico anche su smartphone".

## 3. Script della demo

**Apertura (20")** — Home già aperta, con logo e carosello:
> "CinePosto è un aggregatore dei cinema dell'Umbria: in un'unica app trovi i film in programmazione, gli orari e i cinema. I dati non li inseriamo a mano, li raccoglie automaticamente uno scraper che legge i siti dei tre cinema."

**Home, tab Film (1')**
- Carosello: scorri tra i film in evidenza — "in cima i film del giorno".
- Barra date: tocca un giorno diverso — "si vedono i prossimi giorni, il cartellone si aggiorna".
- Griglia locandine: scorri — "tutti i film in sala in quella data".
- Filtro cinema (icona in alto): scegli un cinema, poi togli il filtro — "si può filtrare per singolo cinema".

**Dettaglio film (1') — il pezzo forte**
- Tocca un film con tanti orari (es. Odissea, o un titolo grosso).
- Mostra poster, trama ("leggi di più") e bottone trailer.
- Orari raggruppati per cinema — "questi sono gli orari veri, raccolti dai cinema e raggruppati per sala nella data scelta".
- Tocca un orario — "porta al sito del cinema per l'acquisto" (puoi non aprirlo davvero).
- Frase da effetto: *"All'inizio qui compariva un solo orario: avevamo scoperto che il database, per il vincolo di unicità, ne teneva uno solo. Ora uniamo tutte le sale — Odissea è passata da 1 a 12 orari."* Fa vedere che sapete diagnosticare e correggere.

**Cerca (30")**
- Tab Cerca, digita un titolo (es. `casa`) — "ricerca per titolo con debounce: aspetta che smetti di digitare prima di interrogare il backend".
- Tocca un risultato → si apre il dettaglio.

**Località, la mappa (40")**
- Tab Località: mappa con i tre marker e la lista con gli indirizzi — "toccando un cinema si apre in Google Maps".

**Multi-piattaforma (20")**
- Prendi il telefono e mostra la stessa schermata — "stessa app, stesso codice: React Native gira su web e su smartphone".

**Chiusura tecnica (30")**
> "Dietro: uno scraper Python con tre connettori produce JSON, un backend FastAPI su SQLite li serve via API REST con 26 test automatici, l'app React Native li consuma. È il flusso completo, end-to-end, su dato reale."

Se il tempo regge, mostra anche la pipeline dal vivo: `python -m scraper.main --once` in un terminale, poi `POST /admin/reimport` da Swagger col token e `GET /admin/dataset-info` per i conteggi aggiornati. Racconta l'idempotenza: "lo possiamo rilanciare cento volte, il DB resta corretto".

## 4. Piano B se la rete fa problemi

Cosa dipende da cosa:

| Componente | Serve internet? |
|---|---|
| App ↔ backend (titoli, orari, cinema) | No, è tutto in rete locale (Mac e telefono sulla stessa Wi-Fi) |
| Locandine dei film | Sì, le immagini stanno sui siti dei cinema |
| Mappa (tab Località) | Sì, Leaflet e le tile arrivano da un CDN |

Se manca la rete della scuola:
1. Attiva l'hotspot del telefono e collega il Mac: hai internet (poster e mappa) e la rete locale Mac↔telefono. È il salvagente numero uno.
2. Se l'hotspot non basta, fai la demo solo sul web del Mac: titoli e orari ci sono comunque (backend locale), le locandine potrebbero non caricarsi.
3. Se cade tutto, mostra gli screenshot e la registrazione preparati al punto 2.7 e racconta il flusso a voce.

Prova l'hotspot **prima** dell'esposizione, così sai già che funziona.

## 5. Domande probabili del prof

**Architettura e design**
- *Perché un'architettura a layer e non un monolite a script?* Ogni layer ha una responsabilità sola e si testa in isolamento: nei 26 test del backend i repository si provano senza HTTP e i router con un DB in-memory iniettato al posto di quello vero (dependency injection su `get_db`). È Sommerville §6.3 applicato.
- *Perché SQLite in produzione e non PostgreSQL?* Carico minimo: tre cinema, un paio di centinaia di spettacoli, sola lettura dall'app. Un DB server aggiungerebbe amministrazione senza benefici misurabili. Il layer repository isola la scelta: passare a PostgreSQL cambierebbe la stringa di connessione, non il codice sopra (D4).
- *Perché la PK di Film è un intero e quella di Cinema uno slug?* I cinema sono tre, stabili, con nomi univoci: lo slug è leggibile negli URL e nei log. I film sono centinaia e i titoli sono fragili (apostrofi tipografici, trattini, remake omonimi): meglio una PK artificiale più un vincolo UNIQUE su (titolo normalizzato, anno) (D3).
- *Che design pattern avete usato?* Tabella completa con file e motivazione in [iss/progettazione-uml.md](iss/progettazione-uml.md) §6: layered, Repository, Service layer, DTO, Dependency Injection, Factory, Strategy nei connettori.

**Dati e scraping**
- *Cosa succede se un cinema rifà il sito e lo scraper si rompe?* È il rischio numero uno del risk assessment (R-01). Mitigazioni: un connettore per cinema (si rompe solo quello), errori raccolti senza bloccare gli altri, delta tracking che tiene i dati vecchi marcandoli, 75 test che fissano il comportamento atteso di ogni parser.
- *Lo scraping è legale ed etico?* Requisito esplicito RF-09: rispetto di robots.txt, rate limiting, run notturna per non caricare i server, User-Agent con contatto reale, link diretto al sito del cinema per l'acquisto (portiamo traffico, non lo togliamo). App gratuita e didattica.
- *Perché Wikidata e non TMDB?* Nessuna API key, nessun limite commerciale, licenza aperta, query SPARQL con cache locale (D1).
- *Come evitate i duplicati se lo scraping gira ogni notte?* Upsert idempotente a ogni livello: vincoli UNIQUE sul DB più lookup applicativo prima di ogni insert. Re-importare gli stessi JSON non cambia niente.

**Processo**
- *Come avete diviso il lavoro?* Uno sprint per componente con dipendenze esplicite: prima lo scraper (valida la fattibilità, "i siti sono scrapabili?"), poi il backend (sblocca il frontend con dati reali), poi l'app. User story tracciate sui requisiti (US-xx → RF-xx).
- *Come testate?* 75 test scraper (parser con fixture HTML/JSON registrate) più 26 backend (unit sui repository ed end-to-end sugli endpoint con TestClient e DB in-memory). CI GitHub Actions a due job su ogni push.
- *Cosa NON avete fatto e perché?* Scope escluso dichiarato nell'analisi requisiti (account, acquisto in-app, notifiche), più funzionalità rimandate alla Release 1.1 (ricerca nell'app, avviso dati obsoleti). Scope congelato il 07/07: ultima settimana solo stabilizzazione.

**Limiti tecnici** (ammetterli fa punti)
- La UNIQUE su (titolo, anno) non protegge a livello DB quando l'anno è NULL: in SQL `NULL ≠ NULL`, quindi lì la dedup è garantita dal codice. Limite noto, documentato in [backend/schema-mapping.md](backend/schema-mapping.md).
- L'API di UCI non è documentata: può cambiare senza preavviso. È il motivo del design "un connettore per cinema".
- SQLite serializza le scritture: va bene perché scrive solo il seed notturno, mentre l'app legge.

## 6. Checklist pre-esposizione

- [ ] Scraper lanciato la mattina stessa, dati del giorno
- [ ] Backend su, seed fatto, Swagger raggiungibile
- [ ] App aperta sul web del Mac e collegata al backend; telefono con Expo Go pronto
- [ ] Screenshot e registrazione della demo pronti come riserva
- [ ] Hotspot del telefono provato in anticipo
- [ ] Diagrammi UML pronti da mostrare ([iss/progettazione-uml.md](iss/progettazione-uml.md))
- [ ] Ogni membro sa rispondere sulle parti degli altri almeno a livello di panoramica
