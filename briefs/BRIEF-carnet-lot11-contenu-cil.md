# Brief Claude Code — Carnet de maison, lot 11 : le dossier reprend le contenu du carnet d'information du logement (point 44)

## Contexte (à lire avant tout)

Point 44 de `TODO.md` : la mention de pied de page du dossier PDF et la liste des rubriques du carnet d'information du logement (CIL) devaient être vérifiées sur le texte officiel. C'est fait (21/10/2026), à partir de la synthèse des textes publiée par [Actu-Juridique](https://www.actu-juridique.fr/civil/immobilier/immobilier-le-contenu-et-les-modalites-dapplication-du-carnet-dinformation-du-logement-sont-precises/) et du texte de l'arrêté du 27 décembre 2022 ([AIDA, INERIS](https://aida.ineris.fr/reglementation/arrete-271222-relatif-carnet-dinformation-logement)).

**Ce que disent les textes** (CCH, art. L. 126-35-2 à L. 126-35-11 et R. 126-32 à R. 126-34 ; arrêté du 27/12/2022) :

- le carnet est établi **par le propriétaire**, sous **format numérique** (standard ouvert), et transmis à l'acquéreur au plus tard à l'acte de vente ;
- il concerne les logements construits (permis ou déclaration préalable depuis le 01/01/2023) et les **rénovations ayant une incidence significative sur la performance énergétique** (devis accepté ou travaux commencés depuis le 01/01/2023) ;
- ces rénovations sont, selon les articles 2 à 6 de l'arrêté : **isolation des toitures** (combles, rampants, toiture terrasse) ; **isolation des murs** donnant sur l'extérieur ; **parois vitrées et portes** donnant sur l'extérieur ; **planchers bas** ; **chauffage, refroidissement et eau chaude sanitaire** (installation, régulation, remplacement, y compris émetteurs, réseau de distribution et pilotage) ;
- contenu pour une rénovation : dates et description des travaux ; matériaux d'isolation (nature, marque et référence, résistance thermique, conductivité, épaisseur, surface, traitement des interfaces) ; équipements (nature, marque, modèle, énergie, **mode d'évacuation**, numéro de série, puissance, **étiquetage énergétique**) ; notices ; DPE, audit et attestations de performance s'ils existent ; attestations d'entretien (chaudière, ramonage et entretien des appareils à combustible solide, systèmes thermodynamiques) ;
- pour une construction neuve, en plus : plans de surface et coupes, plans et descriptifs des réseaux d'eau, d'électricité, de gaz et d'aération.

Le carnet d'Hélios peut donc devenir, pour le propriétaire, **son** carnet d'information du logement, à condition de recueillir les champs qui manquent. C'est l'objet de ce lot.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Nouvelle mention de pied de page | « Ce dossier rassemble les informations déclarées par le propriétaire dans Hélios, selon les rubriques du carnet d'information du logement (code de la construction et de l'habitation, art. L. 126-35-2 et suivants). Il ne remplace pas les documents remis par les professionnels et ne vaut pas attestation. » |
| Équipements | Deux champs de plus : `mode_evacuation` (`ventouse`, `conduit`, `sans_objet`, `inconnu`) et `etiquette_energie` (`A+++` à `G`, `inconnue`). |
| Travaux | Un champ `categorie_cil` : `isolation_toiture`, `isolation_murs`, `parois_vitrees_portes`, `planchers_bas`, `chauffage_froid_ecs`, `autre` (= hors CIL). |
| Isolants | Nouvelle table `isolants` liée à des travaux : nature, marque et référence, résistance thermique (m².K/W), conductivité (W/m.K), épaisseur (mm), surface (m²), note sur le traitement des interfaces. Tous facultatifs, tous déclarés. |
| Plans | Les documents gagnent un type `plan` (plans, coupes, schémas de réseaux). |
| Complétude CIL | Un indicateur calculé, sans valeur légale : pour chaque chantier `categorie_cil` ≠ `autre` réceptionné depuis le 01/01/2023, ce qui manque (description, isolants ou caractéristiques d'équipement, attestations d'entretien). Affiché en liste « À compléter pour votre carnet d'information du logement ». |

## Méthode de travail

- Lire le débrief du lot 6, `services/pdf_dossier.py` (`MENTION`), les modèles `equipement.py`, `travaux.py`, `house_document.py`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, rendu du PDF d'une maison rénovée en 2024 (PAC + isolation des combles) et capture de la liste « À compléter ». **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot11.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Modèles et migration

Champs et table du tableau de décisions, migration réversible ; formulaires du lot 1 complétés (mêmes composants).

## 2. Complétude, en fonctions pures

`services/cil.py` → `a_completer(travaux, equipements, isolants, documents, journal)` : liste des manques par chantier concerné, chaque manque relié à son formulaire. Testé sur des cas simples.

## 3. Le PDF

- Remplacer `MENTION` par le texte du tableau.
- Section « Travaux et garanties » : catégorie CIL, isolants (tableau), mode d'évacuation et étiquette des équipements.
- Section « Documents » : les plans listés à part.

## 4. Tests

- La nouvelle mention est présente mot pour mot (test sur le texte extrait).
- Une PAC posée lors d'un chantier `chauffage_froid_ecs` de 2024 sans mode d'évacuation ni étiquette → deux manques ; complétés → plus rien.
- Un chantier `autre` ou antérieur à 2023 n'apparaît pas dans « À compléter ».
- Les PDF de pré-audit sont inchangés ; tests existants verts, build front vert.

## 5. TODO.md

Cocher le point 44 après vérification, en notant la source des rubriques.

---

## À ne pas faire

- Ne jamais écrire « conforme », « certifié » ni « officiel ».
- Ne pas rendre un champ obligatoire : tout reste facultatif, l'indicateur montre seulement ce qui manque.
- Pas d'export dans un autre format que le PDF dans ce lot.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le dossier porte la nouvelle mention et reprend les rubriques du CIL.
2. Un propriétaire qui a rénové depuis 2023 voit exactement ce qui manque à son carnet d'information du logement.
3. Tests et build verts, rendu et capture joints, débrief écrit, point 44 coché.
