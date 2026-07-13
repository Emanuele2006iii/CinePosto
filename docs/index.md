# Documentazione CinePosto

Aggregatore cinema Umbria: scraper Python, backend FastAPI, app React Native. Tutta la documentazione tecnica vive qui, divisa per componente; nelle cartelle del codice c'è solo un README breve con i comandi essenziali.

## Da dove partire

- [panoramica.md](panoramica.md) — il sistema da cima a fondo: flusso dei dati, componenti, decisioni di design. Il primo da leggere.
- [presentazione-14-luglio.md](presentazione-14-luglio.md) — preparazione all'esposizione: scaletta, script della demo, piano B per la rete, domande probabili del prof.
- [development.md](development.md) — setup locale, test, lint e variabili d'ambiente di ogni componente.

## Aree tecniche

- **Scraper** — [scraper/architecture.md](scraper/architecture.md): connettori, normalizzazione, Wikidata, delta, deploy systemd.
- **Backend** — [backend/architecture.md](backend/architecture.md) (layer, modelli, endpoint), [backend/schema-mapping.md](backend/schema-mapping.md) (come ogni campo JSON diventa colonna, autorevole per il seed), [backend/api.md](backend/api.md) (contratto API completo).
- **App** — [app/overview.md](app/overview.md) (stack, schermate, client API, avvio), [app/integrazione-e-fix.md](app/integrazione-e-fix.md) (integrazione del frontend e fix applicati).

## Documenti del corso (ISS)

Ingegneria del Software, ITS Umbria Academy a.a. 2025/2026 (team RepCode).

- [iss/analisi-requisiti.md](iss/analisi-requisiti.md) — requisiti funzionali e non, stakeholder, matrice importanza-difficoltà, risk assessment.
- [iss/sprint-plan.md](iss/sprint-plan.md) — user story, cinque sprint, piano di rilascio Alpha → 1.0 → 1.1.
- [iss/progettazione-uml.md](iss/progettazione-uml.md) — use case, class diagram, ER, sequence, deployment e design pattern.

## Come è organizzata

```
docs/
├── index.md                     questo indice
├── panoramica.md                il sistema end-to-end
├── presentazione-14-luglio.md   guida all'esposizione
├── development.md               setup, test, lint
├── scraper/architecture.md
├── backend/{architecture,schema-mapping,api}.md
├── app/{overview,integrazione-e-fix}.md
└── iss/{analisi-requisiti,sprint-plan,progettazione-uml}.md
```

Convenzione: la documentazione tecnica sta in `docs/`, nell'area del suo componente; i README nel codice contengono solo i comandi rapidi; i documenti del corso stanno in `iss/`.
