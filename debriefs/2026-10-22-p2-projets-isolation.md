# Débrief — Phase 2 « projets isolation, menuiseries, ventilation et régulation »

22/10/2026. Un commit sur `main`, non poussé. Le lot attend la validation de Stéphane.

**826 tests au vert** (dont 12 nouveaux purs dans `test_projets.py` et 3 contre la base dans
`test_projets_isolation_api.py`), `tsc -b` et `npm run build` passent (520 URL, inchangé). Aucun
débordement à 375 px.

## Les six modèles « Isolation et confort »

Famille `enveloppe`, quatrième de la liste. Aucun nouveau calcul, aucun nouveau prix, aucune fiche
écrite : toutes celles qu'ils citent existent, donc aucun n'est masqué.

| Modèle | Calcul | Fiches | Rubrique proposée | Équipement | Locataire | Appartement |
|---|---|---|---|---|---|---|
| Isolation des combles ou de la toiture | `pre-audit:isolation_combles` | `action_combles` + communes | `isolation_toiture` | — | masqué | masqué |
| Isolation des murs | `pre-audit:isolation_murs` | `action_murs`, `urbanisme_assurance` + communes | `isolation_murs` | — | masqué | masqué |
| Isolation du plancher bas | `pre-audit:isolation_plancher` | `action_plancher` + communes | `planchers_bas` | — | masqué | masqué |
| Changement des fenêtres | `pre-audit:menuiseries` | `action_menuiseries`, `urbanisme_assurance` + communes | `parois_vitrees_portes` | — | masqué | visible |
| Ventilation (VMC) | `pre-audit:ventilation_double_flux` | `action_ventilation` + communes | aucune | VMC double flux, à la place de celle de la fiche | masqué | visible |
| Régulation du chauffage | `pre-audit:regulation` | `action_regulation` + communes | `chauffage_froid_ecs` | — | **visible, avec la mention** | visible |

Fiches communes : `financement_projet`, `choisir_installateur`, `garanties_travaux`.

## Ce qui a changé dans le code

- `modeles.json` : deux champs facultatifs, documentés dans le `LISEZMOI.md` du dossier.
  `categorie_cil` est la rubrique proposée à la réception. `mention_locataire` marque le seul
  modèle léger qu'un locataire voit avec « Les travaux sur le chauffage se décident avec votre
  propriétaire. » (`projets.MENTION_LOCATAIRE`).
- Le chargeur vérifie désormais qu'un `outil` `pre-audit:<clé>` nomme une vraie clé de
  `ACTIONS`. Une faute de frappe aurait donné un modèle à jamais « pas encore de calcul », sans
  erreur.
- `terminer` accepte `categorie_cil` : absente, celle du modèle ; `null`, aucune ; une valeur
  hors liste est refusée (400).
- À l'écran, la rubrique est pré-remplie dans « Les travaux sont terminés ». Pour les trois
  isolations, la saisie des isolants s'ouvre sur le nouveau chantier, par un événement de
  fenêtre comme `ouvrirJournal` (`ouvrirIsolants`, `components/carnet/commun.ts`).

## Vérifié sur le compte de démo

Captures dans `debriefs/captures/` :
- `p2-projets-isolation-famille.jpg` : la famille « Isolation et confort ». Combles, murs et
  plancher annoncent « Un pré-audit du 20/10/2026 existe » ; fenêtres, VMC et régulation, non :
  le pré-audit de démo ne les retient pas.
- `p2-projets-isolation-combles-pre-audit.jpg` : projet combles lié au pré-audit. Le budget
  (2 500 à 7 000 €) et l'économie (85 €/an) sont exactement ceux de la ligne du pré-audit,
  visible juste au-dessus sur la même capture.
- `p2-projets-isolation-terminer-rubrique.jpg` : la réception, rubrique pré-remplie « Isolation de
  la toiture ».
- `p2-projets-isolation-termine-cil.jpg` : le chantier créé, avec sa rubrique, ses trois
  garanties et la saisie des isolants ouverte.

Le compte de démo a été remis à l'identique (0 projet, 1 chantier, 3 équipements, 5 entrées de
journal, 0 isolant, relus en base).

## Deux choses trouvées en vérifiant

- **Le défilement vers les isolants** : un premier essai partait avant que le chantier soit
  rechargé. L'écran attend maintenant que le chantier soit rendu. L'appel est vérifié (intercepté
  dans la page) ; le défilement DOUX, lui, ne s'anime pas quand le panneau du navigateur est
  masqué, comme ici. Le même défilement en mode immédiat amène le chantier à 80 px du haut.
- **Clés React en double, défaut antérieur au lot** : la clé d'une garantie était faite de son
  libellé, donc deux chantiers de même nom (deux projets combles, par exemple) entraient en
  collision. Elle suit maintenant l'id du chantier ou de l'appareil (`source_id`, déjà renvoyé
  par l'API). Vérifié avec deux chantiers « Doublon de test » ajoutés puis retirés : plus aucun
  avertissement.

## Ce qui attend Stéphane

- Valider le lot.
- Point 78 de `TODO.md` : relire la mention du locataire, et confirmer que la ventilation n'a pas
  de rubrique (la liste du brief n'en donne pas).
