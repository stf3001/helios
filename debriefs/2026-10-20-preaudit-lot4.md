# Débrief — Pré-audit, lot 4 « un raisonnement qu'on voit » (v2.4)

20/10/2026. À l'intention de Claude, pour rédiger le prochain brief.
Commits `f937f9e` → `12fa62e` sur `main`. Le lot attend la validation de Stéphane.

## Ce qui est livré

| Étape | Commit | État |
|---|---|---|
| 1. Textes des fiches dans le moteur (`TEXTES_ACTIONS`) | `f937f9e` | fait |
| 2. Gestes par équipement, fusionnés dans `GESTES_GRATUITS` | `1eac15f` | fait |
| 3 + 4. Leviers du contrat, DPE d'avant 2026, rénovation d'ampleur | `7fc1c9a` | fait (un seul commit : mêmes fonctions) |
| 5. Économie au remplacement d'une PAC air/air âgée | `3a48d40` | fait |
| 7 + 8. CO₂ et coût sur 10 ans | `e541152` | fait (un seul commit) |
| 9. PDF, espace client, contexte du chat | `0227ab4` | fait |
| 6. Convecteurs → PAC air/air au lieu d'air/eau | `3f96b62` | **commit isolé, à valider** (`git revert 3f96b62` le retire seul) |

473 tests au vert (`api/tests/test_audit_textes.py` : 60 nouveaux), `tsc -b` et `npm run build` passent.
Vérifié dans le navigateur, avec un compte de démo : nouvel audit, blocs repliés, lien vers la
FAQ, anciens audits v1 toujours lisibles, mobile sans débordement.

## Ce que le JSON d'un audit v2.4 contient en plus

- Sur chaque action, quand une fiche existe : `pourquoi`, `benefices[]`, `vigilance[]`,
  `devis[]`, `fiche`, `fiche_question` (la première question de la fiche, qui donne l'URL
  `/faq/<slug>`).
- `contrat[]` (`{cle, texte}`), `dpe_attestation` (`{texte, fiche}` ou null),
  `renovation_ampleur` (`{texte, vigilance[], fossile, fiche}` ou null).
- `confort_ete.note_clim`.
- Sur le conseil d'âge de la PAC air/air : `economie_au_remplacement_eur {bas, haut}` et
  `statut: "calcule"`. La phrase chiffrée remplace « une PAC récente consomme généralement moins ».
- `climat` : `chauffage_kg_an`, `eau_chaude_kg_an`, `apres_plan_recommande_kg_an`,
  `apres_tout_le_plan_kg_an`, `facteurs`, `statut`.
- `couts` : `chauffage_eur_an`, `eau_chaude_eur_an`, `hausse_pct_an`,
  `chauffage_et_eau_chaude_10_ans_eur`, `economie_10_ans_plan_recommande_eur`, `statut`.
- Le contexte du chat commence par `consigne_prioritaire` (les chiffres de la maison priment
  sur les ordres de grandeur de la base).

## Les règles de fonctionnement à connaître pour écrire un brief

- **Source unique des textes** : `audit_reference.py` recopie mot pour mot les sections
  « Pour le pré-audit » des fiches `kb/`. Un test casse si une fiche change. Pour modifier
  un texte, un brief doit dire « modifier la fiche, puis recopier » — jamais « réécrire dans
  le code ».
- **Une phrase dont une variable manque ne s'affiche pas.** Rien n'est inventé pour combler.
- **Le climat et les coûts rejouent les économies déjà calculées** par le moteur, dans l'ordre
  du plan. Aucun nouveau calcul physique.
