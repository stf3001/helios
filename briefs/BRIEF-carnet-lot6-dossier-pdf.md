# Brief Claude Code — Carnet de maison, lot 6 : le dossier de la maison en PDF

## Contexte (à lire avant tout)

Prérequis : **lots 1, 3 et 4 validés** ; le lot 2 (pièces) est inclus s'il est en place.

Décisions de Stéphane (20/10/2026) :

- le **PDF du dossier de la maison est gratuit** : le foyer repart toujours avec ses données ;
- la page partagée et le transfert à l'acquéreur viendront avec Super Hélios (pas ici) ;
- **contenu conforme au carnet d'information du logement (CIL), sans statut d'opérateur** : le dossier reprend les rubriques attendues, sans prétendre valoir carnet officiel ni attestation.

Le pré-audit a déjà son PDF (`services/pdf_audit.py`, fpdf2, polices du site embarquées). Ce lot crée un second document, **sans changer le rendu du pré-audit**.

Fichiers concernés (à confirmer dans ton plan) :
- `api/app/services/pdf_dossier.py` (nouveau)
- éventuellement `api/app/services/pdf_commun.py` (polices, couleurs, en-têtes), **seulement** si l'extraction ne change rien aux PDF de pré-audit
- `api/app/routers/houses.py` ou un nouveau routeur `dossier.py`
- `frontend/src/pages/Espace.tsx` (onglet « Papiers » ou « Ma maison »)
- `api/tests/test_pdf_dossier.py`, `TODO.md`

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Titre | « Dossier de la maison » |
| Mention en pied de première page | « Ce dossier rassemble les informations déclarées par son propriétaire dans Hélios. Il suit les rubriques d'un carnet d'information du logement, mais ne constitue ni ce carnet au sens de la loi, ni une attestation. » **À recopier telle quelle, puis à faire relire par Stéphane** (signalé dans le résumé). |
| Statut des données | Chaque valeur porte une marque discrète : déclaré, justifié (document joint), supposé, calculé. Une légende en première page. |
| Choix du foyer | Avant l'export, le foyer coche les sections à inclure (toutes cochées par défaut). Les numéros de série sont **exclus par défaut**, avec une case pour les inclure. |
| Documents | Le dossier **liste** les documents de la maison (type, date d'ajout), sans les joindre. |
| Stockage | PDF généré à la demande et renvoyé directement ; pas de conservation sur le disque. |

## Méthode de travail

- Lire `services/pdf_audit.py` (polices, repli Helvetica, `_s()`, logo), les débriefs des lots 1 à 4.
- Plan court, un commit par étape, message en français.
- Juger le rendu **à l'œil**, sur les PDF rendus en image de trois maisons : une maison avec seulement un code postal, une maison moyenne, une maison complète (fiche, 8 équipements, 2 chantiers, 6 pièces, 15 entrées de journal).
- À la fin : s'arrêter, résumer, joindre les trois rendus. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot6.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Le contenu, dans cet ordre

1. **Le logement** : code postal, type, statut, période de construction, surface, niveaux, résidence principale.
2. **L'enveloppe** : isolation (combles, murs, plancher, avec années), menuiseries, ventilation, DPE (lettre et année).
3. **Les équipements** : un tableau par catégorie (type, marque et modèle, pose, âge, garantie fabricant, contrat d'entretien) ; anciens équipements à part.
4. **Les pièces et leurs émetteurs** (si le lot 2 existe).
5. **Les travaux et les garanties** : chaque chantier (nature, entreprise, réception, garanties et leur échéance), avec la mention de vérification du lot 1.
6. **L'entretien** : prochaines échéances (statut, obligation ou conseil), puis le journal des 24 derniers mois et toute entrée justifiée plus ancienne.
7. **L'énergie déclarée** : consommations, puissance souscrite, option tarifaire. **Jamais le PDL.**
8. **Les documents disponibles** : liste.

Une section sans donnée affiche une ligne « Non renseigné », sauf si le foyer l'a décochée (elle disparaît). Pied de page : date de génération, numéro de page, « Hélios ».

Le PDF **met en forme** ce que les moteurs ont calculé : aucun chiffre recalculé dans `pdf_dossier.py`, pas même une somme.

## 2. L'API

`POST /houses/me/dossier` avec la liste des sections et l'option numéros de série → renvoie le PDF (`application/pdf`, nom de fichier `dossier-maison-AAAA-MM-JJ.pdf`). Limité au foyer connecté. Limite de fréquence raisonnable (comme les autres routes coûteuses, `slowapi` est déjà là).

## 3. L'écran

Un bouton **« Télécharger le dossier de ma maison »** dans l'onglet « Papiers », qui ouvre un petit panneau : les sections à cocher, la case des numéros de série, le bouton d'export. Une phrase au-dessus : « Utile pour une vente, une location, un artisan ou votre assureur. » Charte « Carnet de maison ».

## 4. Tests

- Les trois maisons génèrent un PDF sans erreur ; la maison minimale tient en une ou deux pages.
- Sans police embarquée (repli Helvetica), le PDF se génère encore (« € », « œ » remplacés).
- Aucune variable `{…}` non remplie, aucun « None » visible (test sur le texte extrait avec `pypdf`).
- Le PDL n'apparaît jamais ; les numéros de série seulement si l'option est cochée.
- Une section décochée est absente.
- **Les PDF de pré-audit existants sont identiques** avant et après (même nombre de pages, même texte extrait) si un module commun a été extrait.
- Tests existants verts, build front vert.

## 5. TODO.md

Ligne « Carnet, lot 6 » cochée après vérification des rendus. Point ouvert : **faire relire la mention de pied de page par Stéphane**, et confirmer la liste des rubriques du CIL sur le texte officiel avant toute communication sur la conformité.

---

## À ne pas faire

- **Aucune nouvelle dépendance** : fpdf2 et pypdf sont déjà là.
- Ne jamais écrire « conforme », « certifié », « officiel » ni « carnet d'information du logement » comme titre du document.
- Ne pas joindre les fichiers des documents au PDF.
- Ne pas changer le rendu des PDF de pré-audit.
- Pas de page web partagée, pas de lien public, pas de transfert de compte (Super Hélios, plus tard).
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le foyer télécharge en deux clics un dossier lisible, choisit ses sections, et les numéros de série sont exclus par défaut.
2. Chaque valeur indique s'il s'agit d'une donnée déclarée, justifiée, supposée ou calculée.
3. La mention de pied de page est présente telle quelle et signalée pour relecture.
4. Les PDF de pré-audit sont inchangés.
5. Tests et build verts, trois rendus joints, débrief écrit.
