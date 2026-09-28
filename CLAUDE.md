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

> **Conseil plus personnalisé (22/07/2026, retour utilisateur : « conseils trop généralistes »)** —
> suite à l'audit de suggestions, exécution des points #1 et #2 :
> - **#1 Exploiter les études déjà faites** : `rag.build_solar_context/audit_context/energy_context/
>   water_context` (même principe que `build_revolt_context`), branchés dans `chat.py` (requête la
>   dernière étude de chaque type pour la maison de l'utilisateur connecté) et dans `build_prompt`
>   (bloc générique par étude, avec consigne explicite de ne jamais confondre ces données réelles
>   avec un « cas pratique » fictif de la KB). **Point de vigilance découvert en testant réellement**
>   (compte démo, vraies données solaire+Revolt en base) : le modèle local `llama3.2:3b` reste trop
>   petit pour exploiter fiablement un prompt de ~16 Ko — premier essai : chiffres inventés en
>   confondant la fiche foyer avec un cas pratique fictif. Corrigé (consigne anti-confusion + profil
>   foyer/études repositionné juste avant la question, où un petit modèle local a plus d'attention)
>   : il n'invente plus, mais reste encore générique (repose des questions au lieu d'utiliser les
>   données déjà en base) — **limite réelle du modèle local, pas du câblage** ; une vraie
>   personnalisation fiable demandera soit un modèle local plus gros (`llama3.1:8b`, plus lent en
>   CPU), soit une vraie `LLM_API_KEY` (le routeur bascule déjà automatiquement les questions
>   complexes vers l'API dès qu'une clé est configurée).
> - **#2 Barèmes réels et sourcés** : `kb/baremes_aides.md` (7 fiches, recherche web recoupant
>   plusieurs agrégateurs spécialisés — Hellowatt, Effy, Primes Energie) : plafonds de revenus
>   bleu/jaune/violet/rose 2026, montants MaPrimeRénov' par geste (PAC, combles/toiture), **le
>   changement réglementaire important repéré en cherchant** (décret du 8/09/2025 : l'isolation des
>   murs seule n'est plus éligible en parcours par geste depuis le 1ᵉʳ janvier 2026, seulement en
>   rénovation d'ampleur), CEE (mécanisme, cumul avec MaPrimeRénov', 6ᵉ période 2026-2030), TVA
>   5,5 %/10 % (conditions, simplification Cerfa 2026), méthode pour les aides locales (pas de
>   montant nationalement inventé). Tagué `verif:date_sensible_22_07_2026` (à re-vérifier
>   périodiquement, candidat naturel pour la veille agent Phase 4 non encore faite). Branché au
>   crawler + `FAQ_SOURCES` + `rag._QR_SOURCES`. Ingéré et vérifié réellement : FAQ publique 155→162
>   fiches, réponse instantanée testée en 1,5 s citant la bonne fiche (score 0,782) sur la question
>   isolation des murs 2026.
> - **Reste des suggestions non traitées** (axes #3 benchmarks chiffrés réels, #4 DPE réel/
>   observatoire ADEME, #5 cas pratiques enrichis de vrais retours d'expérience, #6 granularité
>   climatique) : pas demandés pour l'instant.

> **Routage hybride local/API activé pour de vrai (22/07/2026)** — une vraie `LLM_API_KEY` Claude a
> été fournie par l'utilisateur, testée en conditions réelles pour la première fois :
> - Modèle **`claude-haiku-4-5-20251001`** (le plus économe en tokens de la gamme Claude) choisi
>   volontairement pendant le développement, sur demande explicite de l'utilisateur (« utilisation
>   minimale des crédits » avant mise en ligne). Budgets abaissés pendant le dev :
>   `LLM_API_BUDGET_DAILY_EUR=1`, `LLM_API_BUDGET_MONTHLY_EUR=10` (à remonter en prod).
> - **Nouveau quota** `llm_api_daily_requests_per_user` (3 par défaut, `config.py`) : indépendant du
>   plafond de coût global, protège contre un seul client qui viderait le budget partagé.
>   `router_llm.daily_quota_exceeded()` compte les `messages.model_used='api'` du jour pour ce
>   `user_id`, vérifié avant `cost_caps_exceeded()` dans `generate_route()`.
> - **Nouveau critère de bascule** : un pré-audit déjà généré pour le foyer (`has_recent_audit`,
>   dérivé de `audit_context is not None` dans `chat.py`) déclenche la route API au même titre
>   qu'un message long ou un mot-clé — la logique : un client qui a déjà un diagnostic chiffré
>   cherche probablement une explication approfondie, pas une généralité.
> - **Clé stockée dans `C:\Users\DELL\Desktop\HELIOS\.env`** (hors du repo git, un niveau au-dessus
>   de `helios/`) — piège découvert en debuggant : le process uvicorn lancé par l'outil de preview
>   tourne avec ce répertoire comme CWD, pas `helios/` ni `helios/api/` (`pydantic-settings` cherche
>   `.env` relatif au CWD réel du process, pas à l'emplacement du code). Un `.env` posé à la racine
>   du repo ou dans `api/` y était invisible — d'où un premier test qui basculait silencieusement
>   en « mode simplifié » sans jamais tenter l'appel API, aucune erreur nulle part (comportement
>   voulu du fallback, mais trompeur ici). Diagnostiqué avec un endpoint `/health` temporarisé
>   affichant `os.getcwd()` et `bool(settings.llm_api_key)`, retiré après coup.
> - **Validé réellement, avec de vrais coûts engagés (quelques centimes)** : appel direct minimal
>   (« réponds OK ») → réponse correcte ; puis un vrai parcours `/api/chat/messages` connecté avec
>   question complexe (mot-clé « combien ») sur le compte démo (fiche 90 %, étude solaire réelle en
>   base) → route `api` choisie, réponse en **12,4 s** (vs 60-150 s en local), **chiffres corrects
>   et personnalisés repris de la vraie étude solaire** (scénarios 3/6/9 kWc, productions et
>   économies réelles, recommandation argumentée) — contrairement au modèle local 3B qui restait
>   générique sur la même question. Quota vérifié : 1 requête API comptée pour l'utilisateur,
>   `daily_quota_exceeded` correctement à `False` sous le seuil de 3.
> - **Reste à faire** (non demandé pour l'instant) : bandeau front explicite quand le quota
>   quotidien est atteint (actuellement bascule silencieuse en mode simplifié, comme les autres
>   cas de fallback) ; remonter les budgets et le modèle une fois en prod.

> **Mise en cache des prompts Anthropic (22/07/2026, sur suggestion utilisateur)** — la constitution
> (identique à chaque appel, quel que soit l'utilisateur/la question) est maintenant séparée du
> contenu variable et envoyée en `system` avec `cache_control: ephemeral` :
> - `rag.py` : `build_prompt()` scindé en `constitution_text` (public) + `build_user_content()`
>   (sources RAG + fiche foyer + études + question, sans la constitution) ; `build_prompt()` redevient
>   un simple wrapper qui reconcatène les deux, gardé pour le modèle local (Ollama n'a pas de
>   séparation system/user ni de cache).
> - `anthropic_client.generate_stream(system, user_content)` : signature changée pour porter la
>   constitution dans le bloc `system` (`cache_control: {"type": "ephemeral"}`) ; logge
>   `usage.cache_creation_input_tokens`/`cache_read_input_tokens` après chaque appel
>   (`logger = logging.getLogger("helios.anthropic")`).
> - `router_llm.generate_route()` : paramètre renommé `prompt`→`user_content` ; reconstruit
>   `rag.constitution_text + user_content` pour le chemin local, passe les deux séparément à
>   `anthropic_client` pour le chemin API. `chat.py` mis à jour en conséquence.
> - **Mesuré réellement, pas supposé** : deux appels Claude Haiku consécutifs avec le même `system`
>   → `cache_write=0` et `cache_read=0` sur les deux. Cause identifiée : la constitution seule fait
>   **~1841 tokens** (mesuré via l'API, `usage.input_tokens`), sous le **seuil minimum de mise en
>   cache de Haiku 4.5 (4096 tokens)** — l'API ignore silencieusement le `cache_control` en dessous
>   de ce seuil (comportement documenté, pas un bug). **Donc aucun gain actuel avec Haiku.**
> - **Pourquoi le garder quand même** : (1) zéro coût/risque — un `cache_control` sous le seuil est
>   un no-op silencieux ; (2) le code est prêt sans rien reconstruire le jour où le modèle change —
>   Claude Sonnet 5 a un seuil minimum de **1024 tokens seulement**, sous lequel la constitution
>   (1841 tokens) serait déjà cacheable telle quelle ; (3) si le contenu système grossit (ex. contexte
>   foyer déplacé dans `system` plus tard), le même mécanisme s'activera automatiquement.
> - **Non prioritaire pour l'instant** : avec le quota de 3 requêtes API/jour/client déjà en place,
>   le volume est trop faible pour que la mise en cache change quoi que ce soit au coût réel, même
>   si le seuil était atteint — à réévaluer si le modèle change ou si le quota est relevé en prod.

> **Design/marketing pré-prod (22/07/2026) — points #1 et #2 de l'audit de suggestions** :
> - **#1 Audit mobile réel** (375×812, DOM/computed-style, pas de suppositions) : un seul vrai bug
>   trouvé — quasi tous les champs de formulaire du site (simulateur solaire, énergie, pro, Revolt,
>   devenir partenaire, recherches FAQ/glossaire) étaient en `text-sm` (14px), ce qui déclenche un
>   **zoom automatique iOS Safari** au focus (seuil 16px). Corrigé en une seule règle globale
>   (`frontend/src/index.css`, `input/select/textarea { font-size: 16px !important }` — `!important`
>   nécessaire car la spécificité d'une classe Tailwind bat un sélecteur de type simple) plutôt que
>   dans les ~15 fichiers concernés. Vérifié sur 8+ pages (dont `/espace`, `/espace/energie`,
>   `/espace/pro`, simulateur solaire connecté avec un vrai résultat Revolt/stockage affiché) :
>   zéro débordement horizontal, tuiles/liens correctement dimensionnés pour le tactile. Le menu
>   burger mobile a été vérifié fonctionnel (un faux positif initial venait de l'outillage de test
>   de session, pas du code).
> - **#2 Image de partage social + habillage PDF** :
>   - `frontend/public/og-image.png` (1200×630, généré via Pillow + polices de marque converties
>     woff2→ttf avec fontTools) : dégradé identique aux hero sections (`from-sun via-primary
>     to-terra`), logo + wordmark, tagline, mascotte `helios-thumbsup`. Branché dans `index.html`
>     (`og:image` + dimensions, `twitter:card=summary_large_image`) — **limite technique
>     assumée** : le site étant une SPA sans SSR, cette image sert de preview pour TOUTES les pages
>     (les crawlers sociaux ne lisent que le HTML initial, identique quelle que soit la route) ;
>     un aperçu par page nécessiterait du pré-rendu, hors scope ici.
>   - **Corrigé au passage** : `theme-color` de `index.html` était resté sur l'ancien orange
>     `#E8871E` alors que `tailwind.config.js` `primary` avait été assombri en `#B85A08` lors du
>     correctif de contraste — incohérence trouvée en marge, corrigée.
>   - `pdf_audit.py` : en-tête « lettre à en-tête » (bandeau crème, vrai logo `logo-mark.png`
>     embarqué, wordmark en `ink`, sous-titre en `primary` mis à jour), titres de section et fond
>     du tableau des priorités harmonisés avec la charte. Vérifié avec un vrai audit du compte démo
>     (rendu réel via PyMuPDF, pas une supposition) : rendu propre, logo net, couleurs correctes.

