# Brief Claude Code — Chat : la réponse directe du pré-audit (puissance, radiateurs, relevé)

## Contexte (à lire avant tout)

Débrief `2026-10-22-chat-puissance` : le chat reçoit les bons chiffres, mais le modèle local (`llama3.2:3b`) en rate deux sur cinq. Il invente « 130 m² » et « 1 262 kW » pour les radiateurs, et déclare « pas possible » un relevé de 15 000 kWh posé dans son contexte. Le pré-audit, lui, a **déjà écrit les phrases justes** : la fourchette, la plage de PAC, une ligne par pièce, le relevé.

Principe du projet : les chiffres viennent du moteur, l'IA les explique. Pour ces questions, il n'y a rien à expliquer de plus : Hélios renvoie les phrases du pré-audit, **sans LLM**, comme la réponse instantanée par fiche (`model_used = "kb"`), mais avec les chiffres de la maison du foyer.

## Décision de Stéphane (22/10/2026)

| Sujet | Décision |
|---|---|
| Réponse | Quand la question porte sur la puissance, les radiateurs, le relevé ou la puissance d'un devis, et que le dernier pré-audit du foyer porte le bloc `puissance` : réponse directe, faite des phrases du pré-audit, sans LLM. |
| Aller plus loin | Le bouton « développer » existant (`force_llm`) reste disponible, comme pour une réponse instantanée. |
| Crédit Claude | Sans effet sur cette règle : elle reste vraie quand le crédit sera rechargé. |

## 1. Quand répondre directement

- Conditions, toutes requises :
  - dernier pré-audit avec un bloc `puissance` ;
  - `force_llm` à faux ;
  - la question correspond à l'un des sujets ci-dessous.
