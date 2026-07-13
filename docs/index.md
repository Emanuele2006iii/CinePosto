# Documentazione CinePosto

Aggregatore cinema Umbria — scraper Python + backend FastAPI + app React Native.

> 📂 **Tutta la documentazione vive qui** (`cineposto/docs/`), organizzata per aree. Nelle cartelle dei componenti c'è solo il `README.md` "front door".

---

## 🎯 Da dove partire

| Documento | A cosa serve |
|-----------|--------------|
| [**panoramica.md**](panoramica.md) | **Il sistema spiegato da cima a fondo** — flusso dati, componenti, decisioni. Da leggere per primo. |
| [**presentazione-14-luglio.md**](presentazione-14-luglio.md) | **Preparazione all'esposizione** — scaletta, demo, domande probabili del prof con risposte. |
| [development.md](development.md) | Setup locale, test, lint, variabili d'ambiente per ogni componente. |

## 📦 Aree tecniche per componente

| Area | Documenti |
|------|-----------|
| **Scraper** | [scraper/architecture.md](scraper/architecture.md) — connettori, normalizzazione, Wikidata, delta, systemd |
| **Backend** | [backend/architecture.md](backend/architecture.md) — layer, modelli, endpoint · [backend/schema-mapping.md](backend/schema-mapping.md) — mapping JSON→DB (autorevole per il seed) · [backend/api.md](backend/api.md) — **contratto API per il team frontend** |
| **App** | [app/overview.md](app/overview.md) — stack, struttura, schermate, client API, avvio (backend+app), web+telefono · [app/integrazione-e-fix.md](app/integrazione-e-fix.md) — integrazione frontend e fix applicati |
| **Worker** | [worker/overview.md](worker/overview.md) — hosting Cloudflare Pages + nota sul codice legacy |

## 📋 ISS — documenti formali del corso

Ingegneria del Software, ITS Umbria Academy a.a. 2025/2026 (team RepCode).

| Documento | Contenuto |
|-----------|-----------|
| [iss/analisi-requisiti.md](iss/analisi-requisiti.md) | RF, RNF, stakeholder, matrice importanza-difficoltà, risk assessment |
| [iss/sprint-plan.md](iss/sprint-plan.md) | User stories, 5 sprint, piano rilasci Alpha→1.0→1.1 |
| [iss/progettazione-uml.md](iss/progettazione-uml.md) | Use case, class diagram, ER, sequence, deployment + design pattern |

## 📂 Struttura

```
cineposto/docs/
├── index.md                     ← questo hub
├── panoramica.md                ← il sistema end-to-end (leggere per primo)
├── presentazione-14-luglio.md   ← guida esposizione
├── development.md               ← setup, test, lint
├── scraper/architecture.md
├── backend/
│   ├── architecture.md
│   ├── schema-mapping.md
│   └── api.md                   ← contratto API per il frontend
├── app/
│   ├── overview.md
│   └── integrazione-e-fix.md    ← integrazione frontend + fix
├── worker/overview.md
└── iss/                         ← documenti formali del corso
    ├── analisi-requisiti.md
    ├── sprint-plan.md
    └── progettazione-uml.md
```

### Regola d'oro

- **Documentazione tecnica** → sempre in `docs/`, nell'area del suo componente
- **`README.md` nei componenti** → solo front-door (link e quickstart)
- **Documenti formali del corso** → `iss/`
- Niente documenti storici od operativi consumati: quando un piano è eseguito, si cancella
