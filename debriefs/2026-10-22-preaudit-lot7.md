# Débrief — Pré-audit, lot 7 « la consommation de fioul, de gaz et de bois enfin lue » (points 79 et 80)

22/10/2026. Commits `e20aac6` → fin du lot sur `main`, non poussés. Le lot attend la validation de
Stéphane.

| Étape | Commit | État |
|---|---|---|
| Fiche : type fermé et unité (migration 0043), contrôle du couple dans `PATCH`, dossier PDF ; sorties v2.6 enregistrées | `e20aac6` | fait |
| Conversion en kWh (`services/autre_energie.py`), facteurs A VALIDER ; réglages de puissance validés (79) | `8cefc04` | fait |
| Moteur v2.7 : relevé de combustible, eau chaude au gaz déduite, appoint hors relevé → volume (80) | `4b9b0ac` | fait |
| « Ce que coûte ma maison » chiffre l'autre énergie ; lien « Indiquer ma consommation » | `3233187` | fait |
| Tableau, rendus, TODO (79 et 80 cochés, 81 ouvert), CLAUDE.md, ce débrief | dernier commit | fait |

**898 tests au vert**, dont 34 dans `test_audit_combustible.py`, 1 contre la base dans
`test_autre_energie_api.py` et 1 de plus dans `test_cout_maison.py`. `tsc -b` passe, build vert.

## Le tableau v2.6 → v2.7

Maison de 100 m² à Marseille (`maison_type`) sauf la référence. Économies : celles du plan
recommandé, en fourchette.

| Cas | Consommation retenue, base | Économies du plan | Référence de puissance | Plage PAC air/eau | Poste « autre énergie » |
|---|---|---|---|---|---|
| Fioul 1 500 L | 11 647 estimée → **15 000 déclarée** | 1 475-1 996 → **1 962-2 654 €/an** | volume 7,3 → **consommation 8,5 kW** | 6-9 → **7-10 kW** | **2 850 €/an** |
| Gaz 12 000 kWh, eau chaude gaz, 3 occupants | 11 000 estimée → **8 700 déclarée** (3 300 d'eau chaude déduits) | 442-598 → **350-474 €/an** | volume 7,3 → **consommation 5,2 kW** | 6-9 → **4-6,5 kW** | 1 747 €/an |
| Gaz 1 100 m³ | 11 000 estimée → **12 100 déclarée** | 442-598 → **487-659 €/an** | volume 7,3 → **consommation 7,3 kW** | 6-9 → **6-8,5 kW** | 1 762 €/an |
| Bois 8 stères | 13 200 estimée → **13 600 déclarée** | 292-394 → **300-407 €/an** | volume 7,3 → **consommation 6,8 kW** | 6-9 → **5,5-8 kW** | 1 088 €/an |
| Référence avec appoint « autre » (point 80) | 2 100 déclarée (inchangé) | 0 (inchangé) | consommation 4,2 → **volume 12,2 kW** | (3,5-5 → 10-14,5, non affichée) | — |
| Fioul sans relevé | inchangé | inchangé | inchangé | inchangé | — |

Le poste « autre énergie » compte toute la quantité livrée (eau chaude comprise) : c'est ce que le
foyer paie. Le pré-audit, lui, n'en garde que la part du chauffage.

Rendus (`debriefs/captures/`) :
- `preaudit-lot7-fioul_1500_litres.pdf` et `-consommation.png` : « D'après votre relevé : 1 500
  litres de fioul par an, soit environ 15 000 kWh », puis la puissance par la consommation ;
- `preaudit-lot7-reference.pdf` : la maison de référence. **Le texte du point 80 n'y apparaît pas** :
  elle est déjà en PAC air/air, le pré-audit ne lui propose aucune PAC, et le bloc ne s'affiche
  qu'avec une PAC proposée (règle du lot 6). Le calcul, lui, a changé (tableau). D'où un rendu de
  plus :
- `preaudit-lot7-gaz_appoint_electrique.pdf` et `-puissance.png` : maison au gaz, 12 000 kWh
  relevés, convecteurs en appoint → « Votre appoint (convecteurs électriques) chauffe une partie de
  la maison sans passer par vos relevés : le calcul au volume (7,3 kW) sert donc de référence. » ;
- `preaudit-lot7-fiche-energie.jpg` : le bloc Énergie de la fiche, fioul, 1 500, litres.

Vérifié à l'écran de bout en bout avec un foyer jetable au fioul, effacé ensuite (avec ses PDF) :
pré-audit sans relevé → lien « Indiquer ma consommation » → bloc Énergie ouvert à 80 px du haut,
unité masquée tant que l'énergie n'est pas choisie, puis réduite à « litres / kWh » pour le fioul →
relevé enregistré → nouveau pré-audit en base déclarée, sans le lien → « Ce que coûte ma maison » :
« 1 500 litres de fioul, soit 15 000 kWh × 0,1900 €/kWh, prix supposé (au 01/09/2026) », 2 850 €/an.

## Ce qui ne change pas, et c'est prouvé

Les sorties v2.6 de neuf maisons ont été enregistrées avant de toucher au moteur
(`api/tests/fixtures/audit_v26/`) : les quatre du lot 6 et les cas du tableau, sans unité (ce que
la v2.6 savait lire). La v2.7 leur est identique, hors version : une quantité sans unité ne sert
toujours pas. Seule exception, voulue : la puissance de la maison de référence (point 80).

La voie électrique est inchangée : la nouvelle règle d'appoint donne exactement l'ancienne
`APPOINT_HORS_FACTURE` pour l'électricité (testé sur chaque valeur d'appoint).

## Écarts avec le brief, et pourquoi

- **Un appoint « autre » est toujours hors relevé.** Le moteur le range en électricité ; généraliser
  le test tel quel l'aurait sorti du point 80 sur une maison électrique — précisément la maison de
  référence. Annoncé dans le plan.
- **Le couple type-unité est contrôlé par la route `PATCH`**, pas par le schéma seul : un envoi de
  la seule unité (ou du seul type) doit être confronté à la fiche enregistrée. Le schéma, lui,
  refuse un type ou une unité hors liste (422). Changer d'énergie à l'écran vide l'unité qui ne
  va plus ; l'API refuse (400) plutôt que de la vider elle-même.
- **Migration** : la base de dev n'avait **aucune** ancienne valeur libre (0 ligne à ramener). La
  fonction de classement est testée sur des textes fabriqués ; « bois » seul (bûches ou granulés ?)
  et « propane » donnent NULL.
- **Alerte d'incohérence des combustibles** : même seuil et même effet que l'électricité ; sa
  phrase dit « l'eau chaude » au lieu des « usages courants », écrite dans le code comme l'alerte
  électrique.
- **« Votre facture et la théorie »** : l'intitulé de l'encadré du PDF reste tel quel avec un relevé.
- **Le lien « Indiquer ma consommation »** mène à `/mon-espace#energie`, qui ouvre le bloc Énergie
  de la fiche et l'amène à l'écran (petite ancre ajoutée à `BlockCard`).
- **Le propane** n'est pas ajouté (consigne) : un foyer au propane ne peut pas déclarer son relevé.
  Inscrit au point 81.

## Ce qui attend Stéphane

- Valider le lot, le tableau et les rendus.
- **Point 81** : valider les facteurs de conversion et l'eau chaude au gaz.
