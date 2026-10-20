# Brief Claude Code — Carnet de maison, lot 5 : Hélios lit le carnet

## Contexte (à lire avant tout)

Prérequis : **lots 1, 3 et 4 validés** ; le lot 2 (pièces) est pris en compte s'il est en place.

Aujourd'hui, le chat du foyer connecté reçoit la fiche maison (`rag.build_house_context`) et les dernières études. Il ignore les équipements, leurs âges, les garanties, les échéances et le journal. Ce lot lui donne **un résumé compact du carnet**, pour qu'il réponde à « Quand dois-je faire entretenir ma PAC ? » ou « Mon ballon a quel âge ? » sans reposer la question.

Configuration actuelle : **chat en local sur Ollama (`llama3.2:3b`)**, pas de clé d'API. Le petit modèle a une fenêtre courte : le résumé doit être **court et trié par importance**. Le jour où la route API sera branchée (IA mixte, décision du 20/10), le même résumé partira vers une API externe : il doit donc être **anonymisé dès maintenant**.

Fichiers concernés (à confirmer dans ton plan) :
- `api/app/services/carnet_contexte.py` (nouveau, fonctions pures)
- `api/app/services/rag.py` (`build_house_context` et le bloc « MODE CONNECTÉ »)
- `api/app/routers/chat.py` (chargement des objets du carnet)
- `api/tests/test_carnet_contexte.py`, `TODO.md`

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Taille | Le résumé du carnet, sérialisé en JSON, tient en **1 500 caractères au plus**. Au-delà, on coupe dans cet ordre : journal, pièces, équipements de faible priorité. |
| Jamais envoyé | Numéro de série, notes libres, nom d'installateur, nom d'intervenant, nom d'entreprise, titres libres du journal, noms de fichiers, montants des travaux. |
| Statuts | Chaque élément porte `declare`, `calcule` ou `suppose`, et le prompt dit au modèle de le respecter. |
| Chiffres | Le modèle cite les âges et les dates fournis, **n'en calcule aucun autre** (coût de remplacement, durée de vie restante, économie). |

## Méthode de travail

- Lire `rag.build_house_context`, le bloc « MODE CONNECTÉ » de `rag.py`, `chat.py` (chargement de la fiche et des études), les débriefs des lots 1 à 4.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, joindre le JSON du résumé pour une maison complète, et les réponses **réelles d'Ollama** aux cinq questions de la section 4. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-carnet-lot5.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Le résumé, en fonctions pures

`carnet_contexte(equipements, echeances, garanties, journal, resume_pieces=None, aujourd_hui) -> dict` :

- `equipements` : en service seulement, au plus 12 : `categorie`, `type`, `marque` (sans modèle), `age_ans` + statut, `contrat_entretien`. Ordre : chauffage, ECS, clim, production d'électricité, stockage, le reste.
- `echeances` : au plus 5, les plus urgentes : libellé, type d'équipement, date, statut, `nature`, `qui`.
- `garanties` : en cours seulement, au plus 5 : nature, date de fin, type d'équipement ou nature des travaux **réduite à sa catégorie**.
- `journal` : au plus 5 entrées des 24 derniers mois : date, `type`, type d'équipement, `justifie` (bool). **Pas de titre.**
- `pieces` (si le lot 2 existe) : nombre, surface déclarée totale, émetteurs par type, nombre de pièces chauffées sans émetteur.
- Aucune clé vide : un bloc sans contenu est omis.
- Respect du plafond de 1 500 caractères par la coupe ordonnée de la décision.

`build_house_context` ajoute ce résumé sous la clé `carnet`, sans rien changer au reste de son contenu.

## 2. Le prompt

Dans le bloc « MODE CONNECTÉ » de `rag.py`, ajouter **trois phrases au plus**, écrites ainsi :

« La clé "carnet" résume les équipements, échéances d'entretien, garanties et travaux de CE foyer. Ces informations sont déclarées par le foyer sauf mention contraire : dis "d'après votre carnet" quand tu t'en sers. Ne calcule aucun coût, aucune durée de vie restante ni aucune économie à partir de ces données. »

Ne pas toucher au reste du prompt, ni à la constitution.

## 3. Le chargement

Dans `chat.py`, pour le foyer connecté, charger équipements, travaux, journal (et pièces si disponibles), appeler les moteurs des lots 1 à 4, puis `carnet_contexte`. Une erreur dans ce chargement ne doit **jamais** faire échouer le chat : en cas d'exception, le contexte part sans `carnet` et l'erreur est journalisée.

## 4. Vérification réelle avec Ollama

Sur une maison de démonstration complète (PAC air/eau posée en 2016, ballon thermodynamique de 2019, panneaux de 2023, un chantier réceptionné il y a 10 mois, trois entrées de journal), poser et noter mot pour mot les réponses à :

1. « Quand dois-je faire entretenir ma pompe à chaleur ? »
2. « Quel âge a mon chauffe-eau ? »
3. « Est-ce que mes travaux sont encore sous garantie ? »
4. « Qu'est-ce que j'ai fait comme entretien cette année ? »
5. « Combien va me coûter le remplacement de ma PAC ? » (attendu : pas de chiffre inventé)

Si la table d'entretien est encore vide, la question 1 doit recevoir une réponse honnête (pas d'échéance inventée). Signaler dans le résumé toute réponse fausse ou tout chiffre inventé, **sans retoucher le prompt au-delà des trois phrases** : on en décidera ensemble.

## 5. Tests

- Aucune des clés interdites n'apparaît dans le JSON, quelle que soit la maison (test qui remplit tous les champs libres avec des valeurs repérables).
- Plafond de 1 500 caractères respecté sur une maison surchargée (60 équipements, 500 entrées de journal), et ordre de coupe vérifié.
- Maison sans carnet : pas de clé `carnet`, contexte identique à avant.
- Le chat répond encore si le chargement du carnet lève une exception (test avec un moteur qui échoue).
- Tests existants verts.

## 6. TODO.md

Ligne « Carnet, lot 5 » cochée après la vérification avec Ollama. Noter les réponses défaillantes éventuelles en point ouvert.

---

## À ne pas faire

- **Aucune nouvelle dépendance**, aucun changement de modèle Ollama ni de route API.
- Ne jamais envoyer au LLM une donnée de la liste « Jamais envoyé ».
- Ne pas laisser le LLM produire un chiffre absent du carnet.
- Ne pas modifier la constitution ni le reste du prompt.
- Pas de nouvelle interface : ce lot ne change que ce que le chat sait.
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Le chat répond aux questions 1 à 4 à partir du carnet, en disant « d'après votre carnet ».
2. La question 5 ne reçoit aucun chiffre inventé.
3. Le résumé ne contient aucune donnée de la liste interdite et tient sous 1 500 caractères.
4. Le chat ne tombe jamais à cause du carnet.
5. Tests verts, JSON et réponses jointes, débrief écrit.
