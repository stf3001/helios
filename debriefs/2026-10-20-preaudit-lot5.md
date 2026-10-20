# Débrief — Pré-audit, lot 5 « le bon pourquoi pour chaque maison » (v2.5)

20/10/2026. À l'intention de Claude, pour rédiger le prochain brief.
Commits `13ef29e` → fin du lot sur `main` (non poussés). Le lot attend la validation de Stéphane.

## Ce qui est livré

| Étape | Commit | État |
|---|---|---|
| 1. `raison_occasion` posée par `planifier` | `13ef29e` | fait |
| 2. Textes par raison, fiches d'abord puis recopie ; règle de choix | `f184dcc` | fait (fiches + `ecs_solaire.md` réingérée) |
| 3. Un seul arrondi pour le coût cité (`cout_cite`) | `90392a9` | fait |
| 4. Valeurs validées (PAC air/air, surcoût du ballon) | `dc208c2` | fait |
| 5. Liens « En savoir plus » sur gestes, contrat, DPE, rénovation d'ampleur | `8bce0f8` | fait |
| 6. Pagination : « À l'occasion » se coupe après son tableau | `a6cc5b8` | fait |
| Compatibilité : fixture d'un audit v2.4 stocké | `2263ac3` | fait |
| TODO (point 33 coché), CLAUDE.md, ce débrief | dernier commit | fait |

502 tests au vert, `tsc -b` et `npm run build` passent. Vérifié dans le navigateur (compte de
démo, audit v2.5 neuf) : liens vers la FAQ sur gestes, contrat et actions, aucune erreur.

## Ce que le JSON d'un audit v2.5 contient en plus

- Sur chaque action « à l'occasion » de **chauffage** : `raison_occasion`
  (`apres_autres` | `chauffage_peu_cher` | `trop_cher`). L'eau chaude et le solaire n'en ont pas.
- `fiche` et `fiche_question` sur les gestes issus d'une fiche, les leviers du contrat,
  `dpe_attestation` et `renovation_ampleur`.
- Aucun chiffre, horizon ni ordre ne change par rapport au v2.4 (hors valeurs validées).

## Les règles de fonctionnement à connaître pour écrire un brief

- **Choix du « pourquoi »** (commentaire en tête de `TEXTES_ACTIONS`) :
  - action « maintenant » ou « prioritaire » : `pourquoi_rentable`. Variantes :
    `pourquoi_rentable_inconnu` (fenêtres non renseignées) et `pourquoi_rentable_convecteurs`
    (PAC air/air) ;
  - action « à l'occasion » : d'abord le texte de sa raison, sinon `pourquoi_occasion`, sinon
    rien. Jamais `pourquoi_peu_rentable` pour une autre raison que `chauffage_peu_cher`.
- **La raison** : `apres_autres` si, seule sur la maison actuelle, l'action passerait le test
  « prioritaire » ; sinon `chauffage_peu_cher` si le chauffage coûte ≤ 800 €/an
  (`audit_chauffage_peu_cher_eur`) ; sinon `trop_cher`.
- **`{avant}`** : actions de chauffage « maintenant » ou « prioritaire » placées avant, avec leur
  article (`LIBELLE_AVANT`). Liste vide = variable manquante, donc on passe au texte suivant.
- **Clés `_convecteurs`** : elles remplacent leur clé de base pour la PAC air/air (même fiche
  `action_pac_remplacement`). `vigilance` et les textes « à l'occasion » sont communs aux deux PAC.
- **`vigilance_si_pac`** (régulation) s'ajoute seulement si le chauffage est une PAC.
- **Source unique** : le test compare chaque clé à la fiche, mot pour mot. Le retrait
  d'éléments côté code (lot 4) a disparu. Toute correction de texte passe par la fiche.
- **Un coût de chauffage cité** dans un texte s'arrondit toujours à la dizaine (`cout_cite`).
- **PDF** : seuls « En résumé » et la note d'aide sont indivisibles. « Comprendre votre maison »
  ouvre toujours une page (règle du lot 3), d'où un blanc possible en fin de plan.

## Écarts avec le brief, et pourquoi

- **Valeur de comparaison du « apres_autres »** : le test « seule » reprend exactement le test
  « prioritaire » de `_horizon` (retour ≤ 20 ans et ≤ durée de vie), calculé au premier passage.
- **Cas construit pour `apres_autres` avec `{avant}`** : après le changement de prix, la PAC
  air/air des convecteurs n'est plus « à l'occasion ». Le test utilise donc une maison de 80 m²
  au fioul aux murs nus, où la PAC air/eau sort en `apres_autres` : « Après la régulation et
  l'isolation du toit, votre maison demandera beaucoup moins de chaleur… ».
- **Fenêtres en `apres_autres`** : la fiche n'a pas de texte `pourquoi_apres_autres`, elles
  reçoivent donc `pourquoi_occasion`, comme prévu par la règle.
