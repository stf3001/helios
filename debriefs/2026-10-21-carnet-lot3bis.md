# Débrief — Carnet de maison, lot 3 bis « la table d'entretien relue »

21/10/2026. À l'intention de Claude, pour rédiger le prochain brief.
Commits `7a92e61` → fin du lot sur `main` (non poussés). Le lot attend la validation de Stéphane.

## Ce qui est livré

| Étape (section 7) | Commit | État |
|---|---|---|
| 1. Extensions du moteur | — (faites au lot 3) | vérifiées : 33 tests verts, chaque cas de la section 1 relu face au code |
| 1 bis. Champ `zone_old`, migration 0026, fiche | `7a92e61` | fait |
| 1 ter. Ligne « Vérifiez si votre terrain est concerné » | `26bd996` | fait |
| 2. Section 6 recopiée dans `taches.json` | `e990bdc` | fait, identique à l'octet près |
| 3. Aucun libellé, fréquence ni source modifié | — | tenu |
| 4. Vérification sur les trois maisons | dernier commit | par l'API (le bloc est au lot 4) ; fiche vérifiée à l'écran |
| TODO (point 39 coché), CLAUDE.md, ce débrief | dernier commit | fait |

566 tests au vert, aucun sauté ; `tsc -b` et `npm run build` passent.

## Les trois maisons de la section 7, au 21/10/2026

Comptes jetables, vraie table, effacés ensuite. Sortie complète :
`debriefs/2026-10-21-carnet-lot3bis-trois-maisons.json`.

**1. Chaudière gaz (posée le 05/11/2018, 24 kW) + VMC simple flux (2018)**

| Statut | Échéance | Tâche | Provenance |
|---|---|---|---|
| en retard | 01/01/2019 | `vmc-bouches` | année de pose (supposée) |
| en retard | 01/07/2019 | `vmc-caisson` | année de pose (supposée) |
| en retard | 31/12/2019 | `chaudiere-entretien` (obligation, période sept.-oct.) | date de pose |
| à planifier | — | `detecteur-fumee-test` | — |
| à vérifier | — | « Vérifiez si votre terrain est concerné » → F33298 | `zone_old` = ne sais pas |

Pas de ramonage pour le gaz (décision 1).

**2. PAC air/eau (12/04/2022, 9 kW) + ballon thermodynamique (2022) + PV (20/03/2024)**

| Statut | Échéance | Tâche |
|---|---|---|
| en retard | 01/08/2022 | `ballon-groupe-securite` (référence supposée) |
| en retard | 01/10/2023 | `pac-unite-exterieure` (reporté en octobre) |
| en retard | 20/04/2024 | `pv-suivi-production` |
| en retard | 01/07/2024 | `ballon-detartrage` (référence supposée) |
| en retard | 31/12/2024 | `pac-entretien` (obligation, année civile n+2) |
| en retard | 01/04/2025 | `pv-inspection-visuelle` (reporté en avril) |
| à planifier | — | `detecteur-fumee-test` |
| à vérifier | — | « Vérifiez si votre terrain est concerné » |

Pas de `clim-filtres` : une PAC air/eau n'a pas d'unités intérieures à filtres, et octobre
est hors de ses `mois_actifs` de toute façon.

**3. Poêle à bois (2019) + fosse septique (2005), `zone_old` = oui**

| Statut | Échéance | Tâche |
|---|---|---|
| en retard | 01/07/2006 | `fosse-niveau-boues` (référence supposée) |
| en retard | 01/07/2015 | `spanc-controle` (obligation) |
| en retard | 01/09/2020 | `poele-entretien` (obligation, reporté en septembre) |
| en retard | 01/09/2020 | `ramonage` (obligation, reporté en septembre) |
| à planifier | — | `debroussaillement` (obligation) |
| à planifier | — | `detecteur-fumee-test` |

Aucune ligne « à vérifier » : la réponse est « oui ».

## Les règles de fonctionnement à connaître pour écrire un brief

- **`zone_old`** : `oui` | `non` | `ne_sais_pas`, NOT NULL, défaut `ne_sais_pas` (fiches
  existantes comprises). Un `null` envoyé par la fiche devient `ne_sais_pas`. Hors score.
- **Question de maison** (`QUESTIONS_DE_MAISON` dans `services/entretien.py`) : sa réponse
  ne compte que si `type_logement = maison`. Un appartement, ou un type non renseigné, n'a ni
  l'obligation ni la ligne de vérification, même avec `zone_old = oui` en base.
- **`verifications`** : liste à part dans `GET /houses/me/entretien`, sans date :
  `tache_id`, `champ`, `libelle`, `tache_libelle`, `nature`, `lien` (l'URL de la source).

## Écarts avec le brief, et pourquoi

- **Vérification « à l'écran du bloc À faire ce mois-ci »** : le bloc n'existe pas (lot 4).
  Fait à la place, comme convenu : la fiche à l'écran, et l'API sur les trois maisons.
- **Choix des équipements des trois maisons** : la section 7 ne donne que leur nature. Dates,
  puissances et marques sont les miennes, choisies pour exercer les règles (date exacte et
  année seule, puissance connue dans la plage, report de mois).

## Ce qui attend Stéphane

- **Tout est « en retard »** sur les trois maisons : aucun journal, aucun roulement (choix du
  lot 3). La fosse de 2005 est en retard depuis 2006. C'est ce que montrera le bloc du lot 4
  tant que le foyer ne peut pas dire « fait le … » : à garder en tête pour son brief
  (proposer un premier « fait le » au moment où l'on ajoute l'équipement ?).
- **Écarts dans la table, recopiés sans rien changer** (à trancher dans une nouvelle version
  du document si besoin) :
  - les deux tâches photovoltaïques sont « Expertise Stéphane, **à valider** » en section 3,
    mais portent `valide_le: 2026-10-20` dans le JSON : elles s'affichent ;
  - « qui : SPANC » en section 2, `pro` dans le JSON ;
  - PAC : « premier dans les 2 ans suivant la pose » en section 2, mais la règle année civile
    du JSON donne plus tard (posée le 12/04/2022 → 31/12/2024, et non avril 2024).
- **L'aide sous la question** dit « Vérifiez sur service-public.gouv.fr (fiche F33298) » :
  texte à valider. Le lien cliquable, lui, est dans la ligne de vérification de l'API.
- Le compte de démo a été remis à « ne sais pas » après le test.

## Pistes pour le prochain brief

1. **Lot 4** : vérifier le bloc sur ces trois maisons (le JSON ci-dessus sert de référence),
   et traiter le « tout en retard » dès l'ajout d'un équipement.
2. **Les rendez-vous admin** (`BRIEF-admin-rendez-vous.md`, point 2 bloquant) : toujours à faire.