> **Système d'icônes par catégorie — guides/FAQ (22/07/2026, point #1 du plan visuel)** :
> - `frontend/src/data/categoryIcons.tsx` (nouveau) : mapping catégorie → icône `lucide-react` +
>   couleur de marque (tokens `tailwind.config.js`), avec `normalizeCat()` pour faire correspondre
>   les libellés capitalisés français des guides (« Copropriété ») et les clés en minuscules sans
>   accent de la FAQ (`copropriete`) — 25 catégories réelles couvertes (vérifiées via `/api/faq`),
>   fallback neutre (`Sparkles` gris) pour toute catégorie non mappée, jamais d'erreur.
> - Branché dans `Guides.tsx` (puces de filtre + icône sur chaque carte), `GuideDetail.tsx`
>   (badge icône en tête d'article) et `Faq.tsx` (puces de filtre + icône devant chaque question).
> - **Glossaire volontairement laissé de côté** : pas de champ catégorie dans `data/glossaire.ts`
>   (liste alphabétique pure), en ajouter un maintenant aurait été un chantier à part entière hors
>   demande — cohérent avec le plan proposé (« pas d'illustration nécessaire, traitement
>   typographique suffit »).
> - Vérifié en navigateur sur les 3 pages (build front OK + rendu réel des icônes/couleurs).
> - **Reste du plan visuel (non fait, discuté avec l'utilisateur mais pas démarré)** : la grande
>   illustration « maison de demain » (coupe de maison + animation CSS du flux d'énergie) — prévue
>   en étape suivante, dessin statique d'abord.

> **Illustration « La maison de demain » (22/07/2026)** — après un essai de SVG codé à la main
> jugé insuffisant (retiré), l'utilisateur a fourni une vraie infographie (générée par outil
> d'image externe : coupe de maison au trait + aplats de couleur de marque, flux d'énergie colorés,
> tulipes éoliennes, puits canadien, AWG). Intégrée comme asset :
> - `frontend/public/maison-demain.webp` — converti depuis le PNG source 1536×1024 (1,84 Mo) en
>   **WebP qualité 90 = 307 Ko** (6× plus léger, visuellement identique, vérifié). PNG lourd non
>   commité. WebP = support universel en 2026.
> - `frontend/src/components/MaisonDemain.tsx` (nouveau, remplace l'ancien SVG supprimé) : image
>   présentée en grand + **vue plein écran au clic** (overlay `fixed z-[100] bg-black/85`, fermeture
>   Échap/clic/croix, blocage du scroll de fond) — nécessaire car les légendes de l'infographie sont
>   illisibles à la taille réduite d'un mobile. Aucune dépendance (juste `useState`/`useEffect` +
>   icônes lucide). `loading="lazy"`, `width/height` explicites (anti-CLS), `alt` descriptif.
> - Placée en tête de `/comment-ca-marche` (juste après le Hero), avec titre + intro + **légende
>   honnête (constitution)** : précise que c'est la vision d'ensemble, distingue ce qui est
>   accessible aujourd'hui (solaire/stockage/pilotage/eau via partenaires) de ce qui viendra
>   (éolien domestique), et rappelle qu'Helios ne propose jamais un équipement inutile au foyer.
> - Vérifié en navigateur : rendu desktop, ouverture/fermeture du zoom plein écran (backdrop
>   `rgba(0,0,0,0.85)` au-dessus du header confirmé en computed-style), et mobile (image contenue
>   dans 375px, zéro débordement, tap-to-zoom fonctionnel). Build front OK.
> - **NB** : l'utilisateur a aussi une version animée (`maison_de_demain_anime.gif`/`.mp4` dans ses
>   Downloads) — non intégrée, à voir si souhaité plus tard (le GIF serait lourd, le MP4 en boucle
>   muette serait préférable).

> **Refonte du hero d'accueil (27/07/2026, suggestions marketing validées avec l'utilisateur)** —
> constat de départ : l'accueil parlait à 100 % de ce qu'Helios *ne fait pas* (3 négations
> défensives : gratuit/indépendant/données protégées), sans jamais dire ce qu'il *fait* pour
> l'habitant → « la confiance se prouve, elle ne se proclame pas ». Pivot vers le bénéfice :
> - **Titre** (option A « la maîtrise ») : « Enfin, un logement que vous comprenez. » + sous-titre
>   sur l'accompagnement dans la durée. (Alternatives B « compagnon » / C « colibri » fournies,
>   swap trivial de 2 lignes si l'utilisateur préfère.)
> - **Champ de saisie dans le hero** (`components/HeroSearch.tsx`, le « game-changer » n°1) :
>   placeholder qui fait défiler de vraies questions (`setInterval`, figé au focus/à la saisie),
>   envoi → `/helios?q=...` ; `HeliosIA.tsx` lit `?q=` (`useSearchParams`) et pré-remplit le
>   `ChatWidget` (`initialInput`) — l'utilisateur relit et envoie lui-même (principe « garde la
>   main » déjà en place, cf. devis). Testé bout en bout en navigateur : question saisie →
>   redirection → chat pré-rempli avec le texte exact.
> - **Les 3 pavés de réassurance supprimés**, condensés en une ligne fine sous les CTA :
>   « Gratuit · indépendant · vos données sous votre contrôle. » + lien discret **« Pourquoi c'est
>   gratuit ? » → /engagements** (prouver le modèle éco. plutôt que le marteler).
> - **Hiérarchie des CTA** : action primaire = le champ de saisie (essai sans engagement) ;
>   secondaire = « Créer mon espace » en outline plus léger (fini les 2 boutons de poids égal).
> - **Dégradé « lever de soleil » animé** (`.hero-sunrise` dans `index.css`, CSS pur, `prefers-
>   reduced-motion` respecté) : tons chauds de marque qui glissent lentement (18 s). Base assombrie
>   (primary/terra) pour garder le contraste du texte blanc (stop le plus clair #C05621 = 4,57:1
>   calculé, titre en grand = seuil 3:1) ; le jaune n'apparaît qu'en halo diffus côté droit
>   (derrière la mascotte, loin du texte). Vérifié desktop + mobile (zéro débordement, champ 16px
>   anti-zoom iOS). Build front OK.
> - **Non fait (choix assumé)** : le colibri SVG animé dans le hero suggéré en n°3 — le hero a déjà
>   la mascotte `helios-salute.png` (visage de marque établi) ; ajouter un 2ᵉ visuel l'aurait
>   chargé. L'esprit colibri reste montré via la section dédiée et la page `/colibri`.

