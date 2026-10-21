# Brief Claude Code — Carnet de maison, lot 10 : ce que coûte la maison, et ce que les travaux changeraient

## Contexte (à lire avant tout)

Décision du 20/10/2026 (brique « Argent ») : **coût de possession et effet des travaux** en gratuit ; la valeur du bien viendra plus tard, en Super Hélios. Hélios n'est pas un outil bancaire : pas de prêt, pas de patrimoine.

Ce lot assemble ce qui existe déjà, sans nouveau calcul de fond :

- la consommation et le contrat déclarés dans la fiche, et les prix d'énergie déjà présents dans `config.py` (utilisés par le pré-audit) ;
- les coûts saisis au journal (lot 4) ;
- les résultats du dernier pré-audit et des études du simulateur (économies, coûts, temps de retour), **stockés** et datés.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Postes | Énergie (électricité, autre énergie) ; entretien et réparations (journal, 12 derniers mois) ; assurance habitation ; taxe foncière (propriétaire seulement) ; charges de copropriété (appartement) ; eau ; autre. |
| Saisie | Les quatre derniers postes sont **déclarés** par le foyer, en euros par an, dans un petit formulaire « Mes charges ». Facultatifs. |
| Énergie | Consommation déclarée × prix du kWh de `config.py` = **calculé** (prix **supposé**, avec sa date de valeur affichée). Une facture jointe ne change rien dans ce lot. |
| Entretien | Somme des `cout_eur` du journal sur 12 mois = **calculé** à partir de données **déclarées**. |
| Effet des travaux | Recopie du dernier pré-audit (plan d'actions : coût en fourchette, économie annuelle, temps de retour) et des études enregistrées, **tels qu'ils ont été calculés**, avec leur date. Aucun recalcul. |
| Affichage | Total par an et par mois, répartition par poste, et pour chaque chiffre son statut. Un poste vide est affiché « Non renseigné », jamais 0. |

## Méthode de travail

- Lire `services/audit_engine.py` (prix de l'énergie, sortie du plan), `config.py`, `models/audit.py`, les études du simulateur, `routers/journal.py`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (maison sans rien, maison complète avec un pré-audit). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot10.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Les charges déclarées

Table `charges_maison` (une ligne par maison) : `assurance_eur_an`, `taxe_fonciere_eur_an`, `charges_copro_eur_an`, `eau_eur_an`, `autre_eur_an`, `autre_libelle`, `updated_at`. Migration réversible. API `GET/PUT /houses/me/charges`.

## 2. Le calcul, en fonctions pures

`services/cout_maison.py` → `cout_possession(house, charges, journal_12_mois, prix)` : postes, total annuel et mensuel, statut de chaque valeur, liste des postes manquants. Les postes qui ne s'appliquent pas (taxe foncière d'un locataire, copropriété d'une maison) sont omis.

`effet_travaux(dernier_audit, etudes)` : la liste à afficher, recopiée des données stockées, avec date et lien vers l'audit ou l'étude.

## 3. L'API et l'écran

- `GET /houses/me/cout` : `cout_possession` + `effet_travaux`.
- Une section « Ce que coûte ma maison » dans l'onglet « Ma maison » : total, barre de répartition simple en CSS (pas de bibliothèque de graphiques), lien « Compléter mes charges », puis « Ce que vos projets changeraient » (si un pré-audit ou une étude existe ; sinon un bouton vers le pré-audit).
- Charte « Carnet de maison », mobile d'abord.

## 4. Tests

- Maison vide : tous les postes « Non renseigné », aucun 0.
- Énergie : le montant suit exactement consommation × prix de `config.py`.
- Entretien : seules les entrées des 12 derniers mois comptent.
- Locataire : pas de taxe foncière ; maison : pas de charges de copropriété.
- Effet des travaux : valeurs identiques à l'audit stocké.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Pas de valeur du bien, pas de prêt, pas de patrimoine.
- Aucun nouveau prix ni coefficient : seulement ceux de `config.py`.
- Ne pas recalculer un pré-audit ni une étude.
- Pas de bibliothèque de graphiques. **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le foyer voit ce que lui coûte sa maison par an et par mois, poste par poste, avec l'origine de chaque chiffre.
2. Les effets des travaux viennent tels quels de ses calculs, datés.
3. Tests et build verts, captures jointes, débrief écrit.
