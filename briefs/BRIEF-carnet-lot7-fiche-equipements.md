# Brief Claude Code — Carnet de maison, lot 7 : une seule source pour les équipements de la fiche (point 35)

## Contexte (à lire avant tout)

Depuis le lot 1, le type et l'année du chauffage, de l'eau chaude, de la clim et de la ventilation vivent à deux endroits : la fiche (`houses.chauffage_principal`, `chauffage_principal_annee`, `ecs`, `ecs_annee`, `clim`, `clim_type`, `ventilation`…), lue par le pré-audit et le score de complétude, et les équipements du carnet (`equipements`, champ `origine_fiche`). Le carnet affiche seulement « Votre fiche indique 2016 » quand les deux diffèrent (point 35 de `TODO.md`).

Ce lot établit **une seule source de vérité** sans toucher au pré-audit.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Qui gagne | **L'équipement en service portant `origine_fiche`.** Le champ de fiche correspondant devient une **copie** maintenue par le serveur. |
| Sens de la synchronisation | Équipement → fiche, à chaque création, modification, mise hors service ou remplacement d'un équipement portant `origine_fiche`. |
| Fiche verrouillée | Dans la page fiche, un champ dont l'équipement existe s'affiche en lecture, avec le lien « Modifier dans Mes équipements ». Sans équipement lié, la fiche reste éditable comme aujourd'hui. |
| Écart existant | À la migration, pour chaque maison où les deux diffèrent, **l'équipement gagne** et l'ancienne valeur de la fiche est consignée dans le journal de la maison (`type: autre`, titre « Fiche mise à jour depuis le carnet », note avec l'ancienne valeur). |
| Remplacement | Un équipement qui remplace un équipement `origine_fiche` hérite de son `origine_fiche` ; la fiche prend les valeurs du nouveau. |
| Mise hors service sans remplaçant | Le champ de fiche est vidé (année et type), et le foyer est invité à indiquer ce qui le remplace. |
| Pré-audit | **Inchangé** : il continue de lire la fiche, qui est désormais juste. Les audits stockés ne sont pas recalculés. |

## Méthode de travail

- Lire le débrief du lot 1, `services/suggestions_fiche.py`, `routers/equipements.py`, `routers/houses.py`, `pages/FicheMaison.tsx`, `services/completeness.py`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (fiche avec un champ verrouillé, carnet après un remplacement). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot7.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. La correspondance, en fonctions pures

`services/fiche_equipements.py` : une table unique `origine_fiche` → champs de fiche et conversion de codes (type d'équipement → valeur de fiche, année de pose ou année de la date de pose → `*_annee`). Les types d'équipement sans équivalent dans la fiche donnent `autre` ou `null`, jamais une valeur inventée. Fonctions : `champs_fiche_depuis(equipement)`, `champs_a_vider(origine_fiche)`, `ecarts(house, equipements)`.

## 2. La synchronisation

- Appelée par les routes d'équipement (création, modification, hors service, remplacement) dans la même transaction.
- Le score de complétude est recalculé après chaque écriture de fiche.
- `PATCH /houses/me` refuse (400, message clair) une modification d'un champ verrouillé.
- `GET /houses/me` expose la liste `champs_verrouilles`.

## 3. La migration des données

Script Alembic (ou script de données lancé par la migration) qui applique la règle « l'équipement gagne » et écrit l'entrée de journal. Idempotent : relancé, il ne fait rien de plus.

## 4. L'écran

- Fiche : les champs verrouillés en lecture, avec le lien.
- Carnet : la note « Votre fiche indique… » disparaît (elle n'a plus lieu d'être).

## 5. Tests

- Chaque `origine_fiche` : création, modification d'année, hors service, remplacement → la fiche suit.
- `PATCH /houses/me` sur un champ verrouillé → 400 ; sur un champ libre → OK.
- Migration : une maison avec écart → l'équipement gagne, une entrée de journal ; relancée → rien.
- Un pré-audit lancé après la synchronisation lit les bonnes valeurs ; les audits stockés sont intacts.
- Tests existants verts, build front vert.

## 6. TODO.md

Cocher le point 35 après vérification.

---

## À ne pas faire

- Ne pas modifier le moteur de pré-audit ni recalculer les audits stockés.
- Ne pas supprimer de colonne de la fiche.
- Ne jamais écrire dans la fiche une valeur qui ne vient pas d'un équipement ou du foyer.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Une seule saisie : modifier l'équipement met la fiche à jour, et la fiche ne peut plus le contredire.
2. Les écarts existants sont résolus en faveur de l'équipement, avec une trace au journal.
3. Le pré-audit lit des valeurs justes sans avoir changé.
4. Tests et build verts, captures jointes, débrief écrit, point 35 coché.
