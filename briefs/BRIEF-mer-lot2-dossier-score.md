# Brief Claude Code — Mises en relation, lot 2 : le dossier transmis et son score

## Contexte (à lire avant tout)

Prérequis : **lot 1 validé** (prix fixe, choix parmi trois).

Une mise en relation vaut 60 € HT parce qu'elle est **qualifiée** : le foyer arrive avec un projet, une maison décrite, un calcul, et des créneaux pour être appelé. Ce lot construit le **dossier transmis** (ce que le foyer choisit de partager, figé au moment du consentement) et un **score de qualification** calculé, que le partenaire lit. Le score ne change pas le prix.

Rappel légal à respecter dans les textes : le démarchage téléphonique est interdit pour ces travaux (loi 2020-901, art. L. 223-1 du code de la consommation). Le partenaire n'appelle que parce que le foyer l'a demandé, **dans les créneaux qu'il a donnés**.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Ce que le foyer partage | Cases à cocher, toutes décochables sauf le minimum : **minimum** = code postal, type de logement, métier, message du foyer ; **au choix** = résumé de la fiche (surface, année, chauffage, isolation), le projet du carnet (lot 9 : étape, budget sourcé), le dernier pré-audit ou la dernière étude utile, jusqu'à 5 documents choisis (devis existants, photos, DPE). |
| Coordonnées | Nom, téléphone et e-mail, saisis ou confirmés à chaque demande. Le téléphone est facultatif ; sans téléphone, le partenaire écrit. |
| Créneaux | Le foyer choisit des jours et des plages (matin, midi, après-midi, soir) ; le dossier les affiche en tête. |
| Dossier figé | À la création du lead, un **instantané JSON** (`leads.dossier`) de ce qui a été coché, daté. Les documents choisis sont copiés dans un dossier propre au lead : supprimer un document de la maison ne le retire pas au partenaire ; **retirer son consentement** (avant signature) le retire. |
| Score (0 à 100, calculé) | Fiche complète à 60 % ou plus : 20 · projet du carnet à l'étape `etude` ou `devis` : 20 · pré-audit ou étude de moins de 6 mois partagé : 20 · horizon déclaré à 6 mois ou moins : 15 · budget envisagé déclaré : 10 · téléphone fourni : 15. Chaque ligne affichée au partenaire avec son statut (acquise / absente). Valeurs dans `config.py`, commentées « proposées le 22/10/2026, à calibrer avec les premiers retours partenaires ». |

## Méthode de travail

- Lire le débrief du mer lot 1, `routers/leads.py`, `models/partner.py`, `routers/projets.py`, `services/completeness.py`, `routers/documents.py`, `pages/EspaceMisesEnRelation.tsx`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (formulaire de demande, dossier vu côté partenaire). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-mer-lot2.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Données

Migration réversible : `leads.dossier` (JSONB), `leads.score` (int), `leads.score_detail` (JSONB), `leads.creneaux` (JSONB), `leads.contact_nom`, `contact_telephone`, `contact_email`, `message`. Copies de documents dans `generated/lead_docs/<lead_id>/`.

## 2. Services purs

- `services/dossier_lead.py` → `construire_dossier(house, projet, etude, documents, choix)` : l'instantané, sans aucune donnée non cochée ; **jamais** le PDL, les numéros de série, les notes libres du carnet, ni les noms d'intervenants.
- `services/score_lead.py` → `score(house, projet, etude, contact, horizon, budget)` : total et détail, valeurs de `config.py`.

## 3. API et écran du foyer

- `POST /leads` accepte les choix, les coordonnées, les créneaux et le message ; refuse sans créneau.
- Le formulaire montre **exactement** ce qui partira (aperçu du dossier) avant la case de consentement.
- Retrait du consentement : supprime les copies de documents du lead et vide `dossier` des données de la maison (le lead garde son historique de statut et son prix).

## 4. Côté partenaire (lecture seule dans ce lot)

`GET /partner/leads/{id}` renvoie le dossier, le score et son détail, les créneaux et les coordonnées. L'affichage complet de l'espace partenaire vient au lot 3 ; ici, une vue simple suffit pour vérifier.

## 5. Tests

- Une donnée non cochée n'apparaît jamais dans le dossier (test qui coche tout puis rien).
- Le PDL, les numéros de série et les notes n'apparaissent jamais.
- Score : chaque critère, et le total, sur trois maisons types.
- Retrait du consentement : documents copiés supprimés, dossier vidé.
- Supprimer un document de la maison ne touche pas la copie du lead.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Le score ne modifie ni le prix, ni l'ordre des propositions, ni l'accès d'un foyer aux mises en relation.
- Aucune donnée partagée sans case cochée.
- Pas d'e-mail.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le foyer voit et choisit précisément ce qu'il transmet, avec ses créneaux.
2. Le partenaire reçoit un dossier figé, daté, avec un score expliqué ligne par ligne.
3. Retirer son consentement retire les données.
4. Tests et build verts, captures jointes, débrief écrit.
