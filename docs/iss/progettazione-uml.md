---
aliases:
  - CinePosto — Progettazione UML e Design Pattern
linter-yaml-title-alias: CinePosto — Progettazione UML e Design Pattern
---

# CinePosto — Progettazione UML e Design Pattern

| **Progetto**   | CinePosto                                                          |
| -------------- | ------------------------------------------------------------------ |
| **Team**       | RepCode                                                            |
| **Componenti** | Emanuele Ceccariglia, Elio Casciola, Andrea Cestelli, Yonas Burka  |
| **Corso**      | Ingegneria del Software — ITS Umbria Academy, a.a. 2025/2026       |

Modelli UML del sistema, derivati dai requisiti ([analisi-requisiti](analisi-requisiti.md)) e dal codice implementato. Riferimenti: Sommerville cap. 5 (modellazione), cap. 6 (architettura).

---

## 1. Use case diagram

Attori: **Utente** (nessuna registrazione richiesta, RNF-03) e **Amministratore** (team, via token). Lo **Scheduler systemd** è un attore di sistema che avvia lo scraping senza intervento umano.

```mermaid
flowchart LR
    U["🧑 Utente"]
    A["🔑 Amministratore"]
    S["⏰ Scheduler systemd"]

    subgraph SISTEMA["Sistema CinePosto"]
        UC1(["Consulta lista cinema<br>RF-01"])
        UC2(["Consulta programmazione<br>RF-02"])
        UC3(["Visualizza cinema su mappa<br>RF-03"])
        UC4(["Filtra per data<br>RF-04"])
        UC6(["Consulta scheda film<br>RF-06"])
        UC7(["Apre sito cinema per acquisto<br>RF-07"])
        UC10(["Cerca film per titolo<br>RF-10"])
        UC8(["Aggiorna dati via scraping<br>RF-08, RF-09"])
        UC11(["Reimporta JSON nel DB<br>admin/reimport"])
    end

    U --> UC1 & UC2 & UC3 & UC4 & UC6 & UC7 & UC10
    A --> UC11
    S --> UC8
    UC8 -.->|produce JSON per| UC11

    classDef components fill:#F3E5F5,stroke:#BA68C8,color:#8E24AA
    classDef process fill:#E0F2F1,stroke:#4DB6AC,color:#00897B
    class UC1,UC2,UC3,UC4,UC6,UC7,UC10 components
    class UC8,UC11 process
```

RF-05 (filtro zona) e RF-11 (avviso dati obsoleti) sono rimandati a Release 1.1 — vedi [sprint-plan](sprint-plan.md).

## 2. Class diagram — modello di dominio backend

Le tre entità SQLAlchemy in `backend/app/models/`. `Showing` è la classe associativa tra `Film` e `Cinema`, con gli orari del giorno serializzati in `times`.

```mermaid
classDiagram
    class Cinema {
        +str slug PK
        +str name
        +str city
        +str address
        +str region
        +float lat
        +float lon
        +str website
        +str phone
    }

    class Film {
        +int id PK
        +str title
        +str title_normalized
        +str original_title
        +int year
        +int runtime_minutes
        +str genres
        +str director
        +str poster_url
        +str synopsis
        +str wikidata_id
        +datetime created_at
    }

    class Showing {
        +int id PK
        +int film_id FK
        +str cinema_slug FK
        +date date
        +str times
        +str language
        +str screen
        +str buy_url
        +datetime scraped_at
    }

    Film "1" --> "0..*" Showing : showings
    Cinema "1" --> "0..*" Showing : showings
```

Vincoli di unicità (dedup): `Film` → `UNIQUE su title_normalized + year`; `Showing` → `UNIQUE su film_id + cinema_slug + date`. Motivazione della PK artificiale di Film in [schema-mapping](../backend/schema-mapping.md).

## 3. Diagramma ER — schema database

```mermaid
erDiagram
    CINEMAS ||--o{ SHOWINGS : "ospita"
    FILMS ||--o{ SHOWINGS : "proiettato in"

    CINEMAS {
        TEXT slug PK
        TEXT name
        TEXT city
        TEXT address
        REAL lat
        REAL lon
    }
    FILMS {
        INTEGER id PK
        TEXT title
        TEXT title_normalized UK
        INTEGER year UK
        TEXT wikidata_id UK
    }
    SHOWINGS {
        INTEGER id PK
        INTEGER film_id FK
        TEXT cinema_slug FK
        DATE date
        TEXT times
        TEXT buy_url
    }
```

