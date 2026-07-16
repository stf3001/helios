# HELIOS — Plateforme de diagnostic énergétique assisté par IA

Accompagner chaque foyer dans la transition énergétique de son logement.
Valeurs : transparence, honnêteté, excellence, humilité. Esprit colibri : chaque geste compte.

## Structure
- `frontend/` — React 19 + Vite + TS + Tailwind (site public + espace client)
- `api/` — FastAPI (auth, fiche maison, chat Helios, audits, leads)
- `agents/` — data-crawler & veille (docs 07)
- `kb/` — base de connaissances versionnée (FAQ + chunks, ingérée vers pgvector)
- `prompts/` — constitution d'Helios versionnée
- `deploy/` — nginx, scripts serveur Oracle

## Démarrage local
```bash
cp .env.example .env          # renseigner les secrets
docker compose up -d postgres # BDD
cd api && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```
Docs de cadrage : dossier parent (00 à 10).
