# Brief Claude Code — Carnet de maison, lot 9 : les projets de la maison

## Contexte (à lire avant tout)

Le carnet sait ce qu'est la maison (équipements, pièces), ce qu'il faut entretenir et ce qui a été fait (journal, travaux). Il ne sait pas encore **ce que le foyer prépare**. Les calculs existent pourtant : simulateur solaire (PV, batterie, carport, eau de l'air, éolien, jardin), pré-audit (PAC air/eau, PAC air/air, ballon thermodynamique, isolation, régulation…), et des fiches de connaissance sur l'urbanisme, les aides, le financement, le choix d'un installateur et les garanties.

Ce lot crée le **projet** : un fil qui va de l'idée à la réception des travaux, réutilise les calculs existants et, une fois terminé, **alimente le carnet sans ressaisie** (travaux, garanties, équipements, journal).

Décision du 20/10/2026 : premiers modèles **solaire et stockage, sortie du fioul ou du gaz, écosystème** (carport, eau de l'air, éolien, jardin d'hiver). Isolation et menuiseries viendront ensuite.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Étapes d'un projet | `idee`, `etude`, `devis`, `decide`, `travaux`, `termine`, `abandonne`. |
| Budget et économie | **Uniquement** depuis un calcul déjà fait (étude du simulateur ou pré-audit du foyer), affiché avec sa date et son statut (`calcule`, `suppose`), ou depuis un devis saisi par le foyer (`declare`). Jamais produit par le LLM ni par ce lot. Sans calcul : un bouton vers le bon outil. |
| Textes | Aucun texte d'explication dans le code : chaque modèle renvoie à des fiches `kb/` existantes par leur identifiant. Un modèle dont une fiche indispensable n'existe pas **ne s'affiche pas**. |
| Neutralité | Aucun nom d'entreprise dans un projet. La mise en relation existante (« Mises en relation ») n'est proposée que par un bouton, à l'initiative du foyer. |
| Locataire | Les projets lourds sont masqués (règle du lot 8 si en place, sinon `statut == locataire`). |
| Limite | 20 projets par maison. |

## Méthode de travail

- Lire `services/audit_engine.py` (actions et leurs coûts), les modèles d'études du simulateur (`models/simulateur.py`, `solar.py`, `water.py`), `routers/travaux.py`, `routers/equipements.py`, `routers/journal.py`, la liste des fiches de `kb/`.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures (liste des projets, un projet solaire avec son étude liée, un projet terminé et ce qu'il a créé dans le carnet). **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot9.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Les modèles de projet

Fichier `api/data/projets/modeles.json` (format sur le modèle de `entretien/taches.json`), une entrée par modèle :

- `id`, `titre`, `famille` (`solaire_stockage`, `sortie_fossile`, `ecosysteme`) ;
- `outil` : où se fait le calcul (`simulateur-solaire`, `pre-audit:<clé d'action>`, `eau`, `vent`, `jardin`) ;
- `fiches_kb` : identifiants des fiches à lire (au moins une parmi `urbanisme_assurance`, `financement_projet`, `baremes_aides`, `choisir_installateur`, `garanties_travaux`, plus la fiche du sujet) ;
- `equipements_crees` : les types d'équipement (codes du lot 1) proposés à la réception ;
- `masque_si` : conditions simples (`statut: locataire`, `type_logement: appartement`).

Modèles à créer (titre court ; ne garder que ceux dont les fiches existent) : panneaux solaires ; batterie ; sortie du fioul vers une PAC air/eau ; sortie du gaz vers une PAC air/eau ; PAC air/air à la place de convecteurs ; ballon thermodynamique ; carport solaire ; machine à eau de l'air ; éolienne verticale ; jardin d'hiver. Le brief ne fixe pas les fiches : **les lister dans le résumé** avec, pour chaque modèle, les fiches trouvées et celles qui manquent.

## 2. Le modèle de données

**`Projet`** (table `projets`) : `id`, `house_id`, `modele_id`, `titre`, `etape`, `etude_ref` (type + id d'une étude ou d'un audit existant, optionnel), `budget_bas_eur`, `budget_haut_eur` et `budget_source` (`etude`, `audit`, `devis`), `economie_annuelle_eur` et sa source, `devis_document_ids` (documents de type `devis`), `note`, `travaux_id` (rempli à la fin), `created_at`, `updated_at`. Migration réversible.

## 3. L'API

- `GET /houses/me/projets/modeles` : les modèles visibles pour ce foyer, avec l'état des calculs déjà faits (« une étude solaire du 12/10 existe »).
- CRUD `/houses/me/projets`.
- `POST /houses/me/projets/{id}/lier-etude` : rattache l'étude ou l'audit le plus récent de l'outil du modèle, et recopie budget et économie **tels quels** avec leur date.
- `POST /houses/me/projets/{id}/terminer` (date de réception, entreprise, montant TTC, documents) : crée les **travaux** (lot 1, garanties calculées), propose les **équipements** de `equipements_crees` pré-remplis (le foyer confirme chacun), écrit une entrée de **journal** `amelioration`, passe le projet à `termine`. Tout dans une transaction.

## 4. L'écran

- Onglet « Ma maison » (ou section « Mes projets ») : les projets en cours par étape, puis « Envisager un projet » avec les modèles groupés par famille.
- Fiche d'un projet : étape (modifiable), budget et économie avec leur source et leur date, bouton vers l'outil de calcul, devis joints, fiches à lire (« Avant de signer »), bouton « Être mis en relation » (flux existant), bouton « Les travaux sont terminés ».
- Charte « Carnet de maison », mobile d'abord.

## 5. Tests

- Un modèle dont une fiche manque n'est pas servi.
- `lier-etude` recopie exactement les valeurs de l'étude (aucun recalcul).
- `terminer` crée travaux, garanties, journal et, après confirmation, les équipements ; un échec annule tout.
- Locataire : projets lourds absents.
- Tests existants verts, build front vert.

---

## À ne pas faire

- Aucun chiffre calculé dans ce lot ; aucun texte produit par le LLM.
- Aucun nom d'entreprise, aucun partenaire mis en avant.
- Ne pas écrire de fiche de connaissance : lister celles qui manquent.
- Pas de lecture de devis (Super Hélios, plus tard).
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le foyer suit un projet de l'idée à la réception, avec des chiffres toujours sourcés et datés.
2. Un projet terminé remplit le carnet : travaux, garanties, équipements, journal.
3. La liste des fiches manquantes par modèle est dans le résumé.
4. Tests et build verts, captures jointes, débrief écrit.