- **Eau chaude au gaz = inconnue.** La couche de consommation du simulateur ne la compte pas
  (0 kWh d'électricité) : `eau_chaude_kg_an` et `eau_chaude_eur_an` valent null.
- **Production solaire** : elle n'est pas comptée dans le CO₂ (l'étude ne dit pas
  l'électricité réseau évitée).
- **PDF** : un bloc ne se coupe pas (`_ensemble`, rendu d'essai de fpdf2). « À l'occasion »,
  « En résumé » et la note d'aide restent ensemble, ce qui peut laisser une demi-page vide
  avant eux. Les montants des textes du moteur reçoivent des espaces insécables.

## Écarts avec le brief, et pourquoi

- **Gestes PAC air/air** : le geste de la fiche remplace aussi la programmation (il dit « baisse
  modérée la nuit »), pas seulement la consigne et les filtres.
- **Conseil d'âge de la PAC air/air** : la phrase chiffrée remplace l'ancienne phrase sans
  chiffre au lieu de s'y ajouter. Elle répétait la même idée.
- **Première étape (page 1)** : le `pourquoi` remplace le `contexte` quand il existe. Il le dit déjà.
- **Rénovation d'ampleur** : les fenêtres n'ont pas d'état « aucune / partielle » dans la fiche ;
  le simple vitrage en tient lieu.
- **Convecteurs** : trois éléments de `action_pac_remplacement` sont retirés pour la PAC
  air/air, sans être réécrits : « sortie du fioul ou du gaz », « désembouage et filtre »,
  « réglage de la loi d'eau ». La question de la fiche pour le lien est « J'ai des convecteurs
  électriques : pompe à chaleur air/eau ou air/air ? ».
- **Tests anciens adaptés**, en plus de celui des convecteurs : `filtres_pac` → `pac_air_air`,
  la phrase de la PAC, la limite de pages 4 → 5, et la recherche de la page « À l'occasion »
  (elle confondait la section avec l'étiquette de la frise).
- **Pages** : 5 pour la maison de référence et pour celle au fioul, **6 pour une maison en
  convecteurs** (aucune limite dans le brief pour ce cas).

## Ce qui attend Stéphane

**Valeurs en config, toutes commentées « à valider » ou « à calibrer »** :
- `audit_facteurs_co2_kg_kwh` : 0,079 / 0,065 / 0,227 / 0,324 / 0,030, conformes au brief ;
  réseau de chaleur inconnu 0,385 (ligne « autres réseaux de chaleur »). Relevés dans la
  transcription open source Open3CL de l'arrêté du 31/03/2021, **pas dans le PDF du JO**.
- `audit_scop_pac_air_air_neuf` 4,3.
- `audit_pac_air_air_cout_unite_eur` (2 500, 4 000), `audit_m2_par_unite_air_air` 30,
  `audit_unites_air_air_max` 6.
- `audit_kva_habituel` : 6 sans chauffage électrique, 9 avec.
- `audit_tarif_bloque_alerte_mois` 3.
- Écart non tranché : surcoût du ballon thermodynamique, 1 500 à 2 500 € dans le moteur,
  contre environ 2 300 à 2 700 € dans `kb/ecs_solaire.md`.

**Textes de fiche qui se trompent selon la maison** — point 33 de `TODO.md`, à corriger
dans les fiches :
1. `pourquoi_peu_rentable` suppose un chauffage bon marché. Or une action passe « à
   l'occasion » aussi parce que les actions d'avant ont déjà pris le gain. Maison F au fioul :
   « votre chauffage vous coûte peu (5 130 €/an) ». **Le plus visible.** Touche les murs, les
   combles, le plancher et la PAC.
2. PAC : « à la fin de vie de votre chaudière » s'affiche pour des convecteurs.
3. PAC air/air sur convecteurs : « beaucoup moins de CO₂ ».
4. Régulation : « baisses modérées avec une PAC » s'affiche aussi au gaz ou au fioul.
5. Menuiseries : « Du simple vitrage » s'affiche aussi quand les fenêtres sont inconnues.

## Pistes pour le prochain brief (lot 5)

1. **Corriger le point 33** : une variante de `pourquoi_peu_rentable` selon la raison réelle
   du classement. Le moteur sait la distinguer : coût du chauffage bas, ou gain déjà pris par
   les actions précédentes (comparer l'économie seule à l'économie marginale). Il faut deux
   textes par fiche, écrits par Stéphane, et une règle de choix dans le moteur.
2. **Trancher l'étape 6** : la garder ou la retirer, et calibrer les coûts par unité.
3. **Petites incohérences d'affichage** : le message « Aucune isolation n'est rentable »
   écrit le coût exact (566 €), le `pourquoi` l'arrondit à la dizaine (570 €). Choisir une
   seule règle.
4. **Pagination** : la demi-page vide avant « À l'occasion » (maison de référence) et les
   6 pages des convecteurs. On pourrait autoriser une coupure du bloc d'occasion après le
   tableau, en gardant la note d'aide avec lui.
5. **Lier les gestes et les leviers du contrat à leur fiche** (le champ `fiche` existe sur les
   gestes de la table, il n'est pas encore exposé dans le JSON).
6. **Points 31 et 32 de `TODO.md`** : intouchés, comme demandé.
