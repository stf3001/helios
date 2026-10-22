# Brief Claude Code — Mises en relation, lot 5 : le suivi côté foyer et les indicateurs

## Contexte (à lire avant tout)

Prérequis : **lots 1 à 3 validés**.

Le foyer doit savoir où en est sa demande et pouvoir réagir si personne ne l'appelle. Ses réponses croisent aussi les déclarations des partenaires : c'est la mesure de la qualité du réseau. Ce lot ajoute ce suivi dans l'espace du foyer, et un tableau d'indicateurs pour l'administration. Toujours **sans e-mail** : les questions apparaissent dans l'espace, et dans le bloc « À faire ce mois-ci » du carnet.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Délai de premier contact | 5 jours ouvrés après la transmission (doc 08). |
| Question au foyer | Passé ce délai sans contact déclaré par le partenaire : « L'entreprise vous a-t-elle contacté ? » (oui / non). La question apparaît dans « Mises en relation » et dans le bloc « À faire ». |
| Si « non » | Le foyer peut demander une autre mise en relation (nouveau tirage parmi les éligibles, en excluant ce partenaire). Le lead d'origine est marqué `sans_contact_signale`. **Le prix du lead d'origine n'est pas annulé automatiquement** : l'administration le voit et décide (une non-réponse avérée peut justifier un avoir sur le relevé non clos). |
| Déclarations du foyer | « Devis reçu », « Travaux signés », « Projet abandonné », à tout moment. Elles alimentent les statistiques, jamais le prix. |
| Écart | Quand le foyer et le partenaire se contredisent (contact, signature), l'écart est listé côté administration. |
| Notation | Inchangée : après « Travaux signés », le foyer peut noter l'entreprise (existant). |

**Indicateurs** (administration, par mois et cumul) : mises en relation transmises ; part des foyers ayant un pré-audit ou une étude qui demandent une mise en relation ; délai moyen de premier contact (déclaré) ; part des « non contacté » signalés ; taux de contestation et d'acceptation ; taux de devis et de signature déclarés (foyer et partenaire) ; note moyenne ; total HT facturable du mois. Chaque indicateur affiche sa source (déclaré partenaire, déclaré foyer, calculé).

## Méthode de travail

- Lire les débriefs des mer lots 1 à 3, `pages/EspaceMisesEnRelation.tsx`, `services/a_faire.py`, `services/admin_stats.py`, `pages/admin/AdminDashboard.tsx`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (question au foyer, nouvelle mise en relation, tableau d'indicateurs). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-mer-lot5.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Données

Migration réversible : `leads.contact_foyer` (`oui|non|null` + date), `leads.declarations_foyer` (JSONB daté), `leads.sans_contact_signale` (bool).

## 2. Fonctions pures

- `jours_ouvres_depuis(date, aujourd_hui)` (week-ends et jours fériés français de la métropole, liste écrite dans le code avec sa source, sans dépendance).
- `question_contact_due(lead, aujourd_hui)`.
- `indicateurs(leads, contestations, audits, etudes, mois)`.

## 3. Écrans

- Espace du foyer : chaque demande avec son étape, la question si elle est due, les déclarations, « Demander une autre entreprise » si « non ».
- Bloc « À faire » : la question y figure tant qu'elle n'a pas de réponse.
- Administration : page « Indicateurs » et liste des écarts.

## 4. Tests

- Jours ouvrés : week-end, jour férié, passage de mois.
- La question n'apparaît qu'après 5 jours ouvrés et sans contact déclaré.
- « Non » → nouvelle proposition sans ce partenaire ; le lead d'origine garde son prix.
- Écart détecté entre déclarations.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Pas d'e-mail, pas de SMS, pas de notification du navigateur.
- Ne jamais annuler un prix automatiquement.
- Aucun classement public des partenaires à partir de ces indicateurs.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le foyer suit sa demande et n'est jamais laissé sans recours si personne ne l'appelle.
2. L'administration voit la qualité du réseau, et les écarts entre foyers et partenaires.
3. Tests et build verts, captures jointes, débrief écrit.