DB: SQLite anche in produzione — decisione D4. Le FK sono attivate esplicitamente con `PRAGMA foreign_keys=ON` a ogni connessione, perché SQLite di default le ignora.

## 4. Sequence diagram — caso d'uso "Film oggi"

Flusso completo della schermata Home attraverso i layer del backend.

```mermaid
sequenceDiagram
    actor Utente
    participant App as App React Native
    participant R as Router film.py
    participant Sv as film_service
    participant Rp as film_repo
    participant DB as SQLite

    Utente->>App: apre la Home
    App->>R: GET /api/v1/film/oggi
    R->>Sv: get_films_today
    Sv->>Rp: list_in_programming con oggi-oggi
    Rp->>DB: SELECT film JOIN showings WHERE date = oggi
    DB-->>Rp: righe film
    Rp-->>Sv: list di Film ORM
    Sv-->>R: list di Film ORM
    R-->>App: JSON list di FilmOut
    App-->>Utente: card dei film in programmazione
```

## 5. Deployment diagram

```mermaid
flowchart TB
    subgraph VM["🖥️ VM Linux Ubuntu"]
        TIMER["systemd timer<br>daily 03:00"]
        SCRAPER["cineposto-scraper<br>Python 3.12 venv"]
        JSON[("output JSON<br>cinemas, films, showings")]
        API["backend FastAPI<br>uvicorn :8000"]
        DB[("SQLite<br>cineposto.db")]
        TIMER --> SCRAPER --> JSON
        JSON -->|seed / reimport| API
        API --- DB
    end

    WD["🌐 Wikidata SPARQL"]
    SITI["🌐 Siti dei 3 cinema"]
    SCRAPER --> WD
    SCRAPER --> SITI

    subgraph CLIENT["Dispositivi utente"]
        MOBILE["📱 App Expo<br>iOS + Android"]
        WEB["💻 Web build<br>Cloudflare Pages"]
    end
    MOBILE -->|HTTPS REST| API
    WEB -->|HTTPS REST| API

    classDef process fill:#E0F2F1,stroke:#4DB6AC,color:#00897B
    classDef storage fill:#F1F8E9,stroke:#9CCC65,color:#689F38
    classDef api fill:#FFF9C4,stroke:#FDD835,color:#F9A825
    classDef components fill:#F3E5F5,stroke:#BA68C8,color:#8E24AA
    class TIMER,SCRAPER process
    class JSON,DB storage
    class API,WD,SITI api
    class MOBILE,WEB components
```

## 6. Design pattern adottati

Pattern effettivamente presenti nel codice, con posizione.

| Pattern | Dove | Perché |
|---|---|---|
| **Layered architecture** — Sommerville §6.3 | `routers/ → services/ → repositories/ → models/` | Ogni layer ha una responsabilità sola; si testa e si sostituisce in isolamento |
| **Repository** — Fowler PoEAA | `backend/app/repositories/` | Le query SQL vivono in un punto solo; i service non conoscono SQLAlchemy |
| **Service layer** — Fowler PoEAA | `backend/app/services/` | Logica di business separata da HTTP e da persistenza |
| **DTO** | `backend/app/schemas/` — Pydantic | Il contratto API è esplicito e disaccoppiato dal modello DB |
| **Dependency Injection** | `Depends(get_db)` nei router | La session DB è iniettata: nei test si sostituisce con il DB in-memory |
| **Factory** | `create_app()` in `main.py` | L'app FastAPI è costruita da una funzione: configurabile e testabile |
| **Strategy** — GoF | `scraper/connectors/base.py` ABC + 3 connettori concreti | Ogni cinema è una strategia intercambiabile con la stessa interfaccia `scrape`; aggiungere un cinema = aggiungere un file |
| **Upsert idempotente** | `seed_from_json.py` + repository `upsert` | Il seed può girare N volte con lo stesso risultato: nessun duplicato |
