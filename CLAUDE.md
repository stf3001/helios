# HELIOS — instructions pour Claude (Code)

## Contexte
Plateforme de diagnostic énergétique assisté par IA. Tout le cadrage est dans le dossier parent :
docs 00 (trame) à 10 (stack + plan de dev en 10 jalons), FAQ 109 entrées (05), KB/ (chunks RAG).
**Lire en priorité : 10-STACK-TECHNIQUE-ET-PLAN-DEV.md et 03-CONSTITUTION-HELIOS.md.**

## Règles du projet
- Valeurs non négociables (charte, doc 01) : transparence, honnêteté, excellence, humilité. Helios ne pousse jamais un partenaire, ne donne jamais de chiffre certain, n'est pas un audit réglementaire.
- Les chiffres des pré-audits viennent d'un moteur déterministe (audit_engine), JAMAIS du LLM (doc 07 §6).
- Secrets uniquement en .env (jamais commités). Anonymiser toute donnée envoyée à une API LLM externe.
- KB et prompts versionnés dans git (kb/, prompts/) = source de vérité, réingérés vers pgvector.

## État (17/07/2026)
- Jalon 1 FAIT : structure repo, docker-compose (postgres+pgvector), API FastAPI /health, front vitrine React 19/Vite/TS/Tailwind (7 pages publiques, textes du doc 06, palette solaire primary #E8871E). Build vérifié.
- Jalon 2 FAIT et validé de bout en bout : auth JWT (access en mémoire + refresh token en cookie httpOnly rotatif), vérification email (lien loggé en dev tant que EMAIL_API_KEY est vide), fiche Maison par blocs (doc 02 §2) avec score de complétude pondéré (doc 02 §4, `api/app/services/completeness.py`), migration Alembic initiale (`api/alembic/versions/0001_initial_schema.py`, sans pgvector/pgcrypto — pas utiles avant J3). Testé contre une vraie base Postgres (voir note Docker ci-dessous) : register, login, refresh rotatif, `/auth/me`, création + PATCH de la fiche maison, score recalculé correctement (20 % après remplissage du bloc identité).
- Jalon 3 CODÉ (partiellement validé — voir blocage pgvector ci-dessous) : modèles `kb_documents`/`kb_chunks` (embedding `vector(1024)` pour bge-m3)/`conversations`/`messages` (`api/app/models/kb.py`, `conversation.py`), migration `0002_kb_chat.py`, client Ollama (`api/app/services/ollama_client.py` — embeddings + génération streaming), service RAG (`api/app/services/rag.py` — recherche cosinus, seuil de pertinence `rag_score_threshold`, prompt = constitution + sources + question), router `/api/chat/messages` (streaming NDJSON avec citations, doc 07 §4-5, mode public uniquement — pas de routeur hybride ni contexte fiche, c'est J4), script d'ingestion `agents/ingest.py` (parse `05-FAQ-V1.md`), widget de chat sur `/helios` (`frontend/src/components/chat/ChatWidget.tsx`). `prompts/constitution-v0.1.md` synchronisé avec le doc 03 (sections 1-6 seulement, la section 7 est pour les devs).
- **Validé réellement** (sans DB, ou contre Ollama réel) : parseur FAQ (109/109 entrées, `agents/ingest.py:parse_faq`), embeddings bge-m3 (1024 dims) et génération llama3.2:3b via Ollama en local, construction du prompt RAG (constitution complète + sources + question), génération réelle testée avec une source injectée — Helios reprend fidèlement les chiffres fournis sans halluciner. Build front OK, toutes les routes API s'enregistrent (`/api/chat/messages` inclus).
- **Bloqué sur cette machine (pas de Docker + pas de Visual Studio Build Tools)** : `pgvector` n'a pas de paquet Windows précompilé (vérifié : ni winget ni choco). La migration `0002` échoue donc ici (`CREATE EXTENSION vector` indisponible) — confirmé par un vrai test : `/api/chat/messages` répond 500 (`relation "conversations" n'existe pas`), erreur strictement liée à l'absence de la table, pas un bug de code. **À faire sur une machine avec Docker** : `docker compose up -d postgres` (image `pgvector/pg16`) puis `cd api && alembic upgrade head` et `api/.venv/Scripts/python.exe agents/ingest.py` (ou l'équivalent Linux) pour ingérer la FAQ et tester le chat de bout en bout.
- Jalon 4 CODÉ (logique pure validée contre Ollama réel ; parcours DB différé, même blocage pgvector que J3) : mode connecté + routeur hybride local/API.
  - `POST /api/chat/messages` accepte désormais un token optionnel (`get_optional_user` dans `deps.py`) : anonyme → `mode="public"`, connecté → `mode="connecte"` + fiche Maison injectée dans le prompt (`rag.build_house_context` réutilise `completeness.py`, `rag.build_prompt(..., house_context)` devient mode-aware). Vérif de propriété de conversation pour éviter le détournement.
  - Routeur `api/app/services/router_llm.py` : `choose_route()` (règles doc 07 §5 : public→local ; connecté + score≥40% + message long/mot-clé → api ; sinon local), `generate_route()` (fallback local + flag `simplified` si clé vide/API en erreur/plafond dépassé), `cost_caps_exceeded()` (SUM `estimated_cost_eur` jour/utilisateur + mois/global), `estimate_cost_eur()`.
  - Client `api/app/services/anthropic_client.py` (SDK `anthropic`, même signature `generate_stream` que Ollama — interchangeables ; lève `ApiUnavailable` immédiatement si `LLM_API_KEY` vide, jamais d'appel réseau à vide).
  - Migration `0003_connected_mode.py` : ajoute `citations`, `chunks_used`, `constitution_version`, `estimated_cost_eur` sur `messages` (log doc 07 §4.5 / doc 03 §7). Nouveaux réglages dans `config.py` : `llm_api_model`, `llm_api_budget_monthly_eur`, `llm_price_per_1k_tokens_eur`, `constitution_version`, seuils de routage.
  - Endpoints historique : `GET /api/chat/conversations` + `GET /api/chat/conversations/{id}/messages` (auth stricte + vérif propriété).
  - Frontend : `ChatWidget` prend une prop `fetchImpl` (→ réutilisé en public via `fetch` et en connecté via `authFetch`), bandeau « mode simplifié ». Nouvelle page protégée `/espace/helios` (`EspaceHelios.tsx`) : liste minimale des conversations + chat connecté. Lien « Mon Helios » ajouté au header.
- **Validé sur cette machine (Ollama réel, sans DB/pgvector/clé API)** : `choose_route` (7 cas, toutes branches), `build_house_context` + `build_prompt` mode-aware, `anthropic_client` lève bien `ApiUnavailable` sans tenter d'appel réseau, `generate_route` bascule en local + `simplified=True` et produit de vrais tokens Ollama, `estimate_cost_eur`, migration `0003` en DDL (`alembic upgrade head --sql`), build front (`tsc -b && vite build`), `/espace/helios` redirige vers `/connexion` si non authentifié, `/helios` public intact.
- **Différé (même blocage pgvector, + pas de clé Anthropic ici)** : parcours `/chat/messages` en mode connecté de bout en bout (nécessite pgvector pour `search_chunks`), vrai appel Claude streamé + précision réelle du calcul de coût/tokens (l'estimation `len//4` est grossière, à calibrer), tests d'intégration des endpoints d'historique. À valider en env Docker + avec une vraie `LLM_API_KEY`.
- Prochain : Jalon 5 (simulateur solaire PVGIS + géocodage).

## Commandes
- Front : `cd frontend && npm install && npm run dev` (build : `npm run build`)
- API : `cd api && pip install -r requirements.txt && uvicorn app.main:app --reload`
- BDD (avec Docker) : `docker compose up -d postgres` puis `cd api && alembic upgrade head`
- Ingestion FAQ (nécessite Ollama + pgvector) : `api/.venv/Scripts/python.exe agents/ingest.py`
- Ollama local : `ollama pull bge-m3 && ollama pull llama3.2:3b` (déjà fait sur cette machine, service tourne sur :11434)
- Mode connecté / API Claude : renseigner `LLM_API_KEY` dans `.env` (vide par défaut → tout reste en local, « mode simplifié »). Modèle par défaut `claude-haiku-4-5-20251001` (cf. `config.py`).

## Remote
https://github.com/stf3001/helios.git
