# Débrief — Pré-audit, lot 6 « la puissance de chauffage et les radiateurs pièce par pièce » (point 37)

22/10/2026. Commits `9ebeaaf` → fin du lot sur `main`, non poussés. Le lot attend la validation de
Stéphane.

| Étape | Commit | État |
|---|---|---|
| Textes ajoutés à `kb/action_pac_remplacement.md` et recopiés (`TEXTES_PUISSANCE`), réglages A VALIDER, sorties v2.5 des quatre maisons enregistrées | `9ebeaaf` | fait |
| Moteur : `puissance_chauffage`, `bilan_radiateurs`, route qui passe les pièces, v2.6 | `ee7c391` | fait |
| Bloc « Puissance de chauffage » dans le PDF et dans l'espace, libellés des hypothèses | `eb73d55` | fait |
| Rendus, TODO (37 et 63 cochés, 79 et 80 ouverts), CLAUDE.md, ce débrief | dernier commit | fait |

**861 tests au vert**, dont 28 dans `test_audit_puissance.py` et 7 de plus dans
`test_audit_textes.py`. `tsc -b` et `npm run build` passent (520 URL, inchangé).

## Les quatre maisons

Rendus dans `debriefs/captures/` : `preaudit-lot6-<maison>.pdf` et, pour les trois qui affichent le
bloc, `preaudit-lot6-<maison>-puissance.png` (la page relue à l'œil).

| Maison | Chauffage | Consommation | P_conso | P_volume | Référence | Plage PAC air/eau | Affiché | Radiateurs |
|---|---|---|---|---|---|---|---|---|
| Référence (`reference_complete`, 200 m², Toulon) | PAC air/air | déclarée | 4,2 kW | 12,2 kW | consommation, 4,2 | (3,5-5) | rien | — |
| Fioul (`maison_type`, 100 m², Marseille), 6 pièces | fioul | estimée | 6,6 kW | 7,3 kW | volume, 7,3 | 6 à 9 kW | complet | Séjour ok 55 · Cuisine insuffisant · Chambre 1 ok 50 · Chambre 2 ok 55 · Bureau (plancher) ok 50 · Salle de bains inconnu |
| Convecteurs (`maison_type`, 12 000 kWh déclarés) | électrique direct | déclarée | 4,9 kW | 7,3 kW | consommation, 4,9 | — | phrase seule | — |
| Gaz sans pièces (`maison_type`) | gaz | estimée | 6,6 kW | 7,3 kW | volume, 7,3 | 6 à 9 kW | complet, sans radiateurs | — |

Chiffres refaits à la main dans les commentaires des tests (fioul : 275 W/K × 24 K = 6,6 kW ;
indice d'isolation 0,764, G = 1,222, 100 × 2,5 × 1,222 × 24 = 7,3 kW ; un radiateur de 1 000 W
donne 482 W à 50/45 et 594 W à 55/50).

Vérifié aussi à l'écran, de bout en bout : un foyer jetable au fioul avec ses six pièces en base, le
pré-audit généré par la route, le bloc relu dans l'espace (`preaudit-lot6-ecran-fioul.jpg`). Aucun
débordement à 375 px. Le foyer et son PDF ont été effacés ensuite.

## Rien d'autre ne change, et c'est prouvé

La sortie v2.5 des quatre maisons a été enregistrée AVANT de toucher au moteur
(`api/tests/fixtures/audit_v25/`). La v2.6, privée de sa version, de son bloc `puissance` et de ses
hypothèses `puissance_*`/`radiateurs_*`, lui est identique au caractère près : mêmes unités air/air,
coûts, aides, économies, horizons, ordre, déperditions, climat. Les PDF des audits v2.5 se génèrent
toujours, sans le bloc.

## Écarts avec le brief, et pourquoi

- **La maison de référence n'affiche pas le bloc.** Elle est déjà en PAC air/air : le pré-audit ne
  lui propose aucune PAC, et la règle du brief n'affiche le bloc qu'avec une PAC proposée. Sa
  puissance est calculée (dans le JSON et le tableau ci-dessus). La « maison en convecteurs » est
  donc `maison_type` en chauffage électrique avec 12 000 kWh déclarés, pas la maison de référence.
- **« Consommation déclarée » ne coexiste jamais avec une PAC air/eau.** L'air/eau n'est proposée
  qu'au fioul et au gaz, et seule l'électricité a un relevé dans la fiche. En pratique : air/eau →
  toujours le volume et `puissance_estimee` ; `puissance_declaree` sert aux maisons électriques
  (air/air, phrase seule).
- **L'indice d'une maison sans aucune isolation vaut 0,985, pas 1** : les ponts thermiques sont
  toujours comptés à 0,7. Gardé tel quel, comme demandé.
- **Le rendement de l'appareil actuel** est lu dans `audit_rendement_chauffage` même quand la
  consommation vient du DPE (le moteur ne le gardait que pour l'autre voie).
- **Cas que le brief ne tranchait pas** (annoncés dans le plan, acceptés) : une pièce chauffée au
  bois, par la clim, par un émetteur « autre » ou sans émetteur n'a pas de verdict ; une pièce en
  émetteurs électriques a le verdict `electrique` sans phrase (la phrase `note_convecteurs` ne sort
  que si toutes les pièces le sont) ; des radiateurs dont un seul n'a pas de puissance → `inconnu` ;
  un plancher chauffant à eau → `ok_50`. **Le plancher chauffant électrique** est compté parmi les
  émetteurs électriques, bien que le brief ne le cite pas. Un sèche-serviettes électrique à côté de
  radiateurs à eau n'entre pas dans leur total (prudent).
- **Réglages en entiers** (températures, degrés-jours, régimes) : en flottants, le PDF imprimait
  « 1500,0 » et « 50,0 / 45,0 ». Et la source des hypothèses dit « valeurs à calibrer » plutôt que
  « A VALIDER », qui s'imprimait tel quel dans le PDF du foyer (le « A VALIDER » reste dans
  `config.py`).
- **Pas de tableau chiffré par pièce dans le PDF** : seules les phrases de la fiche s'affichent.
  Les puissances par pièce (besoin, à 50 et à 55 °C) sont dans le JSON de l'audit si un tableau
  est souhaité plus tard.
- Le contexte du chat (`rag.build_audit_context`) ne reprend pas encore la puissance.

## Ce qui attend Stéphane

- Valider le lot et les rendus.
- **Point 79** : valider les réglages (températures de base, degrés-jours, G, hauteur, exposant,
  plage PAC).
- **Point 80** : une facture qui ne voit pas tout le chauffage donne une puissance trop basse. La
  maison de référence ressort à 4,2 kW par la consommation contre 12,2 kW au volume, à cause de son
  appoint « autre », hors facture. Garder la règle, ou basculer sur le volume dans ce cas : à lui de
  trancher.
