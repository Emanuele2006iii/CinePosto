# Documentazione CinePosto

Aggregatore cinema Umbria — scraper Python + backend FastAPI + app React Native.

> 📂 **Tutta la documentazione vive qui** (`cineposto/docs/`). Nelle cartelle dei singoli componenti (`scraper/`, `backend/`, `app/`) c'è solo il `README.md` "front door"; il dettaglio è qui.

---

## 🎯 Documenti chiave — leggi prima questi

| Documento | Quando aprirlo |
|-----------|----------------|
| [**PIANO-CONSEGNA-14LUGLIO.md**](PIANO-CONSEGNA-14LUGLIO.md) | **Roadmap operativa giorno per giorno** fino alla presentazione. Decisioni L1-L5, scope MVP, sprint, task con DoD, rischi, fallback. |
| [CONTINUAZIONE-PROGETTUALE.md](CONTINUAZIONE-PROGETTUALE.md) | Audit completo dello stato (2026-06-30) e decisioni di design D1-D5. Documento di riferimento storico. |
| [backend/schema-mapping.md](backend/schema-mapping.md) | **Tabella autorevole** per il seed: come ogni campo dei JSON scraper diventa una colonna del DB. |

---

## 📦 Documentazione per componente

### Scraper
| Documento | Descrizione |
|-----------|-------------|
| [`../scraper/README.md`](../scraper/README.md) | Front door scraper: installazione, avvio, output JSON, deploy systemd timer |
| [scraper/architecture.md](scraper/architecture.md) | Architettura tecnica: connettori, modello dati, flusso, Wikidata, delta, systemd |

### Backend
| Documento | Descrizione |
|-----------|-------------|
| [`../backend/README.md`](../backend/README.md) | Front door backend: architettura layered, setup, endpoint, status |
| [backend/architecture.md](backend/architecture.md) | Modelli SQLAlchemy (Cinema/Film/Showing), endpoint REST, decisioni L1-L5 |
| [backend/schema-mapping.md](backend/schema-mapping.md) | Mapping JSON scraper → DB, strategia seed, esempi end-to-end |

### App (React Native + Expo)
| Documento | Descrizione |
|-----------|-------------|
| [`../app/README.md`](../app/README.md) | Front door Expo (boilerplate) |
| [app/overview.md](app/overview.md) | Stack, struttura, comandi Expo, integrazione backend |

### Worker (Cloudflare Pages)
Hosting web build React Native — nessuna logica aggiuntiva. Vedi `../worker/` direttamente.

---

## 📋 ISS — Ingegneria del Software

Documenti formali del corso ITS Umbria Academy a.a. 2025/2026 (team RepCode).

| Documento | Descrizione |
|-----------|-------------|
| [iss/analisi-requisiti.md](iss/analisi-requisiti.md) | RF, RNF, stakeholder, matrice importanza-difficoltà, risk assessment |
| [iss/sprint-plan.md](iss/sprint-plan.md) | 5 sprint, user stories, date, piano rilasci Alpha→1.0→1.1 |

---

## 🛠️ Sviluppo

| Documento | Descrizione |
|-----------|-------------|
| [development.md](development.md) | Testing, lint, variabili d'ambiente, setup locale per ogni componente |
| [`../README.md`](../README.md) | Monorepo overview: struttura, stato componenti, roadmap |

---

## 📂 Struttura completa `cineposto/docs/`

```
cineposto/docs/
├── index.md                          ← questo file (hub)
├── PIANO-CONSEGNA-14LUGLIO.md        ← roadmap T-14 con sprint
├── CONTINUAZIONE-PROGETTUALE.md      ← audit + decisioni D1-D5
├── development.md                    ← testing, lint, setup dev
├── scraper/
│   └── architecture.md               ← architettura tecnica scraper
├── backend/
│   ├── architecture.md               ← modello dati, API, decisioni
│   └── schema-mapping.md             ← mapping JSON → DB (per seed)
├── app/
│   └── overview.md                   ← React Native overview
└── iss/
    ├── analisi-requisiti.md          ← documento formale ISS
    └── sprint-plan.md                ← documento formale ISS
```

### Regola d'oro

- **Documentazione tecnica** → sempre in `docs/`
- **`README.md` nei componenti** → solo front-door (link e quickstart)
- **Niente `<componente>/docs/`** sparso: tutto in `cineposto/docs/<componente>/`
