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

## État (18/07/2026) — J1→J8 + J10 + trous produit (reste : J9 déploiement)

> **Refonte visuelle & PWA (19/07/2026)** — ton chaleureux « esprit colibri », orange dominant + accents bleu marine (`ink`)/vert (`leaf`) du logo, fonds crème.
> - **Marque** : logo H + avatar mascotte Helios dans `frontend/public/brand/` (traités depuis les concepts de l'utilisateur via Pillow) ; icônes d'app 192/512/maskable/apple-touch + favicon dans `public/`.
> - **Typo auto-hébergée** (RGPD, pas de Google CDN) : Fraunces (titres, `font-display`) + Nunito (corps) — woff2 dans `public/fonts/`, `@font-face` dans `src/fonts.css`. Tokens Tailwind : `ink sky leaf cream` + animations `slide-up`/`fade-in`.
> - **PWA installable** : `public/manifest.webmanifest` + `public/sw.js` (network-first nav, cache assets, **ignore `/api/`**). SW enregistré **uniquement en prod** (`import.meta.env.PROD` dans `main.tsx`) — sinon il sert des assets périmés et casse le HMR dev. `src/vite-env.d.ts` ajouté pour typer `import.meta.env`.
> - **Mobile** : menu burger dans `Header.tsx` ; chat plein écran (70vh) avec avatar + amorces.
> - **Pédagogie** : `components/HierarchieColibri.tsx` (constitution §3), pages `/guides` (+`/guides/:slug`, données `data/guides.ts` — chapôs réels, sections en placeholders `[À rédiger]`), `/glossaire` (`data/glossaire.ts`, 14 termes). Accueil narratif refondu (`Home.tsx`).
> - **Finitions** : `hooks/useTitle.ts` (titres SEO par page) ; `components/Skeleton.tsx` ; encouragements bienveillants dans `CompletenessBar.tsx` ; footer navy avec colonne Ressources.
> - **À rédiger par l'utilisateur** (choix « structure seulement ») : le contenu réel des guides (`data/guides.ts`), les définitions sensibles du glossaire (montants d'aides marqués `[à vérifier]`), les textes marketing de l'accueil.


