# Brief Claude Code — Phase 2 : les risques de la commune

## Contexte (à lire avant tout)

Décision du 20/10/2026 : l'assistant Hélios connaît les **risques de l'adresse** (inondation, argiles, feux de forêt…), dits une fois, au bon endroit, sans alarmisme. La fiche maison ne connaît que le **code postal**, qui peut couvrir plusieurs communes : ce lot fait choisir la **commune** au foyer, puis interroge **Géorisques**, l'API publique du ministère de la Transition écologique.

**Géorisques** : accès ouvert sans clé, base `https://georisques.gouv.fr/api/v1/`, documentation `https://www.georisques.gouv.fr/doc-api`, limite de 1 000 requêtes par minute et par adresse IP. Interrogeable par **code INSEE** : risques recensés, arrêtés de catastrophe naturelle, potentiel radon, zonage sismique, plans de prévention des risques ; rapport PDF par commune ou par adresse. **Lire la documentation de l'API avant d'écrire le client** : les noms exacts des routes et des champs ne sont pas recopiés ici.

L'échelle reste la **commune** : Hélios ne demande pas l'adresse précise, et le dit (« à l'échelle de votre commune »).

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Commune | Nouveau champ de fiche `code_insee` + `commune` (hors score de complétude), choisi par le foyer dans la liste des communes de son code postal (API Adresse déjà utilisée par `services/geocoding.py`, ou API Découpage administratif `geo.api.gouv.fr`, publique). Sans choix : rien ne s'affiche. |
| Données gardées | Par commune, dans une table `risques_commune` (code INSEE, liste des risques, nombre d'arrêtés CatNat des 30 dernières années, potentiel radon, zone sismique, existence d'un PPR, date de collecte). Rafraîchies au plus tous les 30 jours. |
| Panne | Une erreur réseau ou un changement de l'API ne bloque jamais l'espace : la section ne s'affiche pas, l'erreur est journalisée. |
| Textes | Tous les textes d'explication viennent de la fiche `kb/risques_maison.md`, **fournie telle quelle** dans `briefs/KB-risques-maison.md` (à recopier sans modification, déclarer dans `agents_engine.SOURCES`, réingérer). |
| Ton | Une ligne par risque présent, avec le lien vers sa question de la fiche ; aucun pourcentage, aucune couleur d'alerte rouge. Un lien vers le rapport Géorisques de la commune. |
| Liens avec le carnet | Feux de forêt présents et `zone_old` à `ne_sais_pas` → l'invitation existante à vérifier le débroussaillement remonte. Argiles présentes → une suggestion « Noter une fissure » ouvre le journal (type `autre`, photo). |
| Chat | `carnet_contexte` ajoute `risques` : la liste courte des risques présents (moins de 200 caractères), statut `observe` (source publique), dans le plafond existant. |

## Méthode de travail

- Lire `services/geocoding.py`, `services/regions.py`, `services/carnet_contexte.py`, `pages/FicheMaison.tsx`, `components/carnet/`, `agents_engine.SOURCES`, la documentation de l'API Géorisques.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures pour trois communes : une commune du Var exposée aux feux de forêt, une commune argileuse, une commune peu exposée. Joindre la réponse brute de l'API pour l'une d'elles. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-p2-risques.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Commune et données

Migration réversible : `houses.code_insee`, `houses.commune`, table `risques_commune`. Choix de la commune dans la fiche (et dans l'espace si absent).

## 2. Client Géorisques

`services/georisques.py` : appels avec délai court, réponse réduite aux champs gardés, normalisation des libellés de risques vers une liste fermée (`inondation`, `argiles`, `feux_de_foret`, `mouvement_de_terrain`, `seisme`, `radon`, `industriel`, `autre`). Tests **sans réseau** sur des réponses enregistrées (fichiers de fixture issus d'un vrai appel).

## 3. Écran

Section « Les risques de ma commune » dans « Ma maison » : la commune, les risques présents en une ligne chacun, la date de collecte, la mention « à l'échelle de la commune ; pour votre parcelle, voyez l'état des risques », le lien Géorisques.

## 4. Tests

- Normalisation : une réponse enregistrée donne la bonne liste fermée.
- Cache : pas de second appel dans les 30 jours ; rafraîchi après.
- Panne : le carnet s'affiche sans la section.
- Chat : `risques` présent, court, dans le plafond.
- Tests existants verts, build front vert.

## 5. TODO.md

Ligne « Phase 2, risques de la commune » cochée après vérification. Point ouvert : **relire `kb/risques_maison.md`** (toutes ses questions sont `verif: a_verifier`).

---

## À ne pas faire

- Ne pas demander l'adresse précise.
- Ne pas modifier le texte de la fiche fournie.
- Aucune probabilité, aucun niveau de risque inventé, aucune couleur d'alarme.
- Aucun appel réseau dans les tests.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le foyer choisit sa commune et voit, sobrement, les risques recensés, avec leur source et leur date.
2. Les risques utiles remontent dans le carnet (débroussaillement, fissures) et dans le contexte du chat.
3. Une panne de Géorisques ne casse rien.
4. Tests et build verts, captures et réponse brute jointes, débrief écrit.
