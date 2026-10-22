# Brief Claude Code — Pré-audit, lot 7 : la consommation de fioul, de gaz et de bois enfin lue (points 79 et 80)

## Contexte (à lire avant tout)

Le lot 6 l'a montré : pour toute maison au fioul ou au gaz, celles à qui l'on propose une PAC air/eau, le pré-audit écrit « Avec vos factures de chauffage, ce chiffre serait plus juste »… mais la fiche ne permet pas de les donner. `conso_autre_energie_qte` est une quantité **sans unité** (litres ? kWh ? m³ ? stères ?). Le moteur l'ignore (`t.hyp_fiche("conso_autre_energie", "non utilisée…")`), tout comme « Ce que coûte ma maison » (`cout_maison.poste_autre_energie`, raison `unite_inconnue`).

Ce lot donne une unité à cette quantité, et la consommation déclarée de fioul, de gaz, de bois ou de réseau de chaleur suit alors **la même voie que l'électricité** : consommation déclarée, calage sur l'estimation, économies, puissance. Il règle aussi les points 79 et 80.

## Décisions de Stéphane (22/10/2026, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Point 79 | Réglages de puissance du lot 6 **validés en l'état**. Dans `config.py`, « A VALIDER » devient « validé par Stéphane le 22/10/2026 (ordres de grandeur, à recaler sur des cas réels) ». Cocher le point 79. |
| Point 80 | Quand un **appoint hors facture** est déclaré, le **calcul au volume** fait référence pour la puissance, et la consommation reste affichée à côté. |
| Lot | Consommation déclarée pour le fioul, le gaz, le bois et le réseau de chaleur, avec une unité. |

## 1. La fiche : type et unité

- `conso_autre_energie_type` devient une liste fermée : `gaz`, `fioul`, `bois_buches`, `granules`, `reseau`. Sa colonne `String(50)` reste en place.
- Migration réversible : nouveau champ `conso_autre_energie_unite`. Les anciennes valeurs libres sont ramenées à la liste quand le texte est sans ambiguïté (« fioul », « gaz », « granulés »…), sinon mises à `null`, avec un compte des cas dans le débrief.
- Unités permises par type, contrôlées par le schéma :

| Type | Unités |
|---|---|
| `gaz` | `kwh` (ce qu'affiche la facture), `m3` |
| `fioul` | `litres`, `kwh` |
| `bois_buches` | `steres` |
| `granules` | `kg` |
| `reseau` | `kwh` |

- Dans `FicheMaison.tsx` : le type devient une liste de choix ; l'unité est une liste qui dépend du type et s'affiche à côté de la quantité. Libellé : « Autre énergie (quantité par an) ».
- Le dossier PDF (`pdf_dossier.py`) imprime l'unité après la quantité.

## 2. La conversion en kWh (un seul endroit)

Une fonction pure, par exemple `kwh_autre_energie(type, unite, qte) -> float | None` (dans `audit_engine.py` ou un petit module partagé), utilisée par le pré-audit **et** par `cout_maison`. Les facteurs vont dans `config.py`, commentés « A VALIDER par Stéphane » :

| Réglage `audit_kwh_par_unite` | Proposition | Repère |
|---|---|---|
| `fioul`, `litres` | 10 | déjà dans le commentaire du prix du fioul (~10 kWh PCI/L) |
| `gaz`, `m3` | 11 | coefficient de conversion courant des factures (kWh PCS/m³), cohérent avec le prix CRE en €/kWh |
| `bois_buches`, `steres` | 1 700 | bois dur sec ; de 1 500 à 2 000 kWh/stère selon l'essence et l'humidité |
| `granules`, `kg` | 4,6 | déjà dans le commentaire du prix du bois (4,6 MWh/t) |
| `kwh` | 1 | |

Le propane n'est pas dans la liste : le moteur n'a pas d'énergie « propane ». Ne pas l'ajouter dans ce lot, et le noter dans le débrief.

## 3. Le pré-audit : la même voie que l'électricité

Dans `consommation()`, remplacer la branche `elif p["energie"] != "electricite"`.

- La quantité déclarée sert **seulement** si son type correspond à l'énergie du chauffage principal :
  - `gaz` ↔ `gaz` ;
  - `fioul` ↔ `fioul` ;
  - `bois_buches` ou `granules` ↔ `bois` ;
  - `reseau` ↔ `reseau`.
  Sinon, la quantité ne sert à rien et une hypothèse le dit.
- `declaree_kwh` = conversion − eau chaude, quand la fiche dit que l'eau chaude vient de la même énergie : `ecs == "gaz"` avec un chauffage gaz. L'eau chaude au gaz se déduit avec `audit_ecs_combustible_kwh_occupant_an` (proposition : 1 100 kWh par occupant et par an, A VALIDER), avec le statut `suppose`. Dans les autres cas, rien n'est déduit et une hypothèse le dit (« l'eau chaude peut être comprise dans cette quantité »).
- Le reste est **identique à la voie électrique** :
  - seuil `audit_chauffage_declare_min_kwh` et alerte d'incohérence ;
  - `ratio_reel_theorique` et `message_ratio` ;
  - `base_economies = "declaree"` ;
  - statuts : quantité `declare`, facteur `suppose`, conversion `calcule`.
