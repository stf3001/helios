# Brief Claude Code — Carnet de maison, lot 8 : un parcours par statut et par type de logement

## Contexte (à lire avant tout)

Décision du 20/10/2026 : le carnet sert aux propriétaires de maison et d'appartement, aux locataires et aux acheteurs. La fiche connaît déjà `statut` (`proprietaire`, `locataire`, `en_achat`) et `type_logement` (`maison`, `appartement`), **mais aucun écran ni moteur ne s'en sert** (vérifié : seul `pdf_dossier.py` les lit, pour un libellé). Un locataire voit donc des projets de travaux qu'il ne peut pas décider, et un acheteur ne voit rien d'utile.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Qui est responsable d'une tâche | Nouveau champ `responsable` dans chaque tâche de `api/data/entretien/taches.json` : `occupant` ou `proprietaire` (valeurs ci-dessous). |
| Locataire | Il voit les tâches `occupant` comme les siennes, et les tâches `proprietaire` en lecture : « À la charge de votre propriétaire, sauf clause contraire du bail ». Il ne voit pas les garanties de chantier ni les projets de travaux lourds ; il garde les gestes, les petits équipements et un bouton « Préparer une note pour mon propriétaire » (voir 3). |
| Appartement | Les tâches `debroussaillement` et `spanc-controle` ne s'appliquent pas. Nouveau champ de fiche `chauffage_collectif` (`oui`, `non`, `ne_sais_pas`, hors score) : `oui` → l'entretien du chauffage s'affiche « Assuré par la copropriété » et sort du bloc « À faire ». |
| Acheteur (`en_achat`) | Un parcours « Avant d'acheter » remplace le bloc « À faire » : la liste des documents à demander au vendeur (section 4), à cocher. Au passage à `proprietaire`, la liste est archivée dans le journal. |

Valeurs de `responsable` (sources : Service Public F20760, F19950, F33298 ; CSP R1331-73 ; fiche SPANC AMP) :

| Tâche | responsable |
|---|---|
| `chaudiere-entretien`, `pac-entretien`, `poele-entretien`, `ramonage` | occupant |
| `detecteur-fumee-test`, `clim-filtres`, `pac-unite-exterieure`, `ballon-groupe-securite`, `vmc-bouches`, `vmc-caisson`, `vmc-filtres-double-flux`, `fosse-niveau-boues` | occupant |
| `ballon-detartrage`, `micro-station-entretien` | occupant |
| `spanc-controle`, `debroussaillement`, `pv-suivi-production`, `pv-inspection-visuelle` | proprietaire |

C'est **le seul changement autorisé** dans `taches.json` : ajouter `responsable`, sans toucher au reste. Mettre `version` à la date du jour.

## Méthode de travail

- Lire les débriefs des lots 3 bis et 4, `services/entretien.py`, `services/a_faire.py`, `pages/Espace.tsx`, `components/carnet/`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures de l'espace pour quatre foyers : propriétaire de maison, propriétaire d'appartement en chauffage collectif, locataire de maison, acheteur. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot8.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Le moteur

- `charger_taches` accepte et exige `responsable`.
- `echeances` reçoit `statut`, `type_logement`, `chauffage_collectif` et marque chaque échéance `pour_moi: bool` et `mention` (« À la charge de votre propriétaire… », « Assuré par la copropriété »). Les tâches non applicables (appartement) disparaissent.
- `a_faire` ne met dans le bloc que les échéances `pour_moi`.
- Fonctions pures, testées.

## 2. La fiche

Champ `chauffage_collectif` (migration, hors score de complétude), demandé seulement aux appartements, `ne_sais_pas` par défaut.

## 3. La note pour le propriétaire (locataire)

Un bouton dans l'espace du locataire génère un texte sobre, à copier : les tâches `proprietaire` en retard ou proches, et les équipements qui ont plus de quinze ans, en phrases simples, sans chiffre ni recommandation d'entreprise. **Rien n'est envoyé** : le locataire copie le texte. Textes fixes écrits d'abord dans une fiche `kb/` (règle de source unique), puis recopiés.

## 4. « Avant d'acheter »

Créer d'abord la fiche `kb/achat_logement.md` (format habituel, `verif: a_verifier`) avec la liste, puis l'afficher :

- le DPE et, s'ils existent, l'audit énergétique et les diagnostics de vente ;
- le **carnet d'information du logement** si le logement a été construit ou rénové énergétiquement depuis 2023 (CCH, art. L. 126-35-2 et suivants : il est transmis à l'acquéreur au plus tard à l'acte) ;
- les attestations d'entretien de la chaudière, de la PAC, du poêle et de ramonage des deux dernières années ;
- en zone de débroussaillement obligatoire, l'**attestation du vendeur** sur le respect de l'obligation (depuis le 1er janvier 2025, Service Public F33298) ;
- en assainissement non collectif, le **rapport du SPANC de moins de 3 ans** ;
- les factures et garanties des travaux récents, notamment la décennale.

Chaque ligne se coche ; le foyer peut joindre le document reçu (type existant `autre` ou `dpe`).

## 5. Tests

- Locataire : une tâche `proprietaire` n'entre jamais dans « À faire ».
- Appartement : débroussaillement et SPANC absents ; chauffage collectif → entretien chaudière marqué copropriété et hors du bloc.
- Acheteur : le bloc « À faire » est remplacé par « Avant d'acheter » ; passage à propriétaire → liste archivée au journal.
- `taches.json` : seul `responsable` (et `version`) a changé (test de comparaison avec la version précédente).
- Tests existants verts, build front vert.

---

## À ne pas faire

- Ne modifier aucun libellé, fréquence ni source de `taches.json`.
- Pas d'envoi de message au propriétaire, ni d'e-mail.
- Ne pas cacher une obligation au propriétaire occupant.
- Pas de conseil juridique sur le bail : seulement « sauf clause contraire du bail ».
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Chaque foyer ne voit dans « À faire » que ce qui lui revient, et comprend pourquoi le reste ne lui revient pas.
2. Un appartement en chauffage collectif n'est pas relancé pour l'entretien de la chaudière.
3. Un acheteur a la liste des documents à demander, cochable.
4. Tests et build verts, captures des quatre foyers, débrief écrit.