> **KB étoffée — confort d'été & réglementation (27/07/2026)** — survol de la couverture existante
> (FAQ source 109 fiches + kb thématiques ~162 total) → deux vrais trous ciblés :
> - `kb/confort_ete.md` (8 fiches) : la base était très « chauffage/hiver », quasi rien sur la
>   **surchauffe estivale** (enjeu majeur avec les canicules). Méthode (protections solaires ext.
>   avant int., sur-ventilation nocturne, toiture, brasseur d'air avant clim), clim/PAC réversible,
>   déphasage des isolants denses, inertie, végétalisation. Chiffres = ordres de grandeur honnêtes.
> - `kb/reglementation.md` (8 fiches) : la base ne comptait qu'1-2 fiches réglementaires alors que
>   « ai-je le droit de louer / dois-je faire un audit / dois-je entretenir » sont très demandées.
>   Calendrier loi Climat (interdiction location G 2025 / F 2028 / E 2034), gel des loyers F/G,
>   audit énergétique obligatoire à la vente (F/G depuis 2023, E 2025, D 2034), validité + opposabilité
>   DPE (+ correction petits logements 2024), entretien obligatoire chaudière/PAC/clim/ramonage,
>   DTG/PPT copro. Échéances datées taguées `verif:date_sensible_27_07_2026` (candidat veille Phase 4).
> - Branché crawler (`agents_engine.SOURCES`) + `FAQ_SOURCES` (faq.py) + `rag._QR_SOURCES` (réponses
>   instantanées). Ingéré via `agents/run_agents.py crawl` (+16 fiches → ~178 au total).

> **VOSS — stockage solaire par volant béton (27/07/2026)** — fiche produit fournie par
> l'utilisateur (AD Solar ; techno réelle Energiestro, specs commerciales = HYPOTHÈSE de
> lancement : 10 kWh / 7 kWh utiles / rendement ~70 % / ~10 000 € posé / garantie 40 ans) :
> - `kb/voss.md` (7 fiches Q/R, `verif:hypothese_lancement`) : principe technique, argument 40 ans
>   (~0,10 €/kWh sur la durée), bilan carbone **avec la formulation prudente imposée par la fiche**
>   (« meilleur bilan carbone sur le cycle de vie matériaux + longévité + fin de vie », JAMAIS
>   « le plus écologique » — risque DGCCRF/loi Climat sur les allégations environnementales),
>   bémol du rendement 70 % assumé frontalement, condition béton bas-carbone (à confirmer
>   fabricant), comparatif honnête vs lithium (chacun gagne sur son terrain), profil cible.
> - **Correction de nom (info utilisateur : « Energisto » était une faute)** : le partenaire
>   s'appelle **Energiestro**, la techno **VOSS** — c'est le même produit que le « stockage
>   inertie » déjà présent. Harmonisé partout : `solar_engine.STORAGE_TECHS` (label « Volant
>   béton VOSS (Energiestro) », prix aligné 900→**1000 €/kWh** soit 10 000 €/10 kWh),
>   fiche historique de `kb/solutions.md` réécrite (bons chiffres + rendement), glossaire
>   (terme « Volant d'inertie (VOSS) », 41 termes). Ancienne fiche « Energisto » supprimée de
>   la base (doc + chunks) car le crawl upsert par titre l'aurait laissée en doublon.
> - Ingéré + vérifié réellement : FAQ publique **185 fiches**, question chat « c'est quoi le VOSS »
>   → réponse instantanée (score 0.775) avec les bons chiffres et la réserve « à confirmer au
>   lancement ». NB : les notes historiques de ce fichier mentionnant « Energisto » sont laissées
>   telles quelles (archives datées).

> **Back-office `/admin` — étape 1 (27/07/2026)** — décisions utilisateur : **identité visuelle
> propre** (pas de copie d'Eolia/Hydrolia) et **accès complet assumé** aux données (pas
> d'anonymisation des conversations).
> - **Auth** (migration `0015_admin_space`) : `users.is_admin` + `get_current_admin`.
>   `require_admin_access` accepte DEUX voies sur les mêmes routes : `X-Admin-Token` (scripts) ou
>   JWT d'un compte admin (interface) — évite la duplication de routes et le conflit de chemins
>   qu'aurait produit un second router monté sur le même préfixe.
> - **Instrumentation ajoutée dans la même migration** : `messages.rag_score` (meilleur score de
>   similarité au moment de la réponse), renseigné dans `chat.py` sur les deux chemins (instantané
>   et LLM). Sous `rag_score_threshold` = trou de la base de connaissances → alimente le compteur
>   « questions sans réponse » et, à l'étape 2, la liste détaillée.
> - **Backend** : `services/admin_stats.py` (agrégats lecture seule : foyers, activité, coût IA vs
>   plafonds, business, KB, alertes dérivées) et `services/admin_health.py` (sondes parallèles
>   Postgres/Ollama/PVGIS ; **Claude et Enedis ne sont PAS appelés** — un test consommerait des
>   crédits pour rien, on rapporte l'état de configuration). Routes : `/api/admin/{me,dashboard,
>   services,agents-log,partners,partners/{id}/activate|suspend}`.
> - **Frontend** : `/admin/*` monté AVANT le site public dans `App.tsx`, **hors** de sa mise en page
>   (ni Header ni Footer public). `components/admin/AdminLayout.tsx` (coquille sombre + `StatCard`
>   / `Section` / `useAdminData`) et `AdminRoute.tsx` (garde qui interroge `/api/admin/me` — le
>   serveur reste l'autorité, le droit admin n'est pas exposé dans le profil utilisateur).
>   4 pages : tableau de bord, partenaires (validation + mot de passe initial affiché une fois),
>   services, journal des agents.
> - **Identité propre vérifiée en navigateur** (computed styles, les captures étant indisponibles) :
>   fond `rgb(2,6,23)`, police système (pas Fraunces/Nunito), aucun header/footer public présent,
>   zéro débordement horizontal.
> - **Validé réellement** : tableau de bord avec vraies données (185 fiches, 11 sources, 2 comptes,
>   3 leads), services (0 en erreur, latences réelles), partenaires (2 actifs), journal des agents
>   (historique du crawler). Sécurité testée dans les 3 cas : sans auth → 403, compte NON admin →
>   403 (jeton forgé pour `test@helios.fr`), secret partagé → 200. Build front OK.
> - **Compte admin de dev** : `demo@helios.fr` promu via `is_admin = True` en base.
> - **Reste (étapes 2 et 3 du plan validé)** : supervision d'Helios (conversations, questions sans
>   réponse détaillées, coût par utilisateur), base de connaissances (fiches jamais citées /
>   les plus citées, lancer crawl+veille depuis l'UI), puis signalements, RGPD et journal des accès.

> **Back-office — étape 2 (27/07/2026) : supervision d'Helios + base de connaissances** —
> le module qui n'existe ni chez Eolia ni chez Hydrolia, et qui justifie le back-office.
> - `services/admin_supervision.py` : `liste_conversations` (filtre public/connecté, drapeau
>   `sans_reponse` par agrégat `MIN(rag_score)`), `detail_conversation` (échange complet avec
>   identité du foyer, voie de réponse, score, citations, coût, version de constitution),
>   `questions_sans_reponse` (**DISTINCT ON** pour rattacher à chaque réponse la question
>   utilisateur la plus proche), `base_connaissances_detail` (SQL brut avec
>   `jsonb_array_elements_text(chunks_used)` → fiches les plus mobilisées / jamais remontées),
>   `cout_par_utilisateur`.
> - **Vocabulaire volontairement exact** : `chunks_used` contient TOUTES les fiches remontées par
>   la recherche (top-k), pas seulement celles citées dans la réponse → l'UI dit « mobilisées » /
>   « jamais remontées », jamais « citées ».
> - **Lancement des agents depuis l'UI** : `POST /admin/agents/run?agent=crawl|veille` via
>   `BackgroundTasks` + session DB propre (`async_session`) — le crawler prend plusieurs minutes
>   (embeddings locaux), une exécution synchrone aurait expiré. Progression suivie dans
>   `agents_log`, erreurs journalisées. Vérifié : veille lancée → journal « 0 document périmé » ;
>   agent inconnu → 400.
> - **Frontend** : `AdminConversations.tsx` (liste + vue détaillée d'un échange) et
>   `AdminConnaissances.tsx` (questions sans réponse, fiches mobilisées, jamais remontées avec
>   filtre par source, boutons crawler/veille). Navigation portée à 6 entrées.
> - **Validé en navigateur avec de vraies données** : 23 conversations listées (identité affichée),
>   détail d'un échange connecté montrant « API · 0,0031 € · constitution v0.2 », 15 fiches les plus
>   mobilisées (top : cas_pratiques et pilotage à 5×), **137 fiches jamais remontées** — signal
>   immédiatement exploitable. Build front OK.
> - **Limite honnête affichée dans l'UI** : « questions sans réponse » est vide car `rag_score`
>   vient d'être introduit (anciens messages à NULL) ; le relevé démarre avec la mise en service.
> - **Reste (étape 3)** : signalements client (bouton « réponse fausse »), RGPD (export/suppression
>   depuis l'UI), journal des accès admin. Moins urgent tant qu'on n'est pas ouvert au public.

> **Back-office — étape 3 (27/07/2026) : signalements, RGPD, traçabilité** — migration
> `0016_moderation` (tables `message_reports` et `admin_access_log`).
> - **Signalements** : le foyer (ou un visiteur anonyme) signale une réponse via un bouton dans
>   le `ChatWidget`. Rend la constitution **vérifiable** au lieu de seulement affirmée.
>   Prérequis technique : `chat.py` émet désormais un événement `{"type":"message_id"}` en FIN de
>   flux (le message n'est enregistré qu'après le streaming, son id n'existait pas avant).
>   `POST /api/chat/signaler` (rate-limité 10/min, ouvert aux anonymes, vérifie que le message
>   existe et vient bien d'Helios). Revue admin : liste filtrable par statut + traitement
>   (« Corrigé » / « Ignorer ») avec note de suite donnée.
> - **RGPD admin** : recherche de foyers, export (portabilité) et suppression (droit à
>   l'effacement) — **réutilise `account.export_data` / `account.delete_account`** plutôt que de
>   dupliquer la logique. Garde-fous : un compte admin ne se supprime pas depuis là ; côté UI,
>   double confirmation dont la ressaisie exacte de l'email. L'export se télécharge en local
>   (aucun service tiers).
> - **Journal des accès** (`admin_access_log`) : contrepartie de l'accès complet assumé — chaque
>   lecture de conversation nominative et chaque export/suppression est tracé (`_tracer`).
>   La trace de suppression est écrite AVANT l'effacement, l'email n'étant plus lisible après.
>   Un accès par secret partagé est enregistré sous « secret_partagé ».
> - **Validé réellement, parcours complet** : question au chat → `message_id` reçu → signalement
>   anonyme accepté → motif invalide refusé (400) → signalement visible dans la file admin avec
>   la réponse incriminée, son score (0,688) et sa voie (kb). Export RGPD → 8 sections de données
>   → tracé dans le journal ; lecture de conversation → tracée aussi. Bouton « Signaler cette
>   réponse » confirmé présent dans le chat public après réponse. Build front OK.
> - **Back-office complet : 8 écrans** (tableau de bord, conversations, connaissances,
>   signalements, foyers & RGPD, partenaires, services, agents).

> **Correctif d'interprétation : « fiches jamais remontées » (27/07/2026)** — le back-office
> affichait « 137 fiches jamais remontées » et j'en avais fait « le signal le plus actionnable ».
> **C'était faux, vérifié après coup** : seulement 20 réponses ont jamais mobilisé des sources,
> soit 20 × `rag_top_k` (8) = **160 tirages au maximum pour 185 fiches** — il était
> mathématiquement impossible que la majorité remonte. C'est un artefact de volume, pas un
> défaut de contenu.
> - `admin_supervision.base_connaissances_detail` renvoie désormais un bloc `volume`
>   (réponses, tirages max, total fiches, `echantillon_suffisant` = au moins 3 tirages/fiche) ;
>   l'UI affiche un avertissement explicite tant que l'échantillon est insuffisant, au lieu de
>   laisser croire à un problème de rédaction.
> - **Métrique de remplacement, indépendante du trafic** : test d'AUTO-RÉCUPÉRATION — pour chaque
>   fiche, on pose sa propre question au moteur et on vérifie qu'elle se retrouve. Une fiche qui
>   ne se retrouve pas elle-même est introuvable en pratique, quel que soit l'usage. Script :
>   `scratchpad/test_recall.py` (185 embeddings réels via Ollama).

> **Test d'auto-récupération : résultats et correctifs (27/07/2026)** — 185 fiches testées
> (chacune interrogée avec sa propre question) :
> - **181/185 au rang 1, 0 introuvable** → base saine, bien indexée et bien formulée.
> - **4 reléguées**, toutes révélatrices de quasi-doublons. Le cas grave : deux fiches
>   **se contredisaient** sur batterie virtuelle vs physique (« souvent moins avantageuse
>   qu'annoncé » contre « fait mieux dans quasi tous les cas ») → selon celle qui remontait,
>   Helios donnait un conseil opposé. Sujet à enjeu commercial (MyLight partenaire).
> - **Arbitrage rendu par l'utilisateur** (position reprise telle quelle dans la fiche) : les deux
>   ont de vrais avantages ; la physique permet le **back-up** en coupure réseau, l'indépendance
>   vis-à-vis d'un opérateur et le rapport à « SON » énergie ; la virtuelle impose un fournisseur
>   alternatif, ce que beaucoup refusent ; et l'écart économique dépend de la **courbe de charge**
>   du foyer. → Helios simule, compare les deux à consommation égale, **et le client décide**.
>   Constat au passage : toutes les fiches existantes traitaient le sujet comme purement
>   financier — le back-up, la réticence fournisseur et l'autonomie n'étaient nulle part.
> - Vérifié avant d'écrire : `revolt_engine.compare_scenarios` compare DÉJÀ physique
>   (`simulate_pv_battery`) et virtuelle (`simulate_mylight`) à consommation réelle égale — la
>   fiche ne promet donc rien qui n'existe pas (seule la courbe Enedis réelle reste à brancher).
> - Doublon « recharge voiture » (FAQ + `solutions.md`) : **fusionné** (les conditions concrètes
>   de la version FAQ — véhicule présent en journée, 6 kWc minimum — ont été reversées dans
>   `solutions.md`) puis l'original retiré. Fiche orpheline supprimée en base (l'upsert par titre
>   ne supprime rien).
> - Réingéré et **vérifié en conditions réelles** : la question « batterie virtuelle ou physique »
>   renvoie désormais la réponse nuancée (score 0,781, réponse instantanée). Base : 184 fiches.

> **⚠️ CORRECTION DE NOMMAGE — « Revolt » → « autoconso » (27/07/2026)** — À RETENIR :
> **REVOLT est un logiciel de dimensionnement solaire TIERS** (payant, utilisé par de nombreux
> installateurs), qui **n'appartient pas à HELIOS**. Il avait été cité par l'utilisateur comme
> simple *repère de qualité* au moment de concevoir le simulateur ; le nom s'est propagé dans le
> code par erreur d'interprétation de ma part. Utiliser la marque d'un produit tiers pour une
> fonctionnalité maison était un risque réel de confusion. **Ne jamais réintroduire ce nom.**
> - Renommé partout en **`autoconso`** (descriptif : autoconsommation = PV + stockage + tarifs,
>   à consommation réelle). 19 fichiers modifiés, 6 renommés :
>   `models/autoconso.py` (`AutoconsoStudy`), `schemas/autoconso.py`, `services/autoconso_engine.py`,
>   `routers/autoconso.py` (préfixe `/api/autoconso`), `kb/autoconso.md` (source `autoconso`),
>   `components/AutoconsoPanel.tsx`. Plus `rag.build_autoconso_context`,
>   `config.autoconso_battery_efficiency`, `FAQ_SOURCES`, `_QR_SOURCES`, guides, glossaire, FAQ.
> - **Migration `0017_rename_autoconso`** : `revolt_studies` → `autoconso_studies` (+ index).
>   Les migrations historiques 0014/0015 gardent l'ancien nom — on ne réécrit jamais une
>   migration déjà appliquée ; la chaîne de révisions en dépend.
> - **Piège rencontré** : le remplacement automatique a inséré « simulateur d'autoconsommation »
>   (avec apostrophe) dans des chaînes JS en quotes simples → 10 erreurs TS. Corrigé en passant
>   ces chaînes en guillemets doubles. Vérifier ce motif après tout remplacement de masse.
> - **Vérifié réellement** : migration appliquée, backend importe, `tsc -b` OK, build front OK,
>   routes `/api/autoconso/{simulate,studies}` enregistrées, **les 2 simulations persistées sont
>   toujours lisibles après renommage de table**, 7 fiches réingérées sous `source=autoconso`
>   (les anciennes `source=revolt` purgées), FAQ à 184 fiches, chat retrouve la fiche (score 0,746).
>
> **Niveau de qualité visé** (étude REVOLT réelle fournie par l'utilisateur, 23 pages, client
> AD Solar 9 kWc) : dimensionnement + récupération Enedis, production/consommation horaire,
> répartition autonomie directe vs batterie virtuelle, profil projeté (VE, équipements),
> facture avant/après, économies N+1, **gains cumulés sur 25 ans**, comparatif d'offres,
> impact environnemental (temps de retour énergétique), analyse d'ensoleillement et d'ombrage 3D,
> simulation d'emprunt. Le simulateur HELIOS couvre aujourd'hui une partie de ce périmètre
> (production PVGIS, autoconso, batterie physique/virtuelle, tarifs) — l'écart restant est
> documenté ici comme cible, pas comme promesse.

> **Avatar animé d'Helios (05/08/2026)** — à partir des poses fournies par l'utilisateur
> (maquette « Avatar animé HELIOS »). L'avatar cesse d'être une vignette figée : il réagit à ce
> qui se passe réellement dans la conversation.
> - **Assets** : `frontend/public/brand/poses/{crossed,thumbsup,salute,hero}.png` — mêmes dessins
>   que les assets de marque existants mais **détourés au plus près et à fond transparent**
>   (150-350 Ko), et surtout **au VISAGE VIDE**. Les anciens `brand/helios-*.png` sont conservés
>   (encore utilisés par Vision / Qui sommes-nous / FicheMaison).
> - **`components/HeliosAvatar.tsx`** : compose la pose PNG + un calque SVG qui dessine yeux et
>   bouche. C'est ce qui permet 5 expressions (`calm/smile/happy/unsure/sad`) sans multiplier
>   les fichiers. **Les coordonnées du visage ont été MESURÉES sur les pixels** (remplissage par
>   diffusion depuis les bords pour isoler la zone fermée sous le casque), pas estimées à l'œil ;
>   la maquette d'origine était décalée de 1 à 2 points sur deux poses.
> - **Repère SVG carré** (`viewBox="0 0 100 100/ratio"`) et non un 100×100 étiré comme dans la
>   maquette : sinon les yeux ronds deviennent des ovales, différemment selon la pose. Même
>   logique pour l'épaisseur de la bouche, exprimée en unités du repère (≈ 2,9 % de la largeur =
>   le trait du dessin) plutôt qu'en pixels CSS figés — elle grossit avec l'avatar.
> - **7 états produit** : `repos` (bras croisés, respiration + clignements), `salutation`,
>   `reflexion` (points), `reponse` (hochement + ampoule), `nesaitpas` (main au casque, haussement
>   d'épaules, « ? »), `erreur` (affaissement, « ! »), `succes` (rebond). Les états transitoires
>   retombent seuls au repos ; la prop `replay` permet de rejouer le même état deux fois d'affilée
>   (les keyframes existent en variantes A/B — changer de nom d'animation est le seul moyen fiable
>   de forcer un rejeu).
> - **Keyframes dans `index.css`**, désactivées sous `prefers-reduced-motion` (les expressions,
>   elles, restent : elles ne bougent pas).
> - **Branchements** : `ChatWidget` (état piloté par le cycle réel du chat), hero d'accueil
>   (pose `hero`, salutation à l'arrivée), accueil d'un `/espace` sans fiche.
> - **Mise en page du chat refondue (retour utilisateur : « quel est l'avatar animé ? »)** — la
>   première version mettait l'avatar en vignette d'en-tête (56 px) plus une vignette figée
>   devant chaque bulle : personne ne voyait qu'il s'animait, et les deux bonshommes brouillaient
>   le message. Désormais **une colonne dédiée à gauche (260 px) avec Helios en 300 px**, nom et
>   fonction dessous, conversation à droite (`max-w-[920px]`) ; **les vignettes de bulles sont
>   supprimées**. Sous `md`, la colonne disparaît et Helios repasse en en-tête compact (62 px).
>   Dans la foulée : les états transitoires tiennent **1,2 s après le geste** (au lieu de 0,4 s)
>   — réglé en regardant l'avatar en grand, l'ampoule disparaissait avant d'être lue.
> - **Signal « je ne sais pas » : réel, pas mimé** — une réponse sans citation veut dire
>   qu'aucune fiche n'a dépassé `rag_score_threshold`, c'est-à-dire exactement ce que le
>   back-office compte en « questions sans réponse ». On l'affiche au client au lieu de simuler
>   l'assurance. Vérifié en conditions réelles : « recette de la tarte tatin » → `nesaitpas`,
>   « par quoi commencer pour isoler ma maison » → `reponse` (ampoule).
> - **Validé** : géométrie du visage recomposée hors navigateur sur les 4 poses (relecture
>   visuelle des 6 expressions), cycle complet observé en direct dans le vrai chat
>   (`réfléchit → a une réponse → repos`, puis `réfléchit → n'a pas la réponse → repos`),
>   hero d'accueil animé sans débordement horizontal, zéro erreur console, build front OK.

> **SEO — phase 1 : pré-rendu des fiches (5/08/2026)** — audit SEO complet publié en artefact.
> **Constat mesuré** (HTML réellement servi, 5 routes) : toutes renvoyaient le MÊME fichier de
> 2 134 octets, **zéro H1**, titre et description identiques → pour un robot sans exécution JS,
> le site entier était une page vide. 184 fiches rédigées, invisibles ; 8 URL sur ~240 possibles.
> - `frontend/scripts/prerender.mjs` : lit `kb/*.md` (mêmes sources que le crawler, même
>   expression régulière que `agents_engine._FAQ_RE` — **à garder synchronisés**) et génère
>   **184 pages**, une par fiche, sans exception (exclure une source aurait créé des liens
>   « Ouvrir cette fiche » menant à une coquille vide pour les moteurs).
>   Chaque page : titre = la question, description tirée de la réponse (coupée sur une frontière
>   de mot), balise canonique, **JSON-LD `FAQPage`** (affichage enrichi dans les résultats) et
>   le contenu visible dans le HTML. Lancé automatiquement par `npm run build`.
> - `frontend/src/lib/faqSlug.js` : **JavaScript simple et volontairement partagé** par le script
>   Node ET l'application TypeScript (`allowJs` activé). Une seule implémentation — deux copies
>   auraient divergé et fait pointer les liens internes vers des pages inexistantes. **Ne jamais
>   modifier cette fonction sans redirections** : elle détermine toutes les URL du site.
>   Le script échoue bruyamment en cas de collision de slug plutôt que d'écraser une fiche.
> - `pages/FaqDetail.tsx` (route `/faq/:slug`) + lien « Ouvrir cette fiche » depuis la liste :
>   c'est ce maillage interne qui rend les 180 pages découvrables. Chaque fiche renvoie vers
>   5 fiches de la même catégorie et vers le chat pré-rempli.
> - **Piège trouvé en testant, décisif** : `faq/<slug>/index.html` n'était servi qu'avec une barre
>   oblique finale (vérifié : sans elle, repli sur la coquille vide). Basculé en fichiers plats
>   `faq/<slug>.html` + `try_files $uri $uri.html $uri/ /index.html` dans `deploy/nginx.conf` —
>   servi directement, sans redirection, l'URL correspondant exactement à la canonique.
>   **Sans cette directive nginx, tout le pré-rendu est inopérant.**
> - **Vérifié réellement** : 184 pages générées, JSON-LD valide (parsé), titres uniques, et test
>   HTTP de bout en bout avec un serveur reproduisant `try_files` → fiches servies avec leur
>   contenu (4 000+ octets, H1 présent), autres routes en repli SPA. Contrôle croisé final :
>   les 184 questions de la base produisent 184 pages existantes — **zéro lien mort**. Rendu
>   React et navigation entre fiches liées vérifiés en navigateur.
> - **Risque à connaître** : le pré-rendu lit `kb/*.md` alors que l'application lit la base via
>   `/api/faq`. Si une fiche est modifiée dans `kb/` sans relancer le crawler, le libellé diffère
>   → slug différent → lien mort. Toujours réingérer après modification d'une fiche.
>
> **SEO — phase 2 : plan de site et robots.txt (5/08/2026)** — générés par le même script, qui
> connaît déjà toutes les URL.
> - `sitemap.xml` : **213 URL** (15 pages fixes + 184 fiches + 14 guides), avec `lastmod` tiré de
>   la date de modification réelle des sources. Pas de `priority` ni `changefreq` : Google les
>   ignore, mieux vaut ne pas émettre de faux signaux.
> - `robots.txt` : zones privées interdites, plan de site déclaré.
> - **Les pages fixes sont énumérées à la main** (`PAGES_FIXES`) plutôt que déduites du routeur :
>   l'espace client et le back-office ne doivent jamais entrer dans le plan de site, et une liste
>   explicite rend l'exclusion vérifiable.
> - **Piège trouvé et corrigé** : `Disallow` fonctionne par PRÉFIXE — `/partenaire` bloquait aussi
>   `/partenaires`, l'annuaire public, pourtant déclaré dans le plan de site. Corrigé en
>   `/partenaire$` (fin d'URL, reconnu par Google). **Vérifier ce piège à chaque nouvelle règle.**
> - **Vérifié** : XML parsé et valide, 0 doublon, 0 fuite d'URL privée, chaque fiche du plan de
>   site correspond à une page réellement générée, et **0 page du plan de site bloquée par le
>   robots.txt** (contrôle croisé automatisé des deux fichiers).
> - `HELIOS_SITE_URL` ajouté à `.env.example` : **à définir avant le build de production**, une
>   canonique pointant vers un mauvais domaine ferait perdre l'indexation de tout le site.
>
>
> **SEO — phase 3 : hypothèses économiques périmées (5/08/2026)** — le simulateur surestimait
> lourdement la rentabilité du solaire. Deux valeurs corrigées dans `config.py`, toutes deux
> vérifiées (recherche web + base de connaissances interne, concordantes) :
> - `solar_prix_revente_eur_kwh` : **0,13 → 0,011 €/kWh**. L'arrêté du 1er juin 2026 (réforme S21)
>   a ramené le rachat du surplus résidentiel à 1,1 c€/kWh et supprimé la prime à
>   l'autoconsommation. L'ancienne valeur surestimait cette ligne d'un facteur 12.
> - `solar_prix_achat_eur_kwh` : **0,25 → 0,20 €/kWh**. TRV option Base au 1er août 2026 :
>   0,2001 € jusqu'à 6 kVA, 0,1985 € dès 9 kVA. La base de connaissances disait déjà ~19 c€ —
>   la config la contredisait depuis le début.
> - **Effet mesuré** (6 kWc, 4 500 kWh consommés, avec pilotage) : économie annuelle
>   **1 398 → 730 €/an**, temps de retour **10,7 → 20,5 ans**. Les chiffres affichés par le
>   simulateur changent donc fortement — dans le sens de l'honnêteté.
> - **TROISIÈME valeur périmée repérée, laissée à l'arbitrage de l'utilisateur** :
>   `solar_cout_par_kwc_eur = 2500` alors que ses PROPRES devis AD Solar donnent
>   **1 450–1 800 €/kWc** (3 kWc ~2 170, 6 kWc ~1 700, 9 kWc ~1 600, 13 kWc ~1 270) et que le
>   marché 2026 annonce 1 800–2 200. Deux défauts : valeur trop haute, et **taux unique ignorant
>   l'effet d'échelle** alors que le simulateur compare justement 3/6/9 kWc. Avec 1 600 €/kWc,
>   le retour d'un 9 kWc passe de 23,1 à 14,8 ans — cohérent avec les 12-18 ans du marché.
>   Non modifié : c'est la réalité commerciale de l'utilisateur, à lui de fixer la valeur.
>
> - **Coût d'installation corrigé** (arbitrage utilisateur, option « grille par palier ») :
>   `solar_cout_par_kwc_eur = 2500` (taux unique) remplacé par `solar_cout_paliers_kwc`
>   = 3 kWc→2 100, 6→1 750, 9→1 600, 12→1 400 €/kWc, avec interpolation linéaire
>   (`solar_engine.cout_par_kwc`) et maintien du palier extrême au-delà (pas d'extrapolation :
>   elle produirait vite des prix irréalistes). Calé sur les **devis réels AD Solar** :
>   6 kWc → 10 500 € (prix exact du devis), 9 kWc → 14 400 € (devis 14 500 €).
>   Un taux unique faussait la comparaison 3/6/9 kWc que produit justement le simulateur.
> - **Résultat final vérifié** (6 kWc, 4 500 kWh, avec pilotage) : 730 €/an, retour **14,4 ans** —
>   cohérent avec les 12-18 ans annoncés par le marché, là où l'ancienne config donnait 10,7 ans
>   (trop optimiste) et la correction des seuls tarifs 20,5 ans (trop pessimiste).
>
> **SEO — phase 4 : titres et descriptions (5/08/2026)**
> - **Génération automatique améliorée** (profite aux 184 fiches) : titre ≤ 60 caractères,
>   coupe sur une frontière de MOT, et **abandon du suffixe « — HELIOS » quand la question est
>   longue** — mieux vaut perdre la marque que tronquer la phrase. Résultat mesuré :
>   **183/184 titres dans la limite contre 67 avant**, plus aucune coupe en plein mot.
> - **Curation manuelle** : `seo_titre` / `seo_desc` peuvent être ajoutés aux métadonnées d'une
>   fiche pour écrire titre et description à la main. **15 fiches à fort enjeu curées** (celles du
>   tableau de mots-clés de l'audit), titres de 45-51 caractères avec le mot-clé en tête.
> - **Séparation propre vérifiée** : le crawler Python ne retient que `cat`/`tags`/`verif` — les
>   métadonnées SEO restent dans le Markdown, lues par le seul script de pré-rendu. Aucune
>   réingestion nécessaire, aucun risque de pollution de la base vectorielle.
> - Descriptions : **184/184 uniques**, 150 caractères en moyenne, toutes ≤ 160.
>
>
> **SEO — phase 5 : pages chapeau (5/08/2026)** — 5 domaines : `/aides`, `/solaire`,
> `/isolation`, `/reglementation`, `/eau` (cette dernière ajoutée à la demande de l'utilisateur).
> - **Contenu éditorial dans `src/data/piliers.json`** (et non en TSX) : c'est la SEULE source,
>   lue à la fois par les pages React et par le pré-rendu — la version servie aux moteurs dit
>   donc exactement la même chose que la page. Un fichier TS aurait dû être analysé par
>   expression régulière depuis le script Node, ce qui aurait été fragile.
> - `components/FichesLiees.tsx` : bloc réutilisable listant les fiches d'un groupe de
>   catégories. **Choix important** : composant réutilisable plutôt que gabarit rigide, ce qui
>   permet à `/eau` de garder sa page sur mesure (partenaire Hydrolia, « pour qui », CTA) tout
>   en gagnant ses 15 fiches liées. `piliers.json` porte un drapeau `pageDediee` pour que la
>   route générique ne soit pas créée en double.
> - **Boucle de maillage fermée** : chapeau → fiches du groupe, fiche → son chapeau
>   (« Sujet : … » sous le titre) + 5 fiches voisines, et **colonne « Sujets » ajoutée au pied
>   de page** — sans lien entrant, un moteur ne découvre pas ces pages.
> - Pré-rendu : `/aides.html`, `/solaire.html`… servis par `try_files $uri $uri.html`, avec
>   titre, description, canonique et contenu visible. Plan de site : **217 URL**.
> - **Vérifié en navigateur** : `/solaire` affiche l'éditorial + **45 fiches** liées
>   (photovoltaique 15 + stockage 23 + autoconso 7), `/eau` garde sa page riche + 15 fiches,
>   et une fiche renvoie bien vers son chapeau. Titres des chapeaux : 43-48 caractères.
>
>
> **SEO — phase 6 : vigilance et pages locales (5/08/2026)** — dernière phase du plan.
> - `kb/vigilance.md` (**8 fiches**) : démarchage, devis gonflés, « travaux à 1 euro », faux RGE,
>   crédit affecté déguisé, urgence artificielle, recours. **C'est le territoire qu'une plateforme
>   vivant de la revente de contacts ne peut pas revendiquer sans se contredire** — Helios le peut.
>   Faits juridiques vérifiés par recherche web : **loi n° 2025-594 du 30 juin 2025** interdisant le
>   démarchage non sollicité en rénovation énergétique (téléphone, SMS, mail, réseaux sociaux),
>   contrat signé après sollicitation interdite **nul de plein droit**, rétractation 14 jours sans
>   motif ni frais, interdiction d'exécuter ou d'encaisser avant la fin du délai, amendes jusqu'à
>   75 000 € / 375 000 €. Chaque fiche rappelle qu'elle informe sans remplacer un conseil juridique.
>   Chapeau `/vigilance` associé. Retrieval vérifié sur 4 questions d'inquiétude réalistes :
>   la bonne fiche remonte en tête à chaque fois.
> - **Pages locales** `/solaire/{ville}` (**12 villes**) : `src/data/villes.json` contient des
>   productions PVGIS **réellement calculées** par ville (script `scratchpad/calc_villes.py`,
>   36 appels PVGIS, exécuté UNE fois et versionné — le build reste hors ligne et reproductible).
> - **Garde-fou anti-« pages satellites »** : des pages géographiques dupliquées sont sanctionnées
>   par les moteurs. Ici l'écart de production est de **×1,50** entre Lille (6 349 kWh) et
>   Marseille (9 546 kWh) pour 6 kWc, et chaque page porte en plus le conseil lié à sa **zone
>   climatique** (H1 isolation d'abord / H2 ventilation / H3 confort d'été). Le contenu est donc
>   authentiquement différent, pas décliné. L'écart est affiché par le script comme contrôle.
> - Honnêteté affichée sur chaque page : chiffres pour une toiture plein sud à 30° sans ombrage,
>   « votre toiture diffère forcément » + renvoi au simulateur pour le cas réel.
> - **Plan de site : 238 URL** (contre 8 au départ de l'audit).
> - Vérifié : pages générées avec titre/description/canonique propres à chaque ville, rendu React
>   confirmé en navigateur sur `/solaire/marseille` et `/vigilance`.

## Commandes
- Front : `cd frontend && npm install && npm run dev` (build : `npm run build`)
- API : `cd api && pip install -r requirements.txt && uvicorn app.main:app --reload`
- BDD (avec Docker) : `docker compose up -d postgres` puis `cd api && alembic upgrade head`
- Ingestion FAQ (nécessite Ollama + pgvector) : `api/.venv/Scripts/python.exe agents/ingest.py`
- Ollama local : `ollama pull bge-m3 && ollama pull llama3.2:3b` (déjà fait sur cette machine, service tourne sur :11434)
- Mode connecté / API Claude : renseigner `LLM_API_KEY` dans `.env` (vide par défaut → tout reste en local, « mode simplifié »). Modèle par défaut `claude-haiku-4-5-20251001` (cf. `config.py`).

## Remote
https://github.com/stf3001/helios.git

## Simulateur « maison + équipements » (`/simulateur-solaire`)
- Moteur horaire déterministe : `simu_conso` (courbe par couches), `simu_pv` (une série PVGIS pour 1 kWc, mise en cache, coordonnées sur grille), `simu_engine` (autoconso, batteries, écrêtage 6 kVA, 25 ans), `simu_options` (3 options + prochaine étape).
- Deux invariants tenus par `api/tests/` : les bilans se ferment, et la prochaine étape ne contredit jamais la recommandation. Ne pas les assouplir.
- Toutes les hypothèses sont dans `config.py` sous `simu_*`, chacune avec son statut, et remontent à l'écran dans « Hypothèses et méthode ».
- `/api/simulateur/calcul` et `/options` sont publics : rien n'est enregistré pour un anonyme, et seule la commune sort dans l'URL de partage.
- `/api/solar/*` et `/api/autoconso/*` sont remplacés dans le parcours mais restent en place.
