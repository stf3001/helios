# Brief Claude Code — Carnet de maison, lot 1 : les équipements datés et leurs garanties

## Contexte (à lire avant tout)

Le 20/10/2026, Stéphane a validé la direction « carnet de maison » (rapport « Hélios, version HomeZada ») et ses décisions :

- **une maison par compte** (la multipropriété sera une brique séparée, plus tard) ;
- **premier lot = équipements datés et garanties** ;
- tout ce lot tourne **en local, sans e-mail, sans clé d'API**.

Aujourd'hui, la fiche connaît chaque système par **un type et une année** (`chauffage_principal` + `chauffage_principal_annee`, `ecs` + `ecs_annee`, `clim`, `ventilation`…). Elle ignore la marque, le modèle, la garantie, l'installateur, et ne retient rien des travaux faits.

Ce lot crée deux objets rattachés à la maison :

1. **l'équipement** : un appareil précis, daté, avec sa garantie fabricant ;
2. **les travaux réceptionnés**, qui ouvrent les **garanties de chantier** : parfait achèvement (1 an), bon fonctionnement (2 ans), décennale (10 ans), comptées depuis la réception.

Le calendrier d'entretien (lot 3), le journal (lot 4), le contexte du chat (lot 5) et le dossier PDF (lot 6) liront ces objets. **Ce lot n'affiche aucun rappel d'entretien.**

Fichiers concernés (à confirmer dans ton plan) :
- `api/app/models/equipement.py`, `api/app/models/travaux.py` (nouveaux), `api/app/models/__init__.py`
- `api/alembic/versions/0024_equipements_travaux.py`
- `api/app/schemas/equipement.py`, `api/app/schemas/travaux.py`
- `api/app/routers/equipements.py`, `api/app/routers/travaux.py`, enregistrement dans `main.py`
- `api/app/services/garanties.py` (nouveau, fonctions pures)
- `kb/garanties_travaux.md` (nouvelle fiche, ou complément d'une fiche existante si le sujet y est déjà)
- `frontend/src/pages/Espace.tsx` (onglet « Ma maison ») et nouveaux composants dans `frontend/src/components/carnet/`
- `api/tests/test_garanties.py`, `TODO.md`

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Comptes | Une maison par compte. Rien ne doit supposer plusieurs maisons. |
| Fiche existante | **Inchangée.** Les champs `*_annee` restent. Aucune synchronisation automatique dans ce lot. |
| Statut des données | Tout ce que le foyer saisit est **déclaré**. L'âge et les dates de fin de garantie sont **calculés**. Une année de pose sans date exacte rend la date **supposée** (1er juillet de l'année). |
| Garanties de chantier | Durées 1, 2 et 10 ans depuis la date de réception. Affichées avec la mention « À vérifier sur votre contrat et l'attestation d'assurance de l'entreprise ». |
| Numéro de série | Stocké, affiché au foyer, **jamais** envoyé au chat (lot 5) ni au LLM. |
| Limites | 60 équipements et 40 travaux par maison. |

## Méthode de travail

