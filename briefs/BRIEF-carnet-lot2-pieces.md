# Brief Claude Code — Carnet de maison, lot 2 : les pièces et leurs émetteurs

## Contexte (à lire avant tout)

Prérequis : **lot 1 validé** (équipements et travaux en place).

Décision de Stéphane (20/10/2026) : Hélios doit connaître la maison **pièce par pièce** (radiateurs, splits, photos), pour quatre usages à venir : dimensionner une PAC ou une clim, affiner le pré-audit, l'inventaire pour l'assurance, les rendus visuels. **Saisie déclarative dans l'espace gratuit ; la lecture des photos viendra avec Super Hélios.**

Ce lot pose la saisie et un résumé calculé. **Il ne modifie aucun moteur de calcul** : le pré-audit et le dimensionnement utiliseront ces données dans un lot ultérieur.

Fichiers concernés (à confirmer dans ton plan) :
- `api/app/models/piece.py` (nouveau : `Piece`, `Emetteur`), `api/app/models/house_document.py` (colonne `piece_id`)
- `api/alembic/versions/0025_pieces_emetteurs.py`
- `api/app/schemas/piece.py`, `api/app/routers/pieces.py`, `api/app/routers/documents.py`
- `api/app/services/pieces.py` (nouveau, fonctions pures)
- `frontend/src/components/carnet/` (nouveaux composants), `frontend/src/pages/Espace.tsx`, `frontend/src/components/fiche/HouseDocuments.tsx`
- `api/tests/test_pieces.py`, `TODO.md`

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Statut des données | Tout est **déclaré**. Les totaux et les écarts sont **calculés**. |
| Photos de pièce | **Une photo par pièce**, rangée dans `house_documents` (type `photo`) avec `piece_id`. Elle **ne compte pas** dans la limite des 6 documents, qui ne s'applique qu'aux documents sans pièce. Stockée seulement, jamais analysée dans ce lot. |
| Limites | 25 pièces par maison, 10 lignes d'émetteurs par pièce. |
| Fiche existante | **Inchangée.** `surface_habitable` et `clim_nb_pieces` ne sont jamais corrigés automatiquement ; un écart est seulement signalé. |
| Lien avec le lot 1 | Un émetteur peut être relié à l'équipement qui le produit (les radiateurs à eau à la chaudière ou à la PAC, les unités intérieures au multisplit). Facultatif. |

## Méthode de travail

- Lire le débrief du lot 1, `models/house_document.py`, `routers/documents.py`, `components/fiche/HouseDocuments.tsx`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (maison vide ; maison de 6 pièces avec émetteurs et deux photos ; vue mobile 375 px). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot2.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Les modèles et la migration

**`Piece`** (table `pieces`) : `id`, `house_id` (cascade), `nom` (ex. « Chambre 2 », obligatoire), `type` (`sejour`, `cuisine`, `chambre`, `salle_de_bain`, `wc`, `bureau`, `entree`, `buanderie`, `garage`, `veranda`, `combles_amenages`, `autre`), `niveau` (int, 0 = rez-de-chaussée, -1 = sous-sol), `surface_m2` (optionnel), `chauffee` (bool, défaut vrai), `orientation` (`N`, `NE`, `E`, `SE`, `S`, `SO`, `O`, `NO`, optionnel), `ordre` (int), `note`.

**`Emetteur`** (table `emetteurs`) : `id`, `piece_id` (cascade), `type` (`radiateur_eau`, `convecteur`, `panneau_rayonnant`, `radiateur_inertie`, `seche_serviettes`, `plancher_chauffant_eau`, `plancher_chauffant_elec`, `unite_interieure_clim`, `poele_bois`, `poele_granules`, `cheminee`, `autre`), `nombre` (≥ 1), `puissance_w` (par unité, optionnel), `robinet_thermostatique` (bool, seulement pour `radiateur_eau`), `programmable` (bool, optionnel), `equipement_id` (FK `equipements.id`, optionnel, `SET NULL`), `note`.

**`house_documents.piece_id`** : FK `pieces.id`, optionnelle, `SET NULL` à la suppression de la pièce (la photo reste dans les papiers).

Migration `0025`, réversible.

## 2. Le résumé calculé, en fonctions pures

`api/app/services/pieces.py` → `resume_pieces(house, pieces, emetteurs)` :

