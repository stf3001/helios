# Brief Claude Code — Chat, lot 3 : deux garde-fous de la réponse directe du pré-audit

## Contexte (à lire avant tout)

Le lot « réponse directe du pré-audit » (`29b40bb`) fonctionne : les questions de puissance, de radiateurs, de relevé et de devis reçoivent les phrases du pré-audit, sans LLM. Deux trous restent.

1. **Un foyer sans bloc puissance** (pré-audit antérieur à la v2.6, ou aucun pré-audit) : la question va au modèle local, qui invente « 20 kW à 40 kW » (débrief, question 5). Une puissance inventée est exactement ce que le projet interdit.
2. **Les mots déclencheurs attrapent d'autres puissances.** `SUJETS_PREAUDIT` exclut le compteur (`_PUISSANCE_COMPTEUR`), mais pas le reste. En lisant le code, on voit que :
   - « Quelle puissance de panneaux solaires ? » recevrait la puissance de chauffage ;
   - « Une borne de 7 kW, c'est assez ? » ou « une clim de 3,5 kW » serait comparée à la plage de PAC air/eau.

Petit lot, sans changement du moteur.

## Décision (22/10/2026)

| Sujet | Décision |
|---|---|
| Sans bloc puissance | Foyer connecté qui pose une question des sujets `puissance`, `devis` ou `radiateurs` alors que son dernier pré-audit n'a pas de bloc `puissance`, ou qu'il n'a aucun pré-audit : réponse directe qui renvoie au pré-audit, **sans LLM**. Le sujet `releve` sans bloc suit la même règle. |
| Visiteur sans compte | Inchangé : voie habituelle. |
| Autres puissances | Les sujets `puissance` et `devis` ne se déclenchent pas quand la question parle d'autre chose que du chauffage (liste ci-dessous). |

## 1. Les textes (fiche d'abord, recopie ensuite)

Les écrire dans la section « Pour le pré-audit » de `kb/action_pac_remplacement.md`, puis les recopier dans `TEXTES_PUISSANCE` :

- **chat_preaudit_ancien** : « Votre pré-audit du {date} ne calcule pas encore la puissance de chauffage de votre maison. Refaites-le depuis votre espace : il donnera la puissance, la plage de pompe à chaleur et, si vos pièces sont saisies, le bilan de vos radiateurs. »
- **chat_sans_preaudit** : « Pour connaître la puissance de chauffage de votre maison, faites votre pré-audit depuis votre espace : il la calcule à partir de votre fiche, avec la plage de pompe à chaleur qui conviendrait et, si vos pièces sont saisies, le bilan de vos radiateurs. »

`model_used = "preaudit"`, `instant: True`, et le bouton « développer » (`force_llm`) passe outre, comme au lot précédent.

## 2. Les exclusions

Dans `sujets_preaudit` : retirer `puissance` **et** `devis` quand la question contient l'un de ces motifs. Garder une constante commentée, qui remplace `_PUISSANCE_COMPTEUR` en l'élargissant :

- compteur : `souscri`, `kva`, `compteur`, `abonnement` (l'existant) ;
- solaire : `solaire`, `panneau`, `photovolta`, `kwc`, `onduleur`, `batterie` ;
- recharge : `borne`, `recharge`, `voiture` ;
- froid : `clim`, `split`.

Les sujets `radiateurs` et `releve` ne sont pas concernés.

## Méthode de travail

- Lire `services/rag.py` (`SUJETS_PREAUDIT`, `sujets_preaudit`, `reponse_preaudit`), `routers/chat.py` (court-circuit `preaudit`), le débrief `2026-10-22-chat-reponse-preaudit.md`.
- Un commit, message en français.
- Vérification par les vraies routes avec deux foyers jetables : un au fioul en v2.7 avec ses pièces, un dont le dernier audit est en v2.5. Puis un troisième foyer, sans aucun pré-audit. Questions :
  1. « Quelle puissance de pompe à chaleur pour ma maison ? » sur les trois foyers ;
  2. « Quelle puissance de panneaux solaires pour ma maison ? » ;
  3. « Une borne de 7 kW, c'est assez ? » ;
  4. « Une clim de 3,5 kW pour ma chambre ? » ;
  5. « Un installateur me propose 14 kW, c'est normal ? », en non-régression.
  Recopier les réponses et la voie suivie dans le débrief. Les questions 2 à 4 doivent aller au LLM. Effacer ensuite les foyers.
- À la fin : s'arrêter, résumer. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-chat-garde-fous.md`. `CLAUDE.md` : rien, ou 1 ligne au plus.

## Tests

- Audit v2.5 + sujet `puissance` → `chat_preaudit_ancien` (date remplie).
- Aucun pré-audit → `chat_sans_preaudit`.
- Visiteur sans compte → voie habituelle.
- Chaque exclusion : `puissance` et `devis` retirés ; `radiateurs` et `releve` intacts.
- Les 23 tests de `test_chat_reponse_preaudit.py` restent verts.
- Textes égaux à la fiche ; aucune variable `{…}` non remplie.
- Tests existants verts. Aucun appel au LLM dans les tests.

## TODO.md

Point 42 : noter que l'audit ancien ne passe plus par le LLM pour la puissance.

---

## À ne pas faire

- Ne pas toucher au moteur, à `audit_version`, aux audits stockés, ni au résumé envoyé au LLM.
- Ne pas répondre directement à un visiteur sans compte.
- Ne pas intercepter les questions solaires, de borne ou de climatisation : elles ont leurs fiches et leur voie.
- Aucun texte écrit directement dans le code.
- **Aucune nouvelle dépendance.**

## Critères d'acceptation

1. Aucun foyer connecté ne reçoit une puissance de chauffage inventée : il reçoit la sienne, ou l'invitation à faire ou refaire son pré-audit.
2. Une question sur une autre puissance (solaire, borne, clim, compteur) n'est jamais comparée à la plage de la PAC.
3. Tests verts, réponses recopiées dans le débrief.