- **Tests anciens adaptés** : les chiffres du ballon (surcoût 1 800-2 800, retour 5,5 ans) et
  de la PAC air/air (7 200-12 000 € pour 4 unités) ; le test de mise en page, qui imposait le
  résumé sur la même page que le tableau « À l'occasion » (c'est ce que l'étape 6 relâche) ;
  le test des gestes accepte `fiche` et `fiche_question`.
- **Pas de commit séparé pour le test de raison** : il est livré avec l'étape 1.

## Résultat sur les quatre maisons

| Maison | Action | Horizon | Raison | Début du « pourquoi » |
|---|---|---|---|---|
| Référence (420 €/an) | Ballon thermodynamique | prioritaire | – | « Votre ballon a 16 ans : au moment de le changer… » |
| | Combles | à l'occasion | chauffage_peu_cher | « Votre toit perd beaucoup de chaleur, mais cette chaleur vous coûte peu… » |
| | Murs | à l'occasion | chauffage_peu_cher | « Isoler les murs coûte cher au m², et votre chauffage vous coûte peu (420 €/an)… » |
| | Plancher | à l'occasion | chauffage_peu_cher | « Le plancher pèse peu dans vos pertes, et votre chauffage vous coûte peu… » |
| Fioul (2 213 €/an) | Régulation | maintenant | – | « Votre chauffage tourne sans programmation… » |
| | Combles | prioritaire | – | « Avec une chaudière fioul, chaque kWh perdu par le toit… » |
| | PAC air/eau | prioritaire | – | « Avec une chaudière fioul, chaque kWh de chaleur vous coûte cher… » |
| | Murs | à l'occasion | trop_cher | « Isoler les murs coûte cher au m² : même avec une chaudière fioul… » |
| | Fenêtres | à l'occasion | apres_autres | « Vos fenêtres pèsent peu dans vos pertes… » (`pourquoi_occasion`) |
| F au fioul (7 695 €/an) | Régulation, combles, murs, fenêtres, PAC air/eau | maintenant / prioritaire | – | les `pourquoi_rentable` (« Avec une chaudière fioul… », « Du simple vitrage… ») |
| Convecteurs (1 981 €/an) | Régulation | maintenant | – | « Votre chauffage tourne sans programmation… » |
| | Combles | prioritaire | – | « Avec des convecteurs électriques, chaque kWh perdu par le toit… » |
| | PAC air/air | prioritaire | – | « Avec des convecteurs, chaque kWh de chaleur se paie au prix de l'électricité… » |
| | Murs | à l'occasion | trop_cher | « Isoler les murs coûte cher au m² : même avec des convecteurs électriques… » |
| | Fenêtres | à l'occasion | apres_autres | « Vos fenêtres pèsent peu dans vos pertes… » |

Les quatre PDF font 5 pages. Le ballon de la référence reste la première étape (retour
5,5 ans au lieu de 4,8). La PAC air/air des convecteurs passe à « prioritaire » (retour 10,8 ans).

## Ce qui attend Stéphane

- **Fenêtres en `apres_autres`** : `pourquoi_occasion` dit « Vos fenêtres pèsent peu dans vos
  pertes ». Pour du simple vitrage au fioul, ce n'est pas forcément vrai : c'est le gain déjà
  pris par la régulation, le toit et la PAC qui les relègue. Un `pourquoi_apres_autres` dans
  `action_menuiseries.md` réglerait le cas.
- **`kb/ecs_solaire.md`** : la phrase dit maintenant « le surcoût réel tombe souvent entre
  1 800 et 2 800 € », mais elle part toujours de « 3 500 € » moins un cumulus de « 800 à
  1 200 € », ce qui donne 2 300 à 2 700. Le calcul affiché dans la même phrase ne tombe plus
  sur le résultat. La suite (« le retour à dix ou douze ans ») est inchangée.
- **Valeurs toujours « à calibrer »** : surface par unité de PAC air/air (30 m²) et plafond
  (6 unités) ; coût complet du ballon thermodynamique (2 500-4 000 €).
- **Facteurs d'émission** : toujours à vérifier sur le texte du JO.

## Pistes pour le prochain brief

1. **Texte `pourquoi_apres_autres` des fenêtres**, et revue de `ecs_solaire.md` (voir plus haut).
2. **Blanc en fin de plan** : « Comprendre votre maison » ouvre toujours une page. Le laisser
   suivre le contenu quand la page précédente est à moitié vide gagnerait de la place.
3. **La maison F au fioul de test n'a pas de `type_logement`** : elle ne déclenche donc ni la
   rénovation d'ampleur ni la piste solaire. Ajouter `type_logement="maison"` aux maisons de
   relecture montrerait ces blocs.
4. **Points 31 et 32 de `TODO.md`** : intouchés, comme demandé.
