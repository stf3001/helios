# Brief Claude Code — Phase 2 : les projets isolation, menuiseries, ventilation et régulation

## Contexte (à lire avant tout)

Le lot 9 du carnet a créé les projets avec trois familles (solaire et stockage, sortie du fioul ou du gaz, écosystème). Décision du 20/10/2026 : **isolation et menuiseries ensuite**. Tout existe déjà pour les servir : le pré-audit calcule ces actions (`audit_engine.ACTIONS` : `isolation_combles`, `isolation_murs`, `isolation_plancher`, `menuiseries`, `ventilation_double_flux`, `regulation`), et les fiches `kb/action_*.md` les expliquent.

Ce lot ajoute une **quatrième famille** de modèles, sans nouveau calcul ni nouveau texte.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Famille | `enveloppe`, titre affiché « Isolation et confort ». |
| Modèles | Isolation des combles ou de la toiture ; isolation des murs ; isolation du plancher bas ; changement des fenêtres ; ventilation (VMC) ; régulation du chauffage. |
| Outil | `pre-audit:<clé d'action>` pour chacun (la clé correspondante d'`ACTIONS`). `lier-etude` recopie le coût, l'économie et l'horizon **de l'action** dans le dernier pré-audit, tels quels, datés. |
| Fiches | La fiche `action_*` du sujet, plus `urbanisme_assurance` pour les murs (une isolation par l'extérieur modifie la façade) et les fenêtres, `financement_projet`, `choisir_installateur`, `garanties_travaux`. Règle du lot 9 inchangée : une fiche manquante masque le modèle. |
| Équipements créés | Ventilation : le type VMC du lot 1 ; régulation : rien (pas d'équipement dans le lot 1) ; isolation et fenêtres : rien, mais `terminer` propose de remplir la rubrique CIL du chantier (lot 11 : `isolation_toiture`, `isolation_murs`, `parois_vitrees_portes`, `planchers_bas`, `chauffage_froid_ecs`) et ouvre la saisie des isolants. |
| Locataire | Modèles masqués comme les autres projets lourds, sauf « régulation du chauffage » (souvent un thermostat, sans travaux sur le bâti) : visible, avec la mention de voir avec le propriétaire. |
| Appartement | Combles, murs et plancher masqués (le plus souvent des parties communes, décidées en copropriété). Fenêtres, ventilation et régulation visibles. |

## Méthode de travail

- Lire le débrief du lot 9, `api/data/projets/modeles.json`, `services/audit_engine.py` (`ACTIONS` et sortie du plan), les fiches `kb/action_*.md`, le débrief du lot 11.
- Plan court, un commit, message en français.
- À la fin : s'arrêter, résumer, captures (famille « Isolation et confort » ; un projet combles lié au pré-audit du compte de démo ; un projet terminé avec sa rubrique CIL). **Attendre la validation de Stéphane.**
- Débrief court `debriefs/AAAA-MM-JJ-p2-projets-isolation.md`. `CLAUDE.md` : 1 ligne au plus.

## Tests

- Chaque modèle servi quand ses fiches existent ; masqué sinon.
- `lier-etude` recopie exactement l'action du pré-audit (aucun recalcul).
- Locataire et appartement : bonnes visibilités.
- `terminer` sur un projet combles propose la rubrique `isolation_toiture`.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Aucun nouveau calcul, aucun nouveau prix ; aucun texte produit par le LLM.
- Ne pas écrire de fiche : lister celles qui manqueraient.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Les six modèles « Isolation et confort » sont servis, reliés au pré-audit, avec leurs fiches.
2. Un projet d'isolation terminé alimente le carnet d'information du logement.
3. Tests et build verts, captures jointes, débrief écrit.
