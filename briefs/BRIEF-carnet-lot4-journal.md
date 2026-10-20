# Brief Claude Code — Carnet de maison, lot 4 : le journal et « À faire ce mois-ci »

## Contexte (à lire avant tout)

Prérequis : **lots 1 et 3 validés** (équipements, travaux, moteur d'entretien).

Ce lot donne au foyer une raison de revenir : un bloc **« À faire ce mois-ci »** en tête de son espace, et un **journal de la maison** qui garde la trace de tout ce qui a été fait. Cocher une tâche l'inscrit au journal, et le moteur du lot 3 recalcule la prochaine échéance.

Décisions de Stéphane (20/10/2026) : rappels par **e-mail et bloc dans l'espace**. Ici, **seulement le bloc** : l'e-mail attend le branchement du fournisseur (point 1 de `TODO.md`). Tout tourne en local.

Si la table d'entretien est encore vide (lot 3 bis pas encore fait), le bloc fonctionne quand même : il affiche les garanties qui arrivent à échéance (lot 1) et un message honnête sur le calendrier.

Fichiers concernés (à confirmer dans ton plan) :
- `api/app/models/journal.py` (nouveau), `api/alembic/versions/0026_journal.py`
- `api/app/schemas/journal.py`, `api/app/routers/journal.py`, `api/app/routers/entretien.py`
- `api/app/services/a_faire.py` (nouveau, fonctions pures)
- `frontend/src/pages/Espace.tsx`, `frontend/src/components/carnet/`
- `api/tests/test_a_faire.py`, `TODO.md`

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Statut des données | Une entrée est **déclarée** ; avec une facture ou un rapport joint, elle est marquée **justifiée**. |
| Place du bloc | En haut de `/espace`, au-dessus des onglets, replié en une ligne quand il n'y a rien d'urgent. |
| Contenu du bloc | Tâches `en_retard` et `ce_mois`, puis jusqu'à 3 `bientot` ; garanties au statut `bientot` ; au plus 6 lignes, avec « Tout voir » vers le calendrier complet. |
| Coûts | Facultatifs, en euros TTC, jamais additionnés en « budget » dans ce lot. |
| Remplacement | Une entrée de type `remplacement` propose de passer l'ancien équipement hors service et d'en créer un nouveau (formulaire du lot 1 pré-rempli). Rien d'automatique. |

## Méthode de travail

- Lire les débriefs des lots 1 et 3, `services/entretien.py`, `services/garanties.py`, `pages/Espace.tsx`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (bloc vide, bloc avec une tâche en retard et une garantie qui expire, journal avec cinq entrées, vue mobile). Pour les captures, utiliser la table d'exemple des tests chargée **en local seulement**, jamais commitée dans `taches.json`. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot4.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Le journal

**`JournalEntree`** (table `journal_maison`) : `id`, `house_id` (cascade), `date` (obligatoire, pas dans le futur), `type` (`entretien`, `controle`, `reparation`, `remplacement`, `amelioration`, `autre`), `titre` (court, obligatoire), `equipement_id` (optionnel, `SET NULL`), `piece_id` (optionnel, `SET NULL`, si le lot 2 est en place), `tache_id` (slug de la table d'entretien, optionnel), `intervenant` (`moi` ou un nom libre), `cout_eur` (optionnel), `document_id` (optionnel, `SET NULL`), `note`, `created_at`.

Migration `0026`, réversible. Limite : 500 entrées par maison.

API :
- `GET /houses/me/journal` : entrées et travaux du lot 1 fusionnés, du plus récent au plus ancien, chaque ligne marquée `source: journal | travaux` ; filtre optionnel par équipement.
- `POST`, `PATCH /{id}`, `DELETE /{id}` sur les entrées (les travaux restent gérés par leur propre route).
- `POST /houses/me/entretien/{tache_id}/fait` avec `equipement_id`, `date` (défaut aujourd'hui), `intervenant`, `cout_eur`, `document_id` : crée l'entrée liée à la tâche.
- Le routeur d'entretien passe désormais au moteur les `derniers_faits` lus dans le journal.
- Contrôles d'accès sur le modèle de `documents.py` ; un document, une pièce ou un équipement lié doit appartenir à la même maison.

## 2. Le bloc « À faire ce mois-ci », en fonctions pures

`api/app/services/a_faire.py` → `a_faire(echeances, garanties, aujourd_hui)` : applique la règle de contenu du tableau de décisions et rend une liste ordonnée de lignes (`kind: tache | garantie`), plus `table_vide` et `rien_d_urgent`.

`GET /houses/me/a-faire` expose cette liste.

## 3. L'écran

- **Bloc « À faire ce mois-ci »** en haut de `/espace` : une ligne par élément (libellé, équipement, échéance relative « depuis 3 semaines », « avant le 12 novembre », pastille obligation ou conseil, `qui`). Bouton **« C'est fait »** sur chaque tâche : petit formulaire (date, moi ou un pro, coût, joindre un document existant) → la ligne disparaît et la prochaine échéance apparaît dans le calendrier.
- Messages :
  - pas d'équipement → « Ajoutez vos équipements pour recevoir votre calendrier d'entretien » + lien vers « Ma maison » ;
  - table vide → « Le calendrier d'entretien est en préparation : il sera relu avant d'être publié. » (garanties affichées quand même) ;
  - rien d'urgent → une ligne : « Rien à faire ce mois-ci. Prochaine échéance : … ».
- **Calendrier complet** (« Tout voir ») : toutes les échéances groupées par statut, dans l'onglet « Ma maison ».
- **Journal** : nouvelle section de l'onglet « Ma maison », frise du plus récent au plus ancien, filtre par équipement, ajout manuel, icône « justifié » quand un document est joint.
- Charte « Carnet de maison », mobile d'abord, aucune couleur en dur.

## 4. Tests

- `a_faire` : composition et ordre du bloc, plafond de 6 lignes, cas table vide, cas rien d'urgent, garantie `bientot` incluse.
- « C'est fait » sur une tâche en retard → l'échéance suivante est calculée depuis la date saisie.
- Une date dans le futur est refusée.
- Le journal fusionné mêle entrées et travaux dans le bon ordre.
- Tests existants verts, build front vert.

## 5. TODO.md

Ligne « Carnet, lot 4 » cochée après vérification. Mettre à jour le point 1 (e-mails) : préciser que **les rappels d'entretien par e-mail** s'ajoutent à ce qu'il débloquera, avec l'endroit du code où les brancher.

---

## À ne pas faire

- **Pas d'envoi d'e-mail**, pas de tâche planifiée, pas de notification du navigateur.
- **Aucune nouvelle dépendance.**
- Ne pas commiter de tâche d'entretien dans `taches.json`.
- Pas de total des dépenses ni de « budget » (brique Argent, plus tard).
- Ne rien créer ni mettre hors service automatiquement.
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le bloc « À faire ce mois-ci » s'affiche en haut de l'espace, juste et sobre, dans tous les cas (sans équipement, table vide, rien d'urgent, tâches en retard).
2. « C'est fait » inscrit l'entrée au journal et décale l'échéance.
3. Le journal mêle entretiens, réparations et travaux, avec les justificatifs signalés.
4. Tests et build verts, captures jointes, débrief écrit.
