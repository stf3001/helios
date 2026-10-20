# Brief Claude Code — Administration : voir et suivre les rendez-vous

## Contexte (à lire avant tout)

Point 2 de `TODO.md` : un visiteur réserve un créneau de 30 minutes, la ligne s'écrit en base (`rendez_vous`), et **aucun écran ne la relit**. Stéphane ne voit pas les appels qu'il manque.

Le point 2 a deux moitiés : la notification (qui attend l'e-mail, point 1) et **un écran d'administration**. Ce lot fait **seulement l'écran**, faisable tout de suite en local. Il ne tranche pas les plages horaires (`rdv_plages_horaires` reste tel quel : c'est une décision de Stéphane, pas technique).

Fichiers concernés (à confirmer dans ton plan) :
- `api/app/models/rendez_vous.py` (colonne `note_interne`), `api/alembic/versions/` (nouvelle migration, numéro suivant)
- `api/app/routers/admin.py`
- `frontend/src/pages/admin/` (nouvelle page), `frontend/src/App.tsx` (route admin), menu d'administration, tableau de bord admin
- `api/tests/`, `TODO.md`

## Décisions (déjà tranchées)

| Sujet | Décision |
|---|---|
| Statuts | `reserve` (défaut existant), `honore`, `absent`, `annule`. |
| Vue par défaut | Rendez-vous à venir, du plus proche au plus lointain ; un second onglet « Passés » sur 60 jours. |
| Note | Une note interne libre par rendez-vous, visible seulement en administration. |
| Notification | **Aucune** dans ce lot. |

## Méthode de travail

- Lire `routers/rendez_vous.py`, `services/creneaux.py`, `routers/admin.py` (motif des routes protégées) et une page admin existante (ex. `AdminSignalements`) comme modèle d'écran.
- Plan court, un commit par étape. À la fin : s'arrêter, résumer, captures (liste vide, liste avec trois rendez-vous). **Attendre la validation de Stéphane.**
- Débrief court dans `debriefs/`. `CLAUDE.md` : 1 ligne au plus.

---

## 1. API (administration seulement)

- `GET /admin/rendez-vous?periode=a_venir|passes` : nom, téléphone, e-mail, sujet, début (affiché en heure de Paris), durée, statut, note interne, lien vers le foyer si `user_id` est renseigné.
- `PATCH /admin/rendez-vous/{id}` : statut et/ou note interne.
- Un créneau `annule` redevient réservable : vérifier ce que fait l'unicité sur `debut` et, si elle bloque, **le signaler dans le résumé sans changer la règle** (on en décidera ensemble).

## 2. Écran

- Page « Rendez-vous » dans le menu d'administration, sur le modèle des pages existantes : une ligne par rendez-vous, numéro de téléphone cliquable (`tel:`), changement de statut en un clic, note dépliable.
- Sur le tableau de bord admin : une tuile « Rendez-vous à venir » avec le nombre et le prochain créneau.

## 3. Tests

- La liste est réservée à l'administration (un foyer connecté reçoit 403).
- Tri et filtre à venir / passés justes autour de l'heure courante, en tenant compte du fuseau de Paris.
- Changement de statut et note persistés.
- Tests existants verts, build front vert.

## 4. TODO.md

Dans le point 2, cocher la moitié « écran d'administration » (sans cocher le point entier) et citer le commit. Laisser ouvertes la notification et la décision sur les plages horaires.

---

## À ne pas faire

- Pas d'e-mail, pas de SMS, pas de notification.
- Ne pas modifier les plages horaires, la durée ni l'horizon de réservation.
- Pas d'export vers un agenda externe.
- **Aucune nouvelle dépendance.**

## Critères d'acceptation

1. Stéphane voit dans l'administration chaque rendez-vous à venir, avec le numéro à appeler.
2. Il peut marquer un rendez-vous honoré, absent ou annulé et y laisser une note.
3. Le tableau de bord annonce le prochain rendez-vous.
4. Tests et build verts, captures jointes.
