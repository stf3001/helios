# Brief Claude Code — Finitions, lot 1 : en-tête, limite de documents, potentiel hydrique, jardin d'hiver

## Contexte (à lire avant tout)

La phase 1 du carnet est finie. Ce lot règle quatre points ouverts de `TODO.md`, indépendants entre eux : **46** (l'en-tête déborde), **49** (limite de 6 documents), **13** (page `/potentiel-hydrique` sur une table climatique inventée), **51** (fiche jardin d'hiver manquante). Un commit par point, dans cet ordre.

Ne sont **pas** dans ce lot : `kb/securite_incendie.md` (non commité, attend la relecture de Stéphane : n'y pas toucher), la photo du héros (point 21), la capture PVGIS (point 53).

## Décisions (déjà tranchées, à appliquer telles quelles)

| Point | Décision |
|---|---|
| 46 | La navigation publique se replie en menu (le même que sur mobile) **en dessous de 1280 px**. Aucun lien retiré. |
| 49 | La limite passe de **6 à 50 documents** par maison, avec un **plafond total de 250 Mo** par maison ; 10 Mo par fichier, inchangé. Les photos de pièce restent hors compte. Raison : un carnet accumule chaque année attestations d'entretien, factures et pièces « Avant d'acheter ». |
| 13 | **Retirer** la page `/potentiel-hydrique` : la route redirige vers `/simulateur-solaire` (la machine à eau y est calculée avec PVGIS), le lien « Potentiel hydrique » de l'espace disparaît. Le chat **cesse d'injecter** la dernière étude hydrique (`build_water_context`) : elle repose sur la table inventée (point 14). Les études stockées ne sont pas supprimées. |
| 51 | Ajouter la fiche `kb/jardin_hiver.md`, **fournie telle quelle** dans `briefs/KB-jardin-hiver.md` (la recopier sans la modifier), la déclarer dans `agents_engine.SOURCES`, la réingérer. Le modèle de projet « Jardin d'hiver » passe à `outil: "aucun"` : l'écran du projet affiche « Pas de calculateur pour ce projet : les fiches ci-dessous » à la place du bouton de calcul. |

## Méthode de travail

- Lire `TODO.md` (points 13, 14, 46, 49, 51), le débrief du lot 9, `components/layout/` (en-tête), `routers/documents.py`, `components/fiche/HouseDocuments.tsx`, `pages/PotentielHydrique.tsx`, `routers/water.py`, `routers/chat.py`, `services/rag.py`, `api/data/projets/modeles.json`, `agents_engine.SOURCES`.
- Plan court, un commit par point, message en français.
- À la fin : s'arrêter, résumer, captures (en-tête à 1024, 1100, 1280 et 1440 px ; compteur de documents ; projet jardin d'hiver). **Attendre la validation de Stéphane.**
- Débrief court `debriefs/AAAA-MM-JJ-finitions-1.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. En-tête (point 46)

- Repli en menu sous 1280 px, sur toutes les pages publiques et sur l'espace.
- Vérifier `scrollWidth <= clientWidth` à 1024, 1100, 1280, 1440 et 375 px.

## 2. Documents (point 49)

- `MAX_DOCUMENTS_PAR_MAISON = 50` et nouveau `MAX_OCTETS_PAR_MAISON = 250 * 1024 * 1024` (somme des `size` hors photos de pièce), avec un message clair quand l'un ou l'autre est atteint.
- La constante du front suit (texte « x / 50 », mention du plafond total).
- Tests : 50ᵉ document accepté, 51ᵉ refusé ; dépassement du plafond total refusé ; photos de pièce toujours hors compte.

## 3. Potentiel hydrique (point 13)

- Route `/potentiel-hydrique` → redirection vers `/simulateur-solaire` ; page et lien retirés.
- Endpoint `/water/*` : le retirer **s'il n'est appelé par rien d'autre** (le vérifier et le dire dans le résumé) ; sinon le laisser et le noter.
- `chat.py` / `rag.py` : ne plus charger ni envoyer l'étude hydrique au modèle.
- Mettre à jour le point 13 (coché) ; le point 14 reste ouvert (c'est Hydrolia qui doit corriger sa table).
- Tests : redirection, absence de la clé d'étude hydrique dans le contexte du chat.

## 4. Jardin d'hiver (point 51)

- Recopier `briefs/KB-jardin-hiver.md` en `kb/jardin_hiver.md` à l'identique, déclarer la source, réingérer.
- `modeles.json` : `outil: "aucun"` pour `jardin-hiver` ; le code des projets accepte cette valeur (pas de bouton de calcul, pas de `lier-etude`).
- Vérifier que le modèle est désormais servi aux maisons (et masqué aux appartements).
- Tests : modèle servi quand la fiche existe ; `lier-etude` refusé proprement pour `outil: "aucun"`.

## 5. TODO.md

Cocher 13, 46, 49 et 51 après vérification, chacun avec son commit. Ajouter en point ouvert : **relire `kb/jardin_hiver.md`** (toutes ses questions sont `verif: a_verifier`).

---

## À ne pas faire

- Ne pas toucher à `kb/securite_incendie.md`.
- Ne pas modifier le texte de la fiche jardin d'hiver.
- Ne supprimer aucune étude stockée ni aucune donnée d'Hydrolia.
- Ne retirer aucun lien de la navigation.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Plus aucun débordement d'en-tête, de 375 à 1440 px.
2. Un foyer peut ranger 50 documents (250 Mo au total), messages clairs aux limites.
3. Plus aucune page ni réponse du chat ne s'appuie sur la table climatique inventée.
4. Le projet « Jardin d'hiver » s'affiche, sans calculateur, avec ses fiches.
5. Tests et build verts, captures jointes, débrief écrit.