> **Lot UX 20/07 (spec expérience client, validé avec l'utilisateur)** — objectif : rendre excellent l'existant, zéro sur-ingénierie. Gemma reste pour la migration serveur (décision utilisateur).
> - **Réponses instantanées** (doc 07 §5 enfin fait) : `rag.instant_answer()` — si une fiche Q/R matche ≥ `rag_instant_answer_threshold`, le chat sert la réponse de la fiche SANS LLM (~0 s au lieu de 30-135 s), `model_used="kb"`, event `instant: true`. Seuil **0.66 calibré par mesure réelle** (exacte 0.69-0.80, paraphrase 0.67-0.69, hors-sujet 0.36 — le chunk Q+R dilue). `ChatIn.force_llm` + bouton « Développer avec Helios » dans le widget pour repasser au LLM (le message fiche est alors remplacé sans redoubler la question). Testé bout en bout : 4.2 s instant / force_llm et hors-sujet → LLM.
> - **Attente vivante** : `WaitIndicator` dans `ChatWidget` (points animés + messages progressifs à 0/6/20 s) à la place du « … » muet.
> - **États d'erreur** : `components/ApiError.tsx` (bannière « momentanément indisponible » + bouton Réessayer) branché sur Faq, Partenaires, Espace (404 fiche = état normal, distingué des vraies erreurs). Plus jamais de page silencieusement vide si l'API est down.
> - **Onboarding « 3 questions »** : création de fiche = code postal + année + chauffage (POST puis PATCH) → score > 0 immédiat ; accueil `/espace` sans fiche mis en scène (avatar + CTA « Répondre aux 3 questions »).
> - **`demarrer-helios.bat`** (racine) : double-clic → vérifie/lance Docker + Postgres, ouvre 2 fenêtres (API 8000, front 5173), ouvre le navigateur. Évite le piège « backend éteint = site qui semble vide » (vécu le 20/07).
> - **FAQ publique élargie** : `/api/faq` sert les 3 sources Q/R (`faq_maison`+`solutions`+`pilotage`) = 125 entrées.
> - Compte de test dev : `demo@helios.fr` / `Helios2026!` (email marqué vérifié en base).
> - **Guides rédigés** : les 6 guides de `data/guides.ts` sont des BROUILLONS complets tirés des fiches validées de la base (mêmes chiffres que la FAQ, zéro invention) — badge « bientôt » retiré, **à relire par l'utilisateur** (mention en tête de fichier).
> - **Citations cliquables** : les 📎 du chat → `/faq?q=<titre>` (recherche préremplie + fiche ouverte). Vérifié en navigateur : question → réponse instantanée + lien citation + « Développer avec Helios ».
> - **Page `/engagements`** (« Nos engagements ») : 6 garde-fous réellement implémentés (avis d'abord/négatif possible, jamais facturé au client, chiffres déterministes, comparateur public, RGPD+PDL, zéro démarchage) ; liens footer (Ressources + bloc Transparence).
> **Simulateur "Revolt" (22/07/2026)** — PV + batterie + tarifs dynamiques, à conso réelle égale.
> Décisions actées avec l'utilisateur avant de coder (je ne peux ni inscrire un vrai partenaire
> Enedis à sa place — SIRET/RGPD/callback public —, ni inventer des tarifs réels) :
> - **Enedis** : coder maintenant avec une courbe simulée, brancher les vraies clés plus tard.
> - **SOBRY SoFlex/SoCap** : grille de TEST fournie par l'utilisateur (SoFlex libre -0,13→0,38 €/kWh,
>   ~1000 h/an négatives ; SoCap plafonné 0→0,25 €/kWh), clairement étiquetée "à confirmer".
> - **Batterie virtuelle** : MyLight (MyBattery), tarifs 2026 relevés sur le web (papernest.com +
>   adsolar.fr, sources concordantes) — 179 € d'activation, ~1,20 €/kWc/mois, restitution ~0,083 €/kWh,
>   nécessite mylight150 comme fournisseur (contrainte réelle signalée à l'utilisateur).
> - `enedis_client.py` : courbe de charge horaire (8760 pts) SIMULÉE à partir du profil maison
>   (chauffage/occupants/conso annuelle), scaffold OAuth2 DataConnect dormant (lève tant que
>   `ENEDIS_CLIENT_ID` est vide) — bascule seule vers le réel le jour venu, zéro autre code à changer.
> - `pvgis.py` : `production_series_hourly()` (endpoint réel `seriescalc`, 8760 points/an, testé
>   réellement : 6 kWc à Lyon → 8059-8106 kWh/an selon l'année de référence).
> - `sobry_tariffs.py` : générateur déterministe de grille horaire annuelle (creux solaire
>   printemps/été à midi, pointes hiver) calé sur les stats fournies — vérifié : min/max exacts,
>   998 h négatives (cible ~1000).
> - `revolt_engine.py` (pur, sans I/O, testable) : `simulate_pv_only`, `simulate_pv_battery`
>   (glouton horaire, rendement configurable), `simulate_mylight` (stockage virtuel illimité),
>   `cost_annuel` (fixe/soflex/socap), `compare_scenarios` (matrice brique × tarif vs référence
>   sans PV). Testé bout en bout avec vrais appels PVGIS : PV+batterie > PV seul en autoconso et
>   économies, comme attendu.
> - Router `POST /api/revolt/simulate` (connecté, fiche requise) + `RevoltPanel.tsx` dans
>   `SimulateurSolaire.tsx` (connecté) : puissance simulée, batterie physique optionnelle, MyLight
>   optionnel, choix des tarifs à comparer, tableau brique × tarif avec économies vs actuel.
> - **Point de vigilance repéré (hors scope de ce lot, à traiter séparément)** : `solar_prix_revente_eur_kwh`
>   (0,13 €/kWh, config existante réutilisée telle quelle) contredit le fait déjà écrit dans
>   `kb/solutions.md` sur la réforme 2026 (surplus revendu ~0,01 €/kWh) — à harmoniser un jour,
>   n'affecte pas la correction du nouveau code mais rend le scénario "fixe" optimiste.
> - **Persistance (22/07/2026, demande utilisateur)** : `revolt_studies` (migration 0014, `house_id`
>   NOT NULL) — chaque simulation est conservée gratuitement dans l'espace client, sans action de
>   sa part (`POST /revolt/simulate` sauvegarde automatiquement, `GET /revolt/studies` liste
>   l'historique, affiché dans `RevoltPanel.tsx`). `rag.build_revolt_context()` résume la dernière
>   simulation (meilleur scénario) et l'injecte dans le prompt du chat (`chat.py`, à la suite du
>   contexte foyer) — Helios réutilise un calcul déjà fait plutôt que d'en inventer un nouveau.
>   Testé : contexte correctement construit et injecté dans le prompt.
> - **Bloqué en local au moment de coder** : le service Windows natif `postgresql-x64-17` a
>   redémarré et intercepte le port 5432 à la place du conteneur Docker (déjà vécu et documenté
>   plus haut) — je n'ai pas les droits admin pour l'arrêter depuis cet environnement. Logique
>   backend intégralement vérifiée par scripts reproduisant exactement le chemin du router
>   (geocoding réel + PVGIS réel + moteur), DB non requise pour ces tests. **Reste à faire par
>   l'utilisateur** : `Stop-Service postgresql-x64-17` (ou `services.msc`) puis test navigateur
>   complet du panneau Revolt sur `/simulateur-solaire`.

> **Audit esthétique (22/07/2026) — 2 correctifs demandés par l'utilisateur** :
> - **#1 Contraste CTA** : `tailwind.config.js` `primary` #E8871E → **#B85A08**. L'ancien couple
>   texte blanc/fond primary donnait un ratio **2,65:1** (échoue WCAG AA, seuil 4,5). Vérifié
>   dans le navigateur sur un vrai bouton du DOM (pas en théorie) : **4,66:1**, conforme — et
>   par symétrie du calcul de contraste, corrige aussi `text-primary` sur fond blanc (liens,
>   icônes). Rendu visuel toujours chaleureux (dégradé hero inchangé, juste un cran plus profond).
> - **#2 Illustrations sur les pages sans aucune image** (constat de l'audit : 0 image hors logo
>   sur Vision/Colibri) : hero à deux colonnes (texte + image) sur Vision et Qui sommes-nous,
>   réutilisant les assets de marque existants (`helios-arms.png`, `helios-thumbsup.png` — `helios-
>   avatar.png` écarté après vérification visuelle : texte parasite visible dans l'image, brouillon
>   inutilisable). Pour Colibri (aucun asset ne convenait) : illustration SVG sur-mesure d'un
>   colibri, palette de marque, sur un badge circulaire (nécessaire pour que la queue bleu marine
>   ressorte sur le dégradé orange — vérifié en navigateur, corrigé après un premier essai où les
>   couleurs terra/jaune se fondaient dans le fond).
> - Build front OK. Vérifié visuellement (captures) sur les 3 pages après correctifs.

> **Montée en puissance des connaissances (22/07/2026, Phase 1 du plan)** — après audit complet du
> fichier FAQ source (141 fiches, 21 catégories déjà bien couvertes : isolation, chauffage, PV,
> stockage, aides, DPE, copropriété, devis/chantier...), ciblage des VRAIS trous plutôt qu'une
> réécriture de ce qui existait déjà :
> - `kb/complements.md` (10 fiches) : aides locales (structurel, pas de montant national inventé),
>   bonus écologique/prime à la conversion VE, MaPrimeAdapt' (distinction), biomasse collective,
>   DPE et vente/notaire, résidence secondaire, auto-rénovation et assurance, PAC hybride,
>   assurance habitation après travaux, location meublée.
> - `kb/cas_pratiques.md` (4 fiches) : **nouveau type de contenu**, narratif plutôt que Q/R sec —
>   4 profils-types (maison 70s tout-élec budget serré, copro chauffage collectif gaz, jeune actif
>   RT2012+solaire, retraités passoire F) qui illustrent la méthode sobriété→isolation→systèmes→
>   production appliquée à un cas concret, sans jamais promettre un chiffre pour LE lecteur.
> - `frontend/src/data/glossaire.ts` : 14 → 40 termes (repris de la KB existante : TURPE, accise,
>   COP, DTG, PPT, ABF, PLU, TRV, garanties décennale/parfait achèvement, V2G/V2H, bonus
>   écologique...).
> - Sources branchées au crawler + FAQ publique + réponses instantanées. Ingéré : **155 fiches
>   au total** (141 + 14). Testé réellement : question VE → réponse instantanée (3-4s) citant
>   correctement `complements`.
> - **Phase 3 faite dans la foulée** : `data/guides.ts` 6 → **15 guides** (9 nouveaux : locataire,
>   copropriété, comprendre son DPE, devis/pièges, après le pré-audit, produire son eau, véhicule
>   électrique, comprendre Revolt) — mêmes faits que la KB, aucun chiffre inventé. Nouvelles
>   catégories : Locataire, Copropriété, DPE, Chantier, Eau, Mobilité. Vérifié en navigateur
>   (liste + un guide détaillé, rendu propre). Build front OK.
> - Reste du plan (non fait) : Phase 4 (veille active sur les fiches "aides"/"réglementation"
>   avec recherche web ciblée à chaque péremption détectée).

> **Espace client étoffé (22/07/2026, inspiré du dashboard Hydrolia)** :
> - **CTA « Parler à Helios » proéminent** en tête d'espace (bandeau ink/primary), rappelant qu'Helios connaît déjà la fiche et les simulations — pas de re-saisie.
> - **Section « Mes simulateurs »** : solaire (Revolt), potentiel hydrique, et **Éolia en tuile « bientôt disponible »** (grisée, non cliquable — honnête, rien n'est promis avant d'exister).
> - **« Mes documents » remonté en premier niveau** sur `/espace` (plus seulement dans `/mon-espace`) : le composant `HouseDocuments` est réutilisé tel quel (auto-suffisant, fetch ses propres données).
> - **Limite de 6 documents/maison** (`MAX_DOCUMENTS_PAR_MAISON`, `documents.py`) — 400 explicite au 7ᵉ upload, compteur "x/6" et bouton désactivé côté front. Testé réellement : 6 uploads OK, 7ᵉ rejeté.
> - **« Avis d'Helios » sur un devis** : nouvel endpoint `GET /houses/me/documents/{id}/extract` (pypdf, texte tronqué à 6000 caractères, PDF uniquement) → le frontend pré-remplit le champ de saisie du chat (`ChatWidget.initialInput`, `EspaceHelios` lit `?ask=`) avec le contenu réel du document. L'utilisateur relit et envoie lui-même — rien n'est expédié automatiquement, aucun chiffre n'est jamais garanti sur un document non vérifié. Testé réellement avec un vrai PDF (fpdf2) : extraction correcte, redirection avec le bon texte, champ pré-rempli confirmé en navigateur.
> - Nouvelle dépendance : `pypdf==5.1.*`.
> - **Refonte engagement institutionnel** (inspiré d'une analyse du site jumeau Hydrolia, en gardant l'honnêteté constitution) :
>   - `components/ScrollReveal.tsx` : révélation au scroll (IntersectionObserver + `animate-slide-up` déjà existant), zéro nouvelle dépendance, `as` polymorphe.
>   - `components/CtaFaisTaPart.tsx` : bandeau CTA réutilisable (« Parler à Helios » / « Créer ma fiche »), posé sur Colibri et Qui sommes-nous.
>   - **`/colibri` refondu** : légende mise en avant, 4 gestes Helios (thermostat, combles, solaire, pilotage — chiffres repris tels quels de la KB, jamais de total inventé), section « Et à grande échelle ? » qui refuse EXPLICITEMENT les faux chiffres d'impact façon Hydrolia (1500 bouteilles évitées etc.) au profit d'un discours qualitatif honnête, section « Faites votre part ».
>   - **`/qui-sommes-nous` créée** (n'existait pas) : origine/mission, alliance humain+IA, la constitution présentée comme preuve (pas promesse) avec lien vers `/engagements`, ce qui nous anime. Route + liens footer (Ressources) + liens croisés Vision↔Colibri↔Qui sommes-nous.
>   - **`/vision`** : grilles Capacités/Valeurs animées au scroll, 3e lien CTA final vers Qui sommes-nous.
> - **Intégration Hydrolia (section eau)** : `kb/eau.md` (9 fiches Q/R publiques : techno AWG, production/climat, prix 20L ~1990 € TTC indicatif, potabilité/kit in situ, robinet vs bouteille — parler-vrai, élec/couplage solaire, cibles, histoire Hydrolia, entretien/filtres) — source `eau` déclarée au crawler, dans `FAQ_SOURCES` et `rag._QR_SOURCES` (réponses instantanées). Page publique `/eau` (4 étapes, parler-vrai, 3 publics, CTA simulateur+chat, bloc transparence apporteur d'affaires) ; lien header « Eau », footer, lien retour depuis `/potentiel-hydrique`, chip accueil « Son eau » cliquable. RÈGLE respectée : zéro donnée business du partenaire (marges/levée/SWOT) dans le repo.

> **Lot 20/07 — Storage/eau/pilotage/courtage/Espace Pro + intégration chat** (migrations 0011→0013) :
> - **Connaissances** (`kb/solutions.md`, `kb/pilotage.md`, ingérées via crawler) : stockage (LFP, sodium-ion, inertie Energisto 10 kWh/9000 €/garantie 40 ans), eau atmosphérique (Hydrolia), pilotage/HEMS (Ecojoko/Comwatt/MyLight), offres d'achat EDF/TotalEnergies/Engie, courtage.
> - **Simulateur solaire** : `solar_engine.STORAGE_TECHS` → `stockage_options` (LFP/sodium/inertie), comparatif dans `SimulateurSolaire.tsx`.
> - **#3 Potentiel hydrique** (migration 0012 `water_studies`) : `water_engine.py` (tables Hydrolia gitignorées `api/data/hydrolia/`, interpolation bilinéaire, fallback), page `/potentiel-hydrique`. Données propriétaires JAMAIS commitées (export Notion déplacé hors repo).
> - **Courtage énergie** : `courtage_client.py` (`estimation(house=None, infos, gain_pct)` — résidentiel ET pro ; `helios_opinion` = règle 5 % + comparateur public + jamais de commission du client), section courtage dans `EspaceEnergie.tsx` (recueil d'infos + consentement horodaté). Partenaire courtier à définir.
> - **#5 Espace Pro** (migration 0013 `pro_profiles`) : `ProProfile` (secteur/surface/équipements/conso…), `pro_advisor.py` (conseils par secteur : boulangerie fours/froid/puissance, restauration, commerce…), router `/api/pro/{profile,advice,courtage}` (courtage pro sans persistance car `energy_studies.house_id` NOT NULL), page `/espace/pro`. Tuile Espace Pro dans `/espace`.
> - **Intégration chat** : `chat.send_message` charge `ProProfile` (+ `House`) de l'utilisateur connecté ; `rag.build_pro_context()` + `rag.build_prompt(..., pro_context)` ajoutent un bloc « MODE CONNECTÉ — CLIENT PROFESSIONNEL » qui prime sur le foyer. Helios détecte le contexte et adapte questions/conseils (postes énergivores du métier, courtage pro). Aucun champ sensible transmis (id/user_id/timestamps exclus, comme PDL côté foyer).
> - Migrations à jour : `alembic upgrade head` applique 0001→0013 (appliquées sur le Postgres Docker).

> **Gros lot du 18/07 (après J8)** — tout validé de bout en bout (API + migrations 0008→0010 + build front) :
> - **Sécurité/conformité** : PDL exclu du contexte LLM (`rag._HOUSE_CONTEXT_EXCLUDE`), constitution **v0.2** (chemin piloté par `settings.constitution_version` ; §5bis garde-fous énergie/SOBRY), **rate limiting** slowapi (login 10/min, register 5/min, chat 20/min → 429).
> - **Upload documents** (`house_documents`, migration 0008) : router `/api/houses/me/documents` (PDF/images, 10 Mo, dpe/facture/devis/photo), stockage `generated/house_docs/` (gitignoré) ; composant `HouseDocuments` dans la fiche.
> - **Admin + espace partenaire** (migration 0009 `partners.password_hash`) : admin par secret `X-Admin-Token` (`require_admin`) → `/api/admin/partners` (revue), activate (génère mdp initial), suspend ; auth partenaire (jeton `type=partner`, `get_current_partner`), `/api/partner/login|leads|leads/{id}/status` (vraie transition côté partenaire, commission auto à SIGNÉ) ; page `/partenaire` (login+dashboard, token localStorage).
> - **Dashboard + RGPD** : dashboard `/espace` (résumé fiche + tuiles ; header pointe dessus et désencombré) ; router `/api/account` : export (portabilité, sans hash), consentements (toggle `consent_leads`), suppression de compte (droit à l'effacement, cascade + fichiers) ; page `/espace/compte`.
> - **J10 agents** (`agents_log`, migration 0010) : framework `api/app/services/agents_engine.py` — sources déclarées (`SOURCES`), `crawl_source`/`run_crawler` (fetch→parse→embed→upsert kb, journalisé), `run_veille` (repère les kb_documents périmés selon `date_maj`). CLI `agents/run_agents.py {crawl|veille}` ; `agents/ingest.py` délègue désormais au framework (ingestion manuelle = agent crawler unifiés). Endpoint `GET /api/admin/agents-log`. Validé : crawler ré-ingère la FAQ (109 upsert), veille détecte la péremption, journal consultable. **Sources web (aides/prix) prévues mais à déclarer/calibrer** (échec réseau journalisé, non bloquant).
> - Migrations à jour : `alembic upgrade head` applique 0001→0010. Nouvelles deps : `slowapi`, `python-multipart` (déjà dans requirements.txt).

## État (18/07/2026) — J1→J8 (8 jalons sur 10)

> **⚡ Docker installé (17/07/2026) — le blocage pgvector est LEVÉ.** Docker Desktop 4.82 + WSL2 sont en place. `docker compose up -d postgres` (image `pgvector/pgvector:pg16`) tourne (conteneur `helios-postgres-1`, port 5432). Le Postgres natif Windows a été **arrêté** (`Stop-Service postgresql-x64-17`) pour libérer le port — le repartir en cas de besoin, mais Docker est désormais la référence. **Les 4 migrations (0001→0004) s'appliquent proprement d'un coup** (`cd api && alembic upgrade head`), la FAQ est ingérée (109 chunks dans pgvector), et **le chat RAG J3/J4 est validé de bout en bout** (voir plus bas). Note PATH : appeler `docker` via un shell peut échouer sur `docker-credential-desktop` — ajouter `C:\Program Files\Docker\Docker\resources\bin` au PATH, ou utiliser le terminal fourni par Docker Desktop.
> **Chat RAG validé réellement** : question publique « par quoi isoler ma maison » → pgvector retrouve la bonne entrée FAQ (score 0.688) → Helios répond en reprenant fidèlement les chiffres, avec citations ; mode connecté (fiche 45 %, niveau `prediagnostic_qualitatif`) → `mode=connecte`, routage API tenté puis fallback local `simplified=True` (pas de clé Anthropic) ; message assistant stocké avec `model_used`, `constitution_version=v0.1`, 8 citations en base (log doc 07 §4.5). Il ne reste à valider qu'avec une **vraie `LLM_API_KEY`** : le vrai appel Claude streamé (le fallback, lui, est prouvé).

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
- Jalon 5 FAIT et validé de bout en bout (aucune dépendance pgvector — entièrement testable ici) : **simulateur de potentiel solaire** (doc 09 §1), ouvert au public (résultats partiels = aimant à inscriptions) et complet + stocké si connecté.
  - Services : `api/app/services/geocoding.py` (API Adresse data.gouv, adresse→GPS), `pvgis.py` (PVGIS Commission européenne, production 3/6/9 kWc ; mapping orientation→azimut, ombrage→pertes), `solar_engine.py` (moteur DÉTERMINISTE — jamais le LLM, doc 07 §6 : autoconso sans/avec pilotage + batterie, économies €/an en fourchettes ±12 %, temps de retour ; toutes les hypothèses éco. dans `config.py` sous `solar_*`, ordres de grandeur 2026 à calibrer).
  - Router `api/app/routers/solar.py` : `POST /api/solar/simulate` (auth optionnelle — anonyme = production seule + CTA inscription, sans stockage ; connecté = scénarios complets + stockage `solar_studies`, valeurs par défaut reprises de la fiche Maison), `GET /api/solar/studies` (historique lié à la maison). Modèle `SolarStudy` + migration `0004_solar_studies.py`.
  - Frontend : page publique `/simulateur-solaire` (`SimulateurSolaire.tsx`) — formulaire adresse/orientation/pente/ombrage/conso → production par puissance, puis CTA inscription (anonyme) ou scénarios éco. complets (connecté). Lien « Simulateur solaire » dans le header.
  - **Validé réellement** : géocodage + PVGIS réels (Paris/Lyon, ombrage et orientation nord/sud correctement pris en compte), moteur de scénarios (cohérence autoconso sans<avec pilotage<batterie, fourchettes), parcours public dans le navigateur (Lyon → 3804/7609/11413 kWh + CTA), parcours connecté via API (scénarios complets + stockage + `GET /studies` lié à la maison — table `solar_studies` créée manuellement ici pour contourner le blocage pgvector des migrations 0002/0003), migration `0004` en DDL, build front.
  - NB pgvector : sur cette machine, `alembic_version` reste à `0001` (les migrations 0002+ sont bloquées par pgvector). `solar_studies` a été créée à la main pour les tests. En env Docker, `alembic upgrade head` appliquera proprement 0002→0004 d'un coup.
- Jalon 6 FAIT et validé de bout en bout (aucune dépendance externe — full stack Docker) : **pré-audit v1** (moteur déterministe → rendu web + PDF), critère de done = généré à ≥ 70 % de complétude.
  - Moteur `api/app/services/audit_engine.py` + tables `audit_reference.py` (méthode 3CL simplifiée dégradée, doc 07 §6) : déperditions par poste (ancrage DPE sinon année de construction, modulé par l'état d'isolation réel, somme 100 %), conso théorique vs déclarée, priorisation dans l'ordre de la constitution (sobriété→enveloppe→systèmes, pondérée par les objectifs), chiffrage en fourchettes (coûts/aides/économies/temps de retour). **Tous les chiffres sont déterministes, JAMAIS le LLM** (doc 07 §6). Hypothèses calibrables dans `audit_reference.py` + `config.py` (`audit_*`).
  - PDF serveur `api/app/services/pdf_audit.py` via **fpdf2** (pur Python, pas de dépendance système ; € écrit « EUR » car police latin-1). Stocké sous `api/generated/audits/` (gitignoré), chemin dans `audits.pdf_path`.
  - Modèle `Audit` + migration `0005_audits.py` (table `audits` : json_result JSONB, pdf_path, version_helios). Router `api/app/routers/audits.py` : `POST /api/audits` (409 si fiche < 70 %), `GET /api/audits` (liste), `GET /api/audits/{id}`, `GET /api/audits/{id}/pdf` (FileResponse) — auth stricte + vérif propriété (404 si pas à soi).
  - Frontend : page protégée `/espace/audits` (`EspaceAudits.tsx`) — jauge de complétude + bouton « Générer » (désactivé < 70 %), historique, rendu web (barres de déperdition, priorités chiffrées, synthèse), téléchargement PDF via `authFetch`→blob. Lien « Mes pré-audits » au header.
  - **Validé réellement** : moteur (déperditions à 100 %, murs non isolés en tête, hiérarchie sobriété<enveloppe<systèmes respectée, chiffres réalistes) ; PDF valide et bien mis en page (relu visuellement) ; API complète (génération, refus 409 à < 70 %, liste, PDF avec bons en-têtes HTTP) ; page navigateur (login → rendu de l'audit, bouton Générer produit un nouvel audit, PDF téléchargeable). Migration `0005` appliquée sur le Postgres Docker.
- Jalon 7 FAIT et validé de bout en bout : **espace énergie + module SOBRY** (doc 09 §2), critère de done = parcours SOBRY bout en bout.
  - Conseil niveau 1 `api/app/services/energy_advisor.py` (déterministe, sans tiers) : dimensionnement puissance souscrite, pertinence option HP/HC, compatibilité tarif dynamique (favorable/neutre/prudence selon usages pilotables). Client `sobry_client.py` : `spot_prices()` (API SOBRY si `SOBRY_SPOT_API_URL` configurée, sinon courbe de démonstration horaire étiquetée `source=demo`) + `estimation()` (gain simulé selon la pilotabilité, à remplacer par le retour réel SOBRY sur PDL).
  - Modèle `EnergyStudy` + migration `0006_energy_studies` (table `energy_studies` : pdl, consent_at horodaté, status `demandee|recue|presentee|souscrite|declinee`, result JSONB, helios_opinion). `partner_id` sans FK pour l'instant (FK vers `partners` en J8).
  - Router `api/app/routers/energy.py` : `GET /advice`, `GET /spot-prices`, `POST /study` (exige `consent=true` sinon 400), `GET /studies`, `POST /study/{id}/decision`. **Garde-fous constitution (doc 09 §2) appliqués dans le code** : étude jamais sans consentement explicite ; avis Helios (`_helios_opinion`, règle des 5 % + risque pointe hivernale) rendu AVANT toute incitation et pouvant être négatif ; **lien partenaire proposé UNIQUEMENT si l'avis est favorable** (vérifié : même avec `SOBRY_PARTNER_LINK` configuré, un avis défavorable ne renvoie aucun lien) ; comparateur public energie-info.fr toujours mentionné ; transparence sur la commission SOBRY.
  - Frontend : page protégée `/espace/energie` (`EspaceEnergie.tsx`) — conseil niveau 1, courbe de prix spot (barres), parcours SOBRY (case de consentement + PDL 14 chiffres, avis Helios présenté avant les boutons de décision, mention comparateur public). Lien « Énergie » au header.
  - **Validé réellement** : conseil déterministe (profils favorable/prudence distingués), prix spot + fallback démo (creux nuit 0.09 / pointe soir 0.31), parcours complet via API (refus 400 sans consentement, avis Helios avec comparateur + transparence commission, garde-fou lien-partenaire-si-favorable prouvé, décision souscrire/décliner, historique). Migration 0006 appliquée. Build front OK. Page confirmée montée + données chargées via le réseau (`/api/energy/advice` + `/spot-prices` 200) — le rendu navigateur exact n'a pas pu être capturé (bug de frames dupliquées du preview, screenshots en timeout toute la session).
  - **Reste à brancher** (hors scope done J7) : vraie API SOBRY (`SOBRY_SPOT_API_URL` + intégration PDL réelle au lieu de l'estimation simulée), lien apporteur réel (`SOBRY_PARTNER_LINK`), et la FK `partner_id`→`partners` (J8).
- Jalon 8 FAIT et validé de bout en bout : **annuaire partenaires + cycle de lead** (doc 08), critère de done = premier lead traçable.
  - Modèles `Partner`/`Lead`/`Review` (`api/app/models/partner.py`) + migration `0007_partners_leads` (crée les 3 tables + ajoute la FK `energy_studies.partner_id`→`partners` restée en attente depuis J7). Moteur `api/app/services/commission.py` : grille par métier (doc 08 §3, taux centraux : pv/pac 5 %, isolation/menuiseries 6,5 %, petits travaux 9 % avec forfait mini 100 € sur < 3 k€), déterministe.
  - Router `partners.py` : `GET /api/partners` (annuaire public, actifs uniquement, filtre `metier`/`zone`, SIRET/email non exposés), `POST /api/partners/apply` (candidature `/devenir-partenaire` → statut `candidat`, activation manuelle ensuite). Router `leads.py` : `POST /api/leads` (exige `consent=true` → `consent_client_at` horodaté, statut `transmis`, notif email partenaire loggée), `GET /api/leads`, `POST /leads/{id}/withdraw` (retrait consentement tant que non signé), `PATCH /leads/{id}/status` (cycle nouveau→transmis→contacté→devis→signé/perdu ; **commission auto-calculée à SIGNÉ** ; lead immuable après signé → 409), `POST /leads/{id}/review` (note 1-5 post-chantier → recalcule `note_moyenne` du partenaire).
  - Frontend : `/partenaires` branché sur l'annuaire réel (cartes RGE/métiers/note/zones), nouvelle page publique `/devenir-partenaire` (candidature), page protégée `/espace/mises-en-relation` (créer un lead avec consentement, suivi des statuts, retrait de consentement, notation). Liens header.
  - **Validé réellement** (11 vérifs API + navigateur) : candidature → non listée (candidat) → activation → apparaît dans l'annuaire filtré ; refus lead sans consentement (400) ; création lead consentie+horodatée ; cycle complet jusqu'à signé avec commission auto (PV 12 000 € → 600 €) ; immuabilité après signé (409) ; notation → note moyenne ; retrait de consentement (statut perdu). Migration 0007 appliquée. Build front OK. Annuaire public + page candidature vérifiés dans le navigateur (`/partenaires` affiche Solaris Renov RGE, `/devenir-partenaire` affiche le formulaire).
  - **Reste à brancher** (hors scope done J8) : espace partenaire (dashboard partenaire = phase 2, doc 04) ; endpoint admin de validation des candidatures (fait à la main en psql pour la démo) ; envoi email réel des notifs de lead (J9).
- Prochain : Jalon 9 (déploiement prod : Oracle Cloud, HTTPS, emails réels Resend/Brevo, rate limiting) — ou brancher la page FAQ publique sur les 109 entrées de la base (petit reste du doc 04).

## Commandes
- Front : `cd frontend && npm install && npm run dev` (build : `npm run build`)
- API : `cd api && pip install -r requirements.txt && uvicorn app.main:app --reload`
- BDD (avec Docker) : `docker compose up -d postgres` puis `cd api && alembic upgrade head`
- Ingestion FAQ (nécessite Ollama + pgvector) : `api/.venv/Scripts/python.exe agents/ingest.py`
- Ollama local : `ollama pull bge-m3 && ollama pull llama3.2:3b` (déjà fait sur cette machine, service tourne sur :11434)
- Mode connecté / API Claude : renseigner `LLM_API_KEY` dans `.env` (vide par défaut → tout reste en local, « mode simplifié »). Modèle par défaut `claude-haiku-4-5-20251001` (cf. `config.py`).

## Remote
https://github.com/stf3001/helios.git