- nombre de pièces, dont chauffées ;
- surface déclarée totale, et **écart avec `surface_habitable`** s'il dépasse 15 % (« La somme de vos pièces fait 92 m², votre fiche indique 110 m² ») ;
- émetteurs agrégés par type (nombre total, puissance totale quand toutes les puissances sont connues, sinon `null`) ;
- pièces chauffées **sans émetteur** (liste des noms) ;
- nombre de pièces avec une unité intérieure de clim, et écart avec `clim_nb_pieces` s'il existe ;
- chaque valeur porte son statut (`declare` ou `calcule`).

Aucun accès à la base dans ce module.

## 3. L'API

- `GET/POST /houses/me/pieces`, `PATCH/DELETE /houses/me/pieces/{id}` ; les émetteurs se créent, modifient et suppriment sous leur pièce (`/houses/me/pieces/{id}/emetteurs`).
- `POST /houses/me/pieces/demarrage` : crée en une fois les pièces courantes à partir d'une liste envoyée par l'écran (ex. séjour, cuisine, 3 chambres, salle de bain, WC). Refusé si la maison a déjà des pièces.
- `GET /houses/me/pieces/resume` : sortie de `resume_pieces`.
- Photo : l'envoi existant de document accepte un `piece_id` optionnel ; avec un `piece_id`, le type est forcé à `photo`, la limite des 6 ne s'applique pas, mais une seconde photo pour la même pièce remplace la première (ancien fichier supprimé du disque).
- Contrôles d'accès sur le modèle de `documents.py` ; un émetteur ne peut viser qu'un équipement de la même maison.

## 4. L'écran

Dans l'onglet « Ma maison », un bloc **« Mes pièces »**, sous les équipements :

- Maison sans pièce : un démarrage rapide (« Combien de chambres ? Une salle de bain ou deux ? ») qui appelle `/demarrage`.
- Une ligne par pièce : nom, surface, niveau, vignette de la photo, émetteurs en une phrase (« 2 radiateurs à eau, robinets thermostatiques »). Dépliée : édition de la pièce, de ses émetteurs, ajout ou remplacement de la photo.
- En tête du bloc, le résumé : nombre de pièces, surface déclarée, émetteurs par type, et les écarts signalés avec leur statut. Une pièce chauffée sans émetteur est signalée doucement (« Aucun émetteur indiqué »).
- Dans « Papiers », les photos de pièce sont regroupées à part (« Photos des pièces ») et ne comptent pas dans le compteur « x / 6 ».
- Charte « Carnet de maison », mobile d'abord.

## 5. Tests

- `resume_pieces` : surface totale et écart à 15 % (14 % sans signal, 16 % avec) ; puissance totale `null` si une puissance manque ; pièce chauffée sans émetteur détectée ; écart clim.
- Photos : une photo de pièce ne fait pas échouer l'envoi quand 6 documents existent déjà ; une seconde photo remplace la première ; supprimer la pièce garde la photo dans les papiers.
- Suppression d'une pièce : ses émetteurs partent avec elle.
- Tests existants verts, build front vert.

## 6. TODO.md

Ligne « Carnet, lot 2 » cochée après vérification à l'écran. Ajouter en point ouvert : **brancher les pièces et émetteurs dans le pré-audit et le dimensionnement PAC/clim** (lot à venir, après validation de Stéphane sur les règles de calcul).

---

## À ne pas faire

- **Aucune nouvelle dépendance.**
- Ne modifier ni le moteur de pré-audit, ni le simulateur, ni le score de complétude de la fiche.
- Ne pas corriger la fiche à partir des pièces.
- Pas d'analyse d'image, pas d'appel au LLM sur les photos.
- Pas de calcul de déperditions, de puissance nécessaire ni de recommandation d'émetteur.
- Pas d'inventaire des biens (meubles, objets) : c'est l'inventaire assurance de Super Hélios.
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Une maison se décrit en moins de deux minutes grâce au démarrage rapide, puis s'affine pièce par pièce.
2. Chaque pièce porte ses émetteurs et une photo ; les photos de pièce ne bloquent jamais les autres documents.
3. Le résumé signale les écarts avec la fiche sans rien corriger.
4. Tests et build verts, captures jointes, débrief écrit.
