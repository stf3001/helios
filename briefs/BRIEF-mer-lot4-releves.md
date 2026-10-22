# Brief Claude Code — Mises en relation, lot 4 : les relevés mensuels

## Contexte (à lire avant tout)

Prérequis : **lots 1 et 3 validés** (prix fixe, contestations).

Chaque mise en relation transmise vaut 60 € HT, sauf contestation acceptée. Il faut un **relevé mensuel par partenaire**, lisible des deux côtés. La société Hélios n'est pas encore créée : ce lot produit des **relevés**, pas des factures. La facturation légale (numérotation continue, mentions obligatoires, TVA) viendra quand la SAS existera ; le relevé est conçu pour qu'elle s'y branche.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Période | Mois civil, à l'heure de Paris, selon la date de **transmission** du lead. |
| Lignes | Leads `travaux` du mois, avec : date, métier, commune (pas de nom du foyer), prix HT, état (`facturable`, `contestation en cours`, `contestation acceptée`). |
| Total | Somme HT des lignes `facturable` ; une contestation encore en attente est listée à part et **exclue** du total tant qu'elle n'est pas tranchée. TVA à 20 % et TTC affichés à titre indicatif. |
| Clôture | Un mois se **clôt** par l'administration, au plus tôt le 8 du mois suivant (après le délai de contestation des leads de fin de mois). Un relevé clos est figé (instantané JSON + PDF), immuable. Un mois non clos s'affiche « provisoire ». |
| Mention | En tête du PDF : « Relevé de mises en relation — ce document n'est pas une facture. » |

## Méthode de travail

- Lire les débriefs des mer lots 1 et 3, `models/partner.py`, `services/pdf_dossier.py` et `pdf_audit.py` (polices et briques communes, à importer et non à modifier).
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, rendu d'un relevé provisoire et d'un relevé clos, captures côté partenaire et côté admin. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-mer-lot4.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Calcul, en fonctions pures

`services/releves.py` → `releve(partenaire, leads, contestations, mois)` : lignes, total HT, TVA, TTC, contestations en attente. Aucun accès à la base dans ce module.

## 2. Données et clôture

Table `releves` (partenaire, mois, statut `provisoire|clos`, instantané JSON, chemin du PDF, date de clôture). `POST /admin/releves/{mois}/cloturer` refuse avant le 8 du mois suivant et s'il reste des contestations en attente sur ce mois (le message les liste).

## 3. Écrans et exports

- Espace partenaire : « Mes relevés », mois par mois, PDF.
- Administration : tableau du mois (partenaire, nombre de leads, contestés, total HT), clôture, export CSV.
- PDF : `services/pdf_releve.py`, mêmes polices que les autres documents.

## 4. Tests

- Frontières de mois à l'heure de Paris (lead transmis le 31 à 23 h 30, le 1er à 0 h 30, passage à l'heure d'hiver).
- Contestation en attente exclue du total ; acceptée exclue ; refusée incluse.
- Clôture refusée avant le 8 et avec une contestation en attente ; relevé clos immuable.
- Le PDF porte la mention exacte et ne contient aucun nom de foyer.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Ne pas émettre de facture ni de numéro de facture.
- Pas de paiement en ligne, pas de prélèvement.
- Aucun nom, téléphone ni e-mail de foyer dans un relevé.
- Ne pas modifier les PDF existants.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Chaque partenaire voit son relevé du mois, provisoire puis clos.
2. Les montants suivent exactement les leads et les contestations.
3. Un relevé clos ne bouge plus.
4. Tests et build verts, rendus et captures joints, débrief écrit.
