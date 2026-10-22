# Débrief — Chat, lot 3 : deux garde-fous de la réponse directe du pré-audit (série 10)

22/10/2026. Commit `b657f0e`, puis le commit de la documentation, sur `main`, non poussés. Le lot
attend la validation de Stéphane.

**968 tests au vert**, dont 20 dans `test_chat_garde_fous.py` (aucun appel au LLM) ; les 23 de
`test_chat_reponse_preaudit.py` sont restés verts sans changement. Le moteur, `audit_version`, les
audits stockés et le résumé envoyé au LLM n'ont pas changé.

## Ce qui est fait

- **Deux textes** (`chat_preaudit_ancien`, `chat_sans_preaudit`) ajoutés à la section « Pour le
  pré-audit » de `kb/action_pac_remplacement.md`, puis recopiés dans `TEXTES_PUISSANCE`
  (vérifiés contre la fiche).
- **Sans bloc puissance** : `reponse_preaudit(..., connecte=True)` renvoie l'un de ces deux textes
  pour toute question des quatre sujets (puissance, devis, radiateurs, relevé). Un visiteur sans
  compte n'est jamais intercepté (`connecte=False` par défaut, et `chat.py` ne le passe à vrai
  que pour un utilisateur connecté). `model_used = "preaudit"`, `force_llm` passe outre.
- **Les autres puissances** : `_PUISSANCE_COMPTEUR` devient `_AUTRES_PUISSANCES` (compteur,
  solaire, recharge, froid, constante commentée avec ses exemples). Quand une question en parle,
  `puissance` et `devis` sont retirés ; `radiateurs` et `releve` restent (« Mes radiateurs et ma
  batterie » donne toujours le bilan des radiateurs).

## Vérification par les vraies routes

Trois foyers jetables (au fioul en v2.7 avec 6 pièces et un relevé de 1 500 L ; dernier audit en
v2.5 ; aucun pré-audit), questions par les routes, API et Ollama en marche. Les trois foyers ont été
effacés ensuite (vérifié : 0 restant). Fichier brut : `debriefs/2026-10-22-chat-garde-fous-reponses.json`.

### 1. « Quelle puissance de pompe à chaleur pour ma maison ? » (foyer au fioul, audit v2.7, 6 pièces, 1 500 L)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> Au jour le plus froid de référence (-5 °C), votre maison demande entre 7,3 et 8,5 kW de chauffage. Le calcul tiré de votre consommation réelle (8,5 kW) est le plus juste ; le calcul au volume (7,3 kW) sert de repère de prudence.
> Une pompe à chaleur air/eau d'environ 7 à 10 kW couvrirait ce besoin. Si un devis propose beaucoup plus, demandez sur quoi repose la puissance choisie.

**Voie juste, réponse juste.** `preaudit` : les phrases du pré-audit, inchangées depuis la série 9.

### 2. « Quelle puissance de pompe à chaleur pour ma maison ? » (foyer dernier audit en v2.5)

Voie : `preaudit`.

> Votre pré-audit du 22/10/2026 ne calcule pas encore la puissance de chauffage de votre maison. Refaites-le depuis votre espace : il donnera la puissance, la plage de pompe à chaleur et, si vos pièces sont saisies, le bilan de vos radiateurs.

**Voie juste, réponse juste.** `preaudit` : `chat_preaudit_ancien`, date remplie. Au lot précédent, le modèle local inventait « 20 kW à 40 kW ».

### 3. « Quelle puissance de pompe à chaleur pour ma maison ? » (foyer aucun pré-audit)

Voie : `preaudit`.

> Pour connaître la puissance de chauffage de votre maison, faites votre pré-audit depuis votre espace : il la calcule à partir de votre fiche, avec la plage de pompe à chaleur qui conviendrait et, si vos pièces sont saisies, le bilan de vos radiateurs.

**Voie juste, réponse juste.** `preaudit` : `chat_sans_preaudit`.

### 4. « Quelle puissance de panneaux solaires pour ma maison ? » (foyer au fioul, audit v2.7, 6 pièces, 1 500 L)

Voie : `local`.

> Pour estimer la puissance de panneaux solaires qui pourraient couvrir une partie de la consommation d'électricité de votre maison, nous utiliserons le simulateur solaire pré-rempli avec votre fiche.
>
> Le simulateur solaire est disponible en cliquant sur le lien « /simulateur-solaire ».

**Voie juste.** Exclue (« panneaux », « solaires ») : va au LLM. La réponse renvoie au simulateur, sans chiffre : acceptable.

### 5. « Une borne de 7 kW, c'est assez ? » (foyer au fioul, audit v2.7, 6 pièces, 1 500 L)

Voie : `local`.

> Non, la borne de 7 kW est un peu faible pour une maison de cette taille.

**Voie juste, réponse fausse.** Exclue (« borne ») : va au LLM, plus de comparaison à la plage de PAC. Mais le modèle local répond « un peu faible pour une maison de cette taille », un raisonnement faux (une borne se juge à la voiture et à l'installation, pas à la maison). Point 42.

### 6. « Une clim de 3,5 kW pour ma chambre ? » (foyer au fioul, audit v2.7, 6 pièces, 1 500 L)

Voie : `local`.

> Pour une clim de 3,5 kW pour votre chambre, je vous propose quelques options de chauffage :
>
> *   **Pompe à chaleur air/eau :** une pompe à chaleur air/eau d'environ 7 à 10 kW couvrirait ce besoin. Si un devis propose beaucoup plus, demandez sur quoi repose la puissance choisie.
> *   **Chaudière à condensat :** une chaudière à condensat d'environ 5 à 7 kW peut être une bonne option.
> *   **Boiler à gaz :** une chaudière à gaz d'environ 3 à 5 kW peut être suffisante, mais gardez à l'esprit que le gaz coûte cher.
>
> Ces chiffres sont basés sur les calculs ci-dessus et peuvent varier en fonction de votre maison et de vos besoins spécifiques.
>
> Pouvez-vous me dire d'où je peux obtenir un devis et quel est le coût estimé de l'installation de cette solution ?

**Voie juste, réponse fausse.** Exclue (« clim ») : va au LLM. Notre code ne compare plus à la plage, mais le modèle local la ressort de lui-même (« pompe à chaleur air/eau d'environ 7 à 10 kW ») depuis son contexte, et invente des puissances de chaudière. Point 42.

### 7. « Un installateur me propose 14 kW, c'est normal ? » (foyer au fioul, audit v2.7, 6 pièces, 1 500 L)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> 14 kW, c'est au-dessus de la plage que calcule votre pré-audit (7 à 10 kW). Demandez à l'installateur sur quoi repose cette puissance : une machine trop puissante coûte plus cher et fonctionne moins bien.

**Voie juste, réponse juste.** Non-régression : `preaudit`, 14 kW au-dessus de la plage.

## Bilan

Les deux critères tiennent pour ce que le code décide : aucun foyer connecté ne reçoit plus de
puissance de chauffage inventée (sa puissance, ou l'invitation au pré-audit), et aucune autre
puissance n'est plus comparée par Hélios à la plage de la PAC. Les questions 4 à 6 vont bien au
LLM. Mais le modèle local y répond mal (borne, clim), et peut même ressortir la plage de PAC de
son contexte : c'est la limite connue du point 42, que ce lot ne prétendait pas lever.

## Ce qui attend Stéphane

- Valider le lot.
- **Point 42** : le crédit Anthropic, toujours.