- Lire `CLAUDE.md`, `TODO.md`, `models/house.py`, `routers/houses.py`, `routers/documents.py` (le motif `_own_house` / `_own_document` est la référence pour les contrôles d'accès), `pages/Espace.tsx` et `components/fiche/`.
- Proposer un plan court, puis un commit par étape, message en français dans le style des précédents.
- À la fin : s'arrêter, résumer, joindre des captures de l'onglet « Ma maison » (vide, puis avec trois équipements et un chantier). **Attendre la validation de Stéphane.**
- Débrief : `debriefs/AAAA-MM-JJ-carnet-lot1.md`, même plan que les débriefs du pré-audit.
- `CLAUDE.md` : au maximum 2 lignes. Pas de journal daté.

---

## 1. Les modèles et la migration

**`Equipement`** (table `equipements`) :

| Champ | Type | Note |
|---|---|---|
| `id` | UUID | |
| `house_id` | FK `houses.id`, index | suppression en cascade avec la maison |
| `categorie` | str, liste fermée | `chauffage`, `ecs`, `clim`, `ventilation`, `production_electricite`, `stockage`, `recharge`, `eau`, `autre` |
| `type` | str, liste fermée par catégorie | reprendre **les mêmes codes que la fiche** quand ils existent (`PAC_air_eau`, `PAC_air_air`, `ballon_elec`, `thermodynamique`, `VMC_simple`…), en ajouter pour le reste : chaudière gaz, chaudière fioul, poêle bois, poêle à granulés, convecteurs, radiateurs à inertie, split, multisplit, gainable, panneaux PV, onduleur, éolienne, batterie, borne de recharge, adoucisseur, fosse septique, micro-station, pompe de piscine, générateur d'eau atmosphérique, autre |
| `marque`, `modele` | str, optionnels | |
| `numero_serie` | str, optionnel | jamais dans le contexte du chat |
| `puissance` + `unite` | float + str (`kW`, `kWc`, `kWh`, `L`), optionnels | |
| `date_pose` | date, optionnelle | |
| `annee_pose` | int, optionnelle | utilisée si `date_pose` est vide |
| `installateur` | str, optionnel | texte libre |
| `garantie_fabricant_fin` | date, optionnelle | |
| `contrat_entretien` | bool, optionnel | + `contrat_prestataire` str optionnel |
| `travaux_id` | FK `travaux.id`, optionnelle, `SET NULL` | |
| `origine_fiche` | str, optionnel | `chauffage_principal`, `chauffage_appoint`, `ecs`, `clim`, `ventilation` : l'équipement a été créé depuis une suggestion de la fiche |
| `en_service` | bool, défaut vrai | faux = déposé ou remplacé ; on garde l'historique |
| `note` | texte, optionnel | jamais envoyée au chat |
| `created_at`, `updated_at` | | |

**`Travaux`** (table `travaux`) : `id`, `house_id`, `nature` (texte court, obligatoire), `entreprise` (optionnel), `date_reception` (date, optionnelle : sans elle, pas de garantie calculée), `montant_ttc` (optionnel), `facture_document_id` et `attestation_assurance_document_id` (FK `house_documents.id`, optionnelles, `SET NULL`), `note`, `created_at`.

Migration `0024`, réversible.

## 2. Les garanties, en fonctions pures

`api/app/services/garanties.py` :

- `fin_garanties_chantier(date_reception) -> list` : trois entrées (`parfait_achevement`, `bon_fonctionnement`, `decennale`) avec leur date de fin. **Un 29 février donne un 28 février** les années non bissextiles ; aucune dépendance de calcul de dates ajoutée.
- `statut_garantie(fin, aujourd_hui)` : `en_cours`, `bientot` (fin dans 60 jours ou moins), `expiree`.
- `garanties_maison(equipements, travaux, aujourd_hui)` : la liste à afficher, garanties fabricant comprises, triée par date de fin. Chaque entrée porte sa provenance (`travaux` ou `equipement`), son libellé et la mention de statut des données (`calcule`, ou `suppose` si la date de pose est supposée).
- `age_ans(equipement, aujourd_hui)` : âge entier, et le statut `calcule` ou `suppose`.

Aucun accès à la base dans ce module.

## 3. La fiche de connaissance

Créer `kb/garanties_travaux.md` (ou compléter la fiche existante qui traite du sujet), au format habituel `### Q:` / `meta` / `R:`, deux à trois questions : ce que couvre chaque garantie, à partir de quand elle court, quoi garder (facture, procès-verbal de réception, attestation d'assurance). Mettre **`verif: a_verifier`** et citer les articles du Code civil (1792, 1792-3, 1792-6) **sans les paraphraser au-delà de leur sens**. Stéphane relit avant que la fiche passe en vérifiée. Aucun texte d'explication en dur dans le code : l'interface renvoie à la fiche par un lien « En savoir plus ».

## 4. L'API

- `GET/POST /houses/me/equipements`, `PATCH/DELETE /houses/me/equipements/{id}`
- `GET/POST /houses/me/travaux`, `PATCH/DELETE /houses/me/travaux/{id}`
- `GET /houses/me/garanties` : sortie de `garanties_maison`
- `GET /houses/me/equipements/suggestions` : pour chaque champ de la fiche parmi `chauffage_principal`, `chauffage_appoint`, `ecs`, `clim`, `ventilation`, renseigné et **sans** équipement en service portant cet `origine_fiche`, une suggestion pré-remplie (catégorie, type, année). Rien n'est créé tant que le foyer ne clique pas.
- Contrôles d'accès sur le modèle de `documents.py` : un identifiant d'un autre foyer répond 404.
- La sortie d'un équipement porte `age_ans` et son statut, calculés côté serveur.
- Un document lié à des travaux doit appartenir à la même maison (sinon 400).

## 5. L'écran

Dans l'onglet « Ma maison » de `/espace`, deux blocs, dans la charte « Carnet de maison » (palette de `index.css`, actions en terracotta, bordures et pas d'ombre, aucune couleur en dur) :

- **« Mes équipements »** : cartes groupées par catégorie (type, marque et modèle, « posé en 2014 · 12 ans », garantie fabricant). Ajout et modification dans un formulaire qui réutilise `FieldInput`. Un équipement hors service passe dans un repli « Anciens équipements ».
- **Bandeau de suggestions** au-dessus, s'il y en a : « Votre fiche indique une PAC air/eau de 2016. L'ajouter à vos équipements ? » → formulaire pré-rempli.
- Si l'année d'un équipement créé depuis la fiche diffère de celle de la fiche : petite note « Votre fiche indique 2016 ». **Pas de correction automatique.**
- **« Travaux et garanties »** : la liste des chantiers et des garanties en cours, les plus proches de leur fin en premier, avec la mention de vérification et le lien vers la fiche de connaissance.
- États vides utiles : une phrase et un bouton, pas d'illustration.
- Mobile d'abord : tout doit être lisible et utilisable à 375 px.

## 6. Tests

- `test_garanties.py` : réception le 15/03/2025 → 15/03/2026, 15/03/2027, 15/03/2035 ; réception le 29/02/2024 → fins au 28/02 ; statuts à J-61, J-60, J+1 ; année de pose seule → date supposée au 1er juillet et statut `suppose` ; tri.
- Suggestions : une fiche avec chauffage et ECS renseignés donne deux suggestions, une seule après création de l'équipement de chauffage depuis la suggestion.
- Accès : si l'infrastructure de test existante permet des tests d'API sans nouvelle dépendance, vérifier qu'un foyer ne lit ni ne modifie l'équipement d'un autre. Sinon, le dire dans le débrief.
- Tous les tests existants restent verts, le build front passe.

## 7. TODO.md

Ajouter une ligne « Carnet, lot 1 » cochée seulement après vérification à l'écran, en citant le commit. Noter en point ouvert : **réconcilier un jour la fiche et les équipements** (une seule source pour l'année du chauffage).

---

## À ne pas faire

- **Aucune nouvelle dépendance** (ni bibliothèque de dates, ni composant d'interface).
- Ne pas modifier la fiche maison, son score de complétude, ni le moteur de pré-audit.
- Ne pas créer d'équipement automatiquement à partir de la fiche.
- Pas de rappel, pas d'e-mail, pas de calendrier d'entretien : ce sont les lots 3 et 4.
- Pas de lecture de photo ni d'OCR de plaque signalétique (Super Hélios, plus tard).
- Pas de pièce ni d'émetteur (lot 2).
- Ne jamais présenter une garantie comme acquise : toujours la mention de vérification.
- Aucun texte d'explication juridique en dur dans le code.
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Un foyer ajoute, modifie, met hors service et supprime un équipement ; l'âge s'affiche, calculé.
2. Les suggestions issues de la fiche apparaissent, se transforment en équipement en un clic, puis disparaissent.
3. Un chantier réceptionné affiche ses trois garanties avec leurs dates de fin et leur statut.
4. Aucune donnée d'un autre foyer n'est accessible.
5. La fiche `kb/garanties_travaux.md` existe, marquée à vérifier.
6. Tests et build verts, captures jointes, débrief écrit.