- Utiliser un motif **plus étroit** que `_SUJET_PUISSANCE`. Une question qui cite seulement « pompe à chaleur » ou « PAC » (« quelle marque ? », « combien ça coûte ? », « c'est bruyant ? ») **reste au LLM**, comme aujourd'hui.

| Sujet | Mots déclencheurs (insensibles à la casse, à affiner) | Réponse |
|---|---|---|
| `radiateurs` | radiateur(s), émetteur(s) | lignes par pièce |
| `releve` | relevé, combien de kWh, mon fioul / mon gaz / mes granulés / mes stères | phrase du relevé |
| `devis` | un nombre suivi de « kW » (« 14 kW », « 12 kw ») | comparaison à la plage |
| `puissance` | puissance, dimensionner, quelle taille, combien de kW | fourchette et plage |

- « kW » ne doit pas attraper « kWh » : « 15 000 kWh » n'est pas un devis.
- Plusieurs sujets dans une question : réponses mises bout à bout, dans l'ordre du tableau, chacune une seule fois.
- Garder les mots déclencheurs dans une constante commentée, avec les cinq questions du débrief précédent en exemples.

## 2. Ce que dit la réponse

Une fonction pure, par exemple `rag.reponse_preaudit(audit_context, question) -> str | None`. Elle n'utilise que les champs déjà présents dans le résumé `puissance` et dans `consommation`, et ne fait **aucun calcul nouveau**, sauf la comparaison d'un nombre à la plage.

- **Intro** : `chat_intro` (date du pré-audit).
- **`puissance`** : `texte`, puis `texte_plage` quand il existe ; sinon `note_radiateurs` quand elle existe.
- **`radiateurs`** :
  - une ligne par pièce, avec les phrases `radiateurs_*` déjà dans la fiche, remplies avec le nom de la pièce ;
  - pièces électriques : `note_radiateurs` ;
  - aucune pièce saisie : `chat_sans_pieces`.
- **`releve`** :
  - avec un relevé : `chat_releve` (quantité, unité, kWh, et l'eau chaude déduite quand il y en a) ;
  - sans relevé : `chat_sans_releve`.
- **`devis`** : le nombre est comparé à la plage `pac_air_eau_kw` :
  - au-dessus : `chat_devis_dessus` ;
  - dans la plage : `chat_devis_dans` ;
  - en dessous : `chat_devis_dessous` ;
  - sans plage (pas de PAC air/eau proposée) : ne pas répondre directement, laisser au LLM.

**Textes nouveaux** : d'abord dans la section « Pour le pré-audit » de `kb/action_pac_remplacement.md`, puis recopiés dans `audit_reference.py`, selon la règle de source unique tenue par `test_audit_textes.py`.

- **chat_intro** : « D'après votre pré-audit du {date} : »
- **chat_releve** : « Votre relevé ({quantite} {unite} de {energie} par an) représente environ {kwh} kWh. »
- **chat_releve_eau_chaude** : « Environ {ecs} kWh vont à l'eau chaude : le chauffage en garde {chauffage} kWh. »
- **chat_sans_releve** : « Votre pré-audit ne repose pas sur un relevé : vous pouvez indiquer votre consommation dans le bloc Énergie de votre fiche, puis refaire le pré-audit. »
- **chat_sans_pieces** : « Pour savoir si vos radiateurs suffisent, indiquez vos pièces et leurs radiateurs (avec leur puissance) dans « Ma maison », puis refaites le pré-audit. »
- **chat_devis_dessus** : « {kw} kW, c'est au-dessus de la plage que calcule votre pré-audit ({pac_bas} à {pac_haut} kW). Demandez à l'installateur sur quoi repose cette puissance : une machine trop puissante coûte plus cher et fonctionne moins bien. »
- **chat_devis_dans** : « {kw} kW, c'est dans la plage que calcule votre pré-audit ({pac_bas} à {pac_haut} kW). »
- **chat_devis_dessous** : « {kw} kW, c'est en dessous de la plage que calcule votre pré-audit ({pac_bas} à {pac_haut} kW). Demandez à l'installateur comment la maison sera chauffée les jours les plus froids. »

Les nombres sont au format français : virgule décimale, espace pour les milliers.

## 3. Intégration au chat

- Dans `routers/chat.py`, juste avant la réponse instantanée par fiche, un court-circuit sur le même modèle : flux `conversation` avec `instant: True`, puis `token`, puis `message_id`.
- `model_used = "preaudit"`, sans citation de fiche ; `chunks_used` vide.
- `admin_stats` : `"preaudit"` compté et affiché comme les autres (docstring et regroupement).
- La consigne et le résumé du lot précédent restent : ils servent quand la question va au LLM.

## Méthode de travail

- Lire :
  - `routers/chat.py` (`question_puissance` et la réponse instantanée) ;
  - `services/rag.py` (`resume_puissance`, `instant_answer`) ;
  - `services/admin_stats.py`, la section « Pour le pré-audit » de `kb/action_pac_remplacement.md` ;
  - le débrief `2026-10-22-chat-puissance.md` et ses deux fichiers de réponses.
- Plan court, un ou deux commits, message en français.
- Vérification à l'écran, avec les deux foyers jetables du lot précédent recréés : les cinq mêmes questions, plus « 6 kW, c'est assez ? » et « Quelle marque de PAC choisir ? ». La dernière doit aller au LLM. Recopier les réponses mot pour mot dans le débrief, puis effacer les foyers.
- À la fin : s'arrêter, résumer. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-chat-reponse-preaudit.md`. `CLAUDE.md` : 1 ligne au plus.

## Tests

- Chaque sujet : bonne réponse sur la maison au fioul à 6 pièces (fixture du lot 6 ou 7).
- `devis` : au-dessus, dans la plage, en dessous ; sans plage → `None`.
- Sans bloc `puissance` (audit v2.5) → `None` ; `force_llm` → pas de court-circuit.
- « Quelle marque de PAC choisir ? » et « Combien coûte une pompe à chaleur ? » → `None`.
- Plusieurs sujets dans une question : ordre fixe, sans doublon.
- Aucune variable `{…}` non remplie ; textes égaux à ceux de la fiche.
- `admin_stats` compte `preaudit`.
- Tests existants verts, build front vert. Aucun appel au LLM dans les tests.

## TODO.md

Mettre à jour le point 42 : les questions de puissance, de radiateurs et de relevé ne passent plus par le LLM.

---

## À ne pas faire

- Aucun calcul nouveau, sauf la comparaison d'un nombre à la plage.
- Ne pas intercepter les questions générales sur les PAC : marque, prix, bruit, aides.
- Ne pas toucher au moteur, à `audit_version`, aux audits stockés, ni au résumé envoyé au LLM.
- Aucun texte écrit directement dans le code.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Les questions 1 à 4 du débrief précédent reçoivent les chiffres exacts du pré-audit, sans LLM.
2. Une question sans ces calculs, ou d'un autre sujet, suit la voie habituelle.
3. Tests et build verts, réponses recopiées dans le débrief, point 42 mis à jour.
