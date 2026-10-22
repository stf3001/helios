# Modèles de projet — `modeles.json`

Lu par `api/app/services/projets.py` (chargeur strict + fonctions pures). Carnet de maison,
lot 9. Un modèle ne contient AUCUN chiffre et AUCUN texte d'explication : les chiffres
viennent d'un calcul déjà fait, les explications des fiches `kb/` qu'il nomme.

## Un modèle

- `id` : identifiant unique (`panneaux-solaires`).
- `titre` : ce que le foyer lit.
- `famille` : `solaire_stockage`, `sortie_fossile`, `ecosysteme` ou `enveloppe` (« Isolation et confort »).
- `outil` : où se fait le calcul — `simulateur-solaire`, `pre-audit:<clé d'action>` (clés de
  `ACTIONS` dans `audit_reference.py`), `vent`, `jardin`, ou `aucun` : pas de calculateur,
  l'écran renvoie aux fiches et `lier-etude` est refusé (jardin d'hiver ; machine à eau tant
  que le calculateur d'Hydrolia est en panne).
- `poste` : pour le simulateur seulement, la ligne de `investissement` qui chiffre ce projet
  (`panneaux_eur`, `carport_eur`, `batterie_eur`, `inertie_eur`, `eolien_eur`).
- `fiches_kb` : identifiants de SOURCE (`SourceSpec.name` de `agents_engine.py`). **Toutes
  sont indispensables** : une seule qui manque, et le modèle n'est pas servi.
- `equipements_crees` : `[{"categorie", "type", "origine_fiche"?}]`, codes du lot 1. Proposés
  à la réception, créés seulement si le foyer les coche. Avec `origine_fiche`, le nouvel
  appareil prend la place de celui qui la tenait (passé hors service) et la fiche suit (lot 7).
- `lourd` : vrai pour des travaux qu'un locataire ne décide pas — masqués pour lui (lot 8).
- `masque_si` : `{champ de fiche : [valeurs]}` — caché si la fiche porte l'une d'elles.
- `affiche_si` : `{champ de fiche : [valeurs]}` — caché si la fiche porte une AUTRE valeur ;
  un champ non renseigné ne cache rien.
- `categorie_cil` (facultatif) : la rubrique du carnet d'information du logement (`CATEGORIES_CIL`
  de `models/travaux.py`) que « Les travaux sont terminés » propose pour le chantier ; le foyer
  peut la changer ou la retirer.
- `mention_locataire` (facultatif, vrai ou faux) : un modèle LÉGER que voit un locataire porte
  `projets.MENTION_LOCATAIRE` (« voir avec le propriétaire »). Seule la régulation l'a.
- Un `outil` `pre-audit:<clé>` doit nommer une clé de `ACTIONS` : le chargeur le vérifie.
