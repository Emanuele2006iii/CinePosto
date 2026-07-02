# App — Overview (React Native + Expo)

Stato: inizializzata, navigazione tab funzionante, schermate mock attive.

> 📱 **Per il team frontend**: prima di collegare l'app al backend, leggere [`docs/frontend-integration.md`](../frontend-integration.md) — contratto API, tipi JSDoc, esempi `fetch`, checklist di setup.

---

## Stack

- **React Native** + **Expo SDK 54** — unica codebase per iOS, Android e web
- **Expo Go** sul device fisico (iOS/Android) — SDK 54 è la versione massima compatibile con Expo Go
- **Linguaggio attuale**: `.jsx`. **Target Sprint 3** (decisione D5): migrare a `.tsx` — `tsconfig.json` è già presente, mancano le conversioni dei 2 file esistenti
- **Routing:** Expo Router v6 (file-based), struttura `(tabs)/`
- **Web build** distribuita su Cloudflare Pages via `worker/`
- **Dati** serviti dal backend FastAPI (per ora mock locali — collegamento previsto Sprint 3, vedi [CONTINUAZIONE-PROGETTUALE.md](../CONTINUAZIONE-PROGETTUALE.md) §7)

> **IMPORTANTE:** NON usare `npx create-expo-app` — installa sempre l'SDK più recente (55+), incompatibile con Expo Go. Usare la procedura manuale qui sotto.

---

## Struttura file attuale

```
app/
├── package.json           ← Expo SDK 54 definitivo
├── app.json               ← name "CinePosto", slug "cineposto", scheme "cineposto"
├── babel.config.js        ← babel-preset-expo (obbligatorio)
├── tsconfig.json          ← extends expo/tsconfig.base, allowJs:true, include .jsx/.js
└── src/app/
    ├── _layout.jsx        ← Stack, headerShown:false
    └── (tabs)/
        ├── _layout.jsx    ← Tabs, activeTintColor #E50914
        ├── index.jsx      ← Home "Film Oggi": FlatList film mock con orari e link cinema
        └── cinema.jsx     ← Lista 3 cinema umbri con indirizzo e link sito
```

---

## Setup da zero (SDK 54 verificata)

```bash
cd app
# 1. Installa expo
npm install expo@~54.0.0
# 2. Installa pacchetti compatibili (una sola riga)
npx expo install react react-native react-dom react-native-web react-native-safe-area-context react-native-screens expo-router expo-asset expo-constants expo-font expo-linking expo-splash-screen expo-status-bar expo-system-ui
# 3. Installa babel preset (obbligatorio, spesso dimenticato)
npx expo install babel-preset-expo
# 4. Avvia
npx expo start
```

Scansiona il QR code con Expo Go su iOS/Android.

---

## Versioni installate (SDK 54)

| Pacchetto | Versione |
|---|---|
| expo | ~54.0.x |
| react | 19.1.0 |
| react-native | 0.81.5 |
| expo-router | 6.0.24 |
| babel-preset-expo | 54.0.11 |

---

## Note architetturali

- React Native Web copre il target browser — non serve frontend separato
- Web build: `npx expo export --platform web` → output in `worker/pages-public/`
- Cloudflare Pages serve la build da `worker/` con CDN globale
- Il colore brand è `#E50914` (rosso cinema)