- Conséquence voulue : les économies, les coûts du chauffage actuel et la puissance d'une maison au fioul ou au gaz **avec relevé** changent. Une maison **sans relevé** ne change pas.

## 4. Point 80 dans `puissance_chauffage`

- Un appoint est **hors facture** quand `chauffage_appoint` est renseigné et que son énergie (`ENERGIE_CHAUFFAGE`) diffère de celle de la consommation déclarée. Généraliser le test actuel (`APPOINT_HORS_FACTURE`, écrit pour l'électricité) à toutes les énergies, sans changer son effet sur le calage électrique (une hypothèse, rien de plus).
- Base `declaree` avec un appoint hors facture : le **volume** fait référence, avec un nouveau texte, d'abord dans la section « Pour le pré-audit » de `kb/action_pac_remplacement.md`, puis recopié :
  - **puissance_appoint** : « Au jour le plus froid de référence ({t_base} °C), votre maison demande entre {p_bas} et {p_haut} kW de chauffage. Votre appoint ({appoint}) chauffe une partie de la maison sans passer par vos relevés : le calcul au volume ({p_volume} kW) sert donc de référence. »
- Dans l'espace, sous le bloc « Puissance de chauffage » en base `estimee` : un lien « Indiquer ma consommation » vers la rubrique Énergie de la fiche. Rien dans le PDF.

## 5. « Ce que coûte ma maison »

`poste_autre_energie` utilise la même conversion :
- montant = kWh × `prix_energie` de ce type (bûches et granulés : le prix `bois`) ;
- `prix_statut` `suppose` et la date de valeur du prix, comme le poste électricité ;
- la raison `unite_inconnue` ne reste que pour une ancienne valeur sans unité.

## Méthode de travail

- Lire :
  - `services/audit_engine.py` (`_profil`, `consommation`, `usages_specifiques_kwh`, `puissance_chauffage`) ;
  - `audit_reference.py` (`ENERGIE_CHAUFFAGE`, `APPOINT_HORS_FACTURE`) ;
  - `services/cout_maison.py`, `services/pdf_dossier.py`, `pages/FicheMaison.tsx`, `schemas/house.py` ;
  - les débriefs du pré-audit lot 6 et du carnet lot 10.
- Plan court, un commit par étape, message en français.
- `audit_version` passe à `"v2.7"`. Les audits stockés ne sont jamais recalculés et s'affichent toujours.
- **Avant de toucher au moteur**, enregistrer la sortie v2.6 de cinq maisons : les quatre du lot 6 et la maison de référence avec son appoint « autre ».
- À la fin : s'arrêter, résumer et joindre un tableau v2.6 → v2.7 pour six cas :
  - fioul 1 500 L ;
  - gaz 12 000 kWh, ECS gaz, 3 occupants ;
  - gaz 1 100 m³ ;
  - bois 8 stères ;
  - référence avec appoint (point 80) ;
  - fioul sans relevé.
  Colonnes : consommation retenue, base, économies du plan, référence de puissance, plage PAC, poste « autre énergie ». Joindre aussi les PDF du fioul 1 500 L et de la référence, et une capture de la fiche. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-preaudit-lot7.md`. `CLAUDE.md` : 2 lignes au plus.

## Tests

- Conversion : chaque couple type et unité ; couple interdit refusé par le schéma ; quantité nulle → `None`.
- Correspondance : un relevé de fioul sur une maison au gaz est ignoré, avec une hypothèse.
- Eau chaude au gaz déduite ; fioul sans déduction, avec une hypothèse.
- Seuil, alerte et ratio identiques à la voie électrique, sur un cas à la main.
- Point 80 : référence avec appoint → volume, texte `puissance_appoint` ; électrique sans appoint → inchangé.
- Non-régression : chaque maison **sans relevé** de combustible donne une sortie v2.7 identique à la v2.6, hors version et hypothèses nouvelles.
- `cout_maison` : poste chiffré avec un relevé, `unite_inconnue` pour une ancienne valeur.
- Migration aller et retour ; anciens audits v1 à v2.6 toujours affichables ; aucune variable `{…}` non remplie.
- Tests existants verts, build front vert.

## TODO.md

Cocher 79 et 80 après vérification. Ajouter : **valider les facteurs de conversion et l'eau chaude au gaz** (`audit_kwh_par_unite`, `audit_ecs_combustible_kwh_occupant_an`).

---

## À ne pas faire

- Ne pas ajouter le propane, ni une énergie nouvelle au moteur.
- Ne pas deviner une unité absente : sans unité, la quantité ne sert pas.
- Ne pas toucher à la voie électrique, hormis la généralisation du test d'appoint, sans effet sur son calage.
- Ne pas utiliser un relevé d'une autre énergie que celle du chauffage principal.
- Aucun chiffre produit par le LLM ; aucun texte écrit directement dans le code.
- Ne pas recalculer les audits stockés.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Un foyer au fioul, au gaz, au bois ou en réseau de chaleur peut donner sa consommation avec son unité, et le pré-audit s'en sert comme pour l'électricité.
2. Avec un appoint hors facture, la puissance de référence est celle du volume, et le foyer lit pourquoi.
3. « Ce que coûte ma maison » chiffre le poste « autre énergie ».
4. Une maison sans relevé de combustible ne change pas.
5. Tests et build verts, tableau, rendus et capture joints, débrief écrit, points 79 et 80 cochés.
