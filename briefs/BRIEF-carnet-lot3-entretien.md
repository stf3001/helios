# Brief Claude Code — Carnet de maison, lot 3 : le moteur d'entretien

## Contexte (à lire avant tout)

Prérequis : **lot 1 validé** (équipements datés). Le lot 2 n'est pas nécessaire.

Ce lot construit le calcul des échéances d'entretien : pour chaque équipement en service, quelles tâches, à quelle date, faites par qui, obligatoires ou recommandées. C'est un **moteur déterministe** : aucun LLM, aucun texte inventé, chaque tâche vient d'une table versionnée et sourcée.

Décisions de Stéphane (20/10/2026) :

- **Obligations légales** (chaudière, PAC, ramonage, détecteur de fumée, assainissement individuel, débroussaillement…) : Claude rédige chaque entrée en citant le texte officiel, **Stéphane relit** avant publication. Une obligation non relue ne s'affiche pas.
- Rappels : e-mail et bloc « À faire ce mois-ci ». **Ce lot ne fait ni l'un ni l'autre** : il fournit le calcul et l'API. Le bloc vient au lot 4, l'e-mail quand le fournisseur sera branché.

**Le contenu réel de la table n'est pas dans ce lot.** Il arrivera dans un document séparé, rédigé et sourcé dans le projet Hélios, relu par Stéphane, puis intégré par un court lot 3 bis. Ici, la table est créée vide, avec son format, son chargeur et ses garde-fous, et les tests tournent sur une table d'exemple.

Fichiers concernés (à confirmer dans ton plan) :
- `api/data/entretien/taches.json` (nouveau, liste vide + en-tête), `api/data/entretien/LISEZMOI.md` (format)
- `api/app/services/entretien.py` (nouveau : chargeur + moteur, fonctions pures)
- `api/app/routers/entretien.py`, enregistrement dans `main.py`
- `api/tests/fixtures/entretien_exemple.json`, `api/tests/test_entretien.py`
- `TODO.md`

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Format | JSON dans `api/data/entretien/`, sur le modèle de `api/data/jardin/calendrier.json`. Versionné dans git. |
| Validation | Une tâche s'affiche **seulement si `valide_le` est renseigné**. Une obligation exige en plus une `source` (titre + URL d'un texte officiel). Une tâche invalide fait échouer le chargement en test, pas en production : en production, elle est ignorée et journalisée. |
| Date de référence | Dernière fois faite (journal, lot 4) ; sinon date de pose ; sinon 1er juillet de l'année de pose (**supposé**) ; sinon inconnue. |
| Statuts | `en_retard` (échéance passée), `ce_mois` (dans les 30 jours), `bientot` (31 à 90 jours), `plus_tard`, `a_planifier` (date de référence inconnue). |
| Saison | Une tâche peut porter des mois préférés (ex. clim : avril-mai) : l'échéance est alors reportée au premier mois préféré qui suit la date calculée. |

## Méthode de travail

- Lire le débrief du lot 1, `api/data/jardin/calendrier.json` et son chargeur (modèle à suivre), `services/garanties.py`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, joindre la sortie de l'API pour la maison d'exemple des tests. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot3.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Le format de la table

`taches.json` :

```json
{
  "version": "AAAA-MM-JJ",
  "avertissement": "…",
  "taches": [
    {
      "id": "pac-air-eau-entretien",
      "applique_a": {"categorie": "chauffage", "types": ["PAC_air_eau"]},
      "libelle": "…",
      "frequence_mois": 24,
      "qui": "pro",
      "nature": "obligation",
      "mois_preferes": [9, 10],
      "source": {"titre": "…", "url": "https://www.legifrance.gouv.fr/…"},
      "fiche_kb": "slug-de-la-fiche",
      "valide_le": "2026-10-25",
      "note": "…"
    }
  ]
}
```

- `qui` : `soi`, `pro`, `soi_ou_pro`. `nature` : `obligation`, `recommande`.
- `applique_a` vise une catégorie et une liste de types du lot 1 (liste vide = toute la catégorie).
- `LISEZMOI.md` décrit chaque champ en une ligne et rappelle la règle : **aucune tâche sans relecture de Stéphane**.
- Le fichier livré contient l'en-tête et `"taches": []`.

## 2. Le moteur, en fonctions pures

`api/app/services/entretien.py` :

- `charger_taches(chemin) -> list` : lit, valide (champs obligatoires, codes connus, obligation ⇒ source, `valide_le` présent), lève une erreur claire en mode strict (tests) ou ignore et journalise en mode normal.
- `echeances(equipements, taches, derniers_faits, aujourd_hui) -> list` : pour chaque équipement **en service** et chaque tâche qui s'y applique, une échéance :
  - `tache_id`, `equipement_id`, libellé, `qui`, `nature`, source, `fiche_kb` ;
  - `date_reference` et sa provenance (`journal`, `date_pose`, `annee_pose` → **supposé**, `inconnue`) ;
  - `echeance` (date ou `null`) et `statut` ;
  - `derniers_faits` est un dictionnaire `(tache_id, equipement_id) → date`, vide tant que le journal n'existe pas (lot 4).
- Tri : `en_retard`, puis `ce_mois`, `bientot`, `a_planifier`, `plus_tard` ; à statut égal, la date la plus proche d'abord ; les obligations avant les recommandations.

## 3. L'API

- `GET /houses/me/entretien` → les échéances de la maison du foyer connecté, plus `version` de la table et le nombre de tâches validées.
- Table vide → liste vide et un champ `table_vide: true`, pour que l'écran du lot 4 affiche le bon message.

## 4. Tests

Sur `tests/fixtures/entretien_exemple.json` (cinq tâches fictives, clairement nommées « exemple », jamais copiées dans `taches.json`) :

- une obligation sans source et une tâche sans `valide_le` sont rejetées en mode strict ;
- PAC posée le 15/03/2020, fréquence 24 mois, aucun journal → échéances successives correctes et statut juste à trois dates « aujourd'hui » ;
- année de pose seule → référence au 1er juillet, provenance `annee_pose` ;
- ni date ni année → `a_planifier` ;
- `derniers_faits` renseigné → il prime sur la date de pose ;
- mois préférés → report au bon mois, y compris en passant d'une année à l'autre ;
- un équipement hors service ne produit rien ;
- tri conforme.

Tous les tests existants restent verts.

## 5. TODO.md

Ligne « Carnet, lot 3 » cochée après vérification. Ajouter : **lot 3 bis — intégrer la table d'entretien relue par Stéphane** (document à venir dans le projet Hélios).

---

## À ne pas faire

- **N'écrire aucune vraie tâche d'entretien dans `taches.json`**, même « évidente » : ni fréquence, ni obligation, ni conseil. Le contenu viendra relu.
- Aucun appel au LLM, aucun texte généré.
- **Aucune nouvelle dépendance.**
- Pas d'écran, pas de rappel, pas d'e-mail (lot 4 et plus tard).
- Ne pas lire la fiche maison pour inventer des équipements : le moteur ne travaille que sur les équipements du lot 1.
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le format est documenté, la table livrée est vide, le chargeur refuse toute tâche non relue ou toute obligation non sourcée.
2. Le moteur calcule échéances et statuts justes sur la table d'exemple, avec la provenance de chaque date.
3. L'API répond pour une maison réelle, y compris quand la table est vide.
4. Tests verts, sortie d'exemple jointe, débrief écrit.
