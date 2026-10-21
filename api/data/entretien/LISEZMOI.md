# Table d'entretien — `taches.json`

Lue par `api/app/services/entretien.py` (chargeur + moteur, fonctions pures). Aucun LLM :
chaque tâche affichée vient d'ici, et nulle part ailleurs.

**RÈGLE : AUCUNE TÂCHE SANS RELECTURE DE STÉPHANE.** Une tâche sans `valide_le` ne
s'affiche pas. Une obligation exige en plus une source officielle. Le contenu réel arrive
au lot 3 bis depuis `briefs/KB-entretien-table.md` ; ne rien écrire ici « parce que c'est
évident » — ni fréquence, ni obligation, ni conseil.

Validation : en test (mode strict), une tâche invalide fait échouer le chargement ; en
production, elle est ignorée et une ligne est écrite dans le journal (`helios.entretien`).

## En-tête

- `version` : date de la version de la table (`AAAA-MM-JJ`).
- `avertissement` : phrase affichée avec le calendrier.
- `taches` : la liste des tâches.

## Une tâche

- `id` : identifiant unique, en minuscules et tirets (`pac-entretien`).
- `applique_a` : à quoi la tâche s'applique, l'une des deux formes :
  - `{"categorie": "chauffage" | ["chauffage", "clim"], "types": [...]}` — équipements du
    carnet (codes de `models/equipement.py`) ; `types` vide = toute la catégorie ;
  - `{"maison": {}}` — la maison elle-même (détecteur de fumée) ; `{"maison": {"champ": valeur}}`
    seulement si le champ de la fiche vaut cette valeur. Un champ que la fiche n'a pas : tâche absente.
- `libelle` : ce que le foyer lit.
- `regle` : `mois` (défaut) ou `annee_civile`.
  - `mois` + `frequence_mois` (entier ≥ 1) : échéance = référence + n mois.
  - `annee_civile` + `n_annees` (entier ≥ 1) : échéance = 31 décembre de (année de référence + n).
- `puissance_kw` : `{"min": 4, "max": 70}`, facultatif, tâches d'équipement seulement. Puissance
  connue (unité `kW`) hors plage → tâche absente ; inconnue → tâche affichée avec une mention.
- `qui` : `soi`, `pro` ou `soi_ou_pro`.
- `nature` : `obligation` ou `recommande`.
- `mois_preferes` : mois (1-12) conseillés. Règle `mois` : l'échéance est reportée au 1er du
  premier mois préféré qui suit. Règle `annee_civile` : l'échéance reste le 31/12, les mois sont
  renvoyés comme période conseillée.
- `mois_actifs` : mois (1-12) où la tâche a un sens ; hors de ces mois, elle n'est pas renvoyée.
- `source` : `{"type": "officiel" | "guide" | "fabricant" | "expertise", "titre": "…", "url": "…" | null}`.
  Une obligation exige `type: officiel`, un titre et une URL.
- `fiche_kb` : source de la base de connaissances à proposer en lecture (facultatif).
- `valide_le` : date de relecture par Stéphane (`AAAA-MM-JJ`). **Obligatoire.**
- `note` : précision affichée avec la tâche (facultatif).
