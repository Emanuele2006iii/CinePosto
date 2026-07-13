# Worker — Cloudflare Pages

## Ruolo nel sistema

Hosting della **web build** dell'app React Native: `npx expo export --platform web` genera una cartella statica che Cloudflare Pages serve. Nessuna logica server. Previsto per lo Sprint 4/5.

## Contenuto

| File | Ruolo |
|---|---|
| `worker/Makefile` | target `deploy`, `deploy-dev`, `tail` via wrangler |
| `worker/pages-public/index.html` | placeholder in attesa della web build |

## Deploy (quando la web build sarà pronta)

```bash
cd app && npx expo export --platform web     # genera dist/
cd ../worker && npx wrangler deploy          # pubblica su Cloudflare Pages
```
