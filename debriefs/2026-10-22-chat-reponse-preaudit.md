# Débrief — Chat : la réponse directe du pré-audit (série 9)

22/10/2026. Commit `29b40bb`, puis le commit de la documentation, sur `main`, non poussés. Le lot
attend la validation de Stéphane.

**946 tests au vert**, dont 23 dans `test_chat_reponse_preaudit.py` (la fonction seule, et la route
contre la base avec un faux générateur : aucun appel au LLM). Build vert (520 URL). Le moteur,
`audit_version` (v2.7), les audits stockés et le résumé envoyé au LLM n'ont pas changé.

## Ce qui est fait

- **Huit textes `chat_*`** ajoutés à la section « Pour le pré-audit » de
  `kb/action_pac_remplacement.md`, puis recopiés dans `TEXTES_PUISSANCE` ; `test_audit_textes.py`
  les compare à la fiche.
- **`rag.reponse_preaudit(audit_result, date, question)`**, pure : reconnaît les sujets
  (`SUJETS_PREAUDIT`, constante commentée avec les questions du lot précédent en exemples),
  assemble les phrases dans l'ordre radiateurs → relevé → devis → puissance, chacune une fois. Le
  seul calcul : comparer la puissance d'un devis à la plage `pac_air_eau_kw`. « 15 000 kWh » n'est
  pas un devis ; « Quelle puissance souscrire ? » (compteur) n'est pas la puissance de chauffage ;
  « marque », « prix », « bruit », « aides » ne déclenchent rien.
- **`chat.py`** : court-circuit juste avant la réponse instantanée par fiche, sur le même modèle
  (flux `conversation` avec `instant: True`, puis le texte, puis `message_id`),
  `model_used = "preaudit"`, sans citation. `force_llm` (« Développer avec Helios ») passe outre.
- **Back-office** : « preaudit » a son libellé dans le tableau de bord (« Phrases du pré-audit
  (aucun LLM) ») et dans les conversations (« pré-audit ») ; le décompte par voie le regroupe de
  lui-même (testé).
- **Libellés du relevé** (`TYPE_RELEVE`, `UNITE_RELEVE`) déplacés de `pdf_audit.py` vers
  `audit_reference.py` : le PDF et le chat lisent la même liste.

## Écarts avec le brief, et pourquoi

- **La réponse est construite à partir du bloc `puissance` complet du pré-audit**, pas du résumé
  envoyé au LLM : celui-ci ne garde qu'une ligne compacte par pièce, alors qu'il faut le nom et le
  verdict séparés pour remplir les phrases. Le résumé n'a pas changé. Annoncé dans le plan.
- **Les puissances sont comparées bornes comprises** : 6 kW est « dans la plage » de 6 à 9 kW.
- **Une question où « devis » rencontre une maison sans plage air/eau** (convecteurs, PAC air/air)
  va entièrement au LLM, même si elle porte aussi sur un autre sujet : le brief ne demande de
  répondre que quand tout peut l'être.

## Vérification par les vraies routes : sept questions, mot pour mot

Les deux foyers jetables du lot précédent recréés (maison au fioul de 100 m² à Marseille, relevé
1 500 L, 6 pièces ; un foyer avec un dernier audit v2.5), pré-audit et questions par les routes,
API et Ollama en marche. Les foyers ont été effacés ensuite. Fichier brut :
`debriefs/2026-10-22-chat-reponse-preaudit-reponses.json`.

### 1. « Quelle puissance de pompe à chaleur pour ma maison ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> Au jour le plus froid de référence (-5 °C), votre maison demande entre 7,3 et 8,5 kW de chauffage. Le calcul tiré de votre consommation réelle (8,5 kW) est le plus juste ; le calcul au volume (7,3 kW) sert de repère de prudence.
> Une pompe à chaleur air/eau d'environ 7 à 10 kW couvrirait ce besoin. Si un devis propose beaucoup plus, demandez sur quoi repose la puissance choisie.

**Juste.** Voie `preaudit`, sans LLM. La fourchette, le calcul qui fait référence (la consommation, grâce au relevé de 1 500 L) et la plage de PAC : les phrases mêmes du pré-audit. Au lot précédent : la fourchette seule.

### 2. « Mes radiateurs suffiront-ils ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> - Séjour : vos radiateurs seraient un peu justes, même à 55 °C. Un radiateur de plus, ou plus grand, réglerait la question.
> - Cuisine : vos radiateurs seraient un peu justes, même à 55 °C. Un radiateur de plus, ou plus grand, réglerait la question.
> - Chambre 1 : vos radiateurs suffisent avec une eau à 55 °C.
> - Chambre 2 : vos radiateurs seraient un peu justes, même à 55 °C. Un radiateur de plus, ou plus grand, réglerait la question.
> - Bureau : vos radiateurs suffisent avec une eau à 50 °C.
> - Salle de bains : la puissance des radiateurs n'est pas indiquée ; l'installateur doit la relever.

**Juste.** Une ligne par pièce, le verdict calculé par le moteur. Au lot précédent : « 130 m² » et « 1 262 kW » inventés.

### 3. « Un installateur me propose 14 kW, c'est normal ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> 14 kW, c'est au-dessus de la plage que calcule votre pré-audit (7 à 10 kW). Demandez à l'installateur sur quoi repose cette puissance : une machine trop puissante coûte plus cher et fonctionne moins bien.

**Juste.** 14 kW comparé à la plage 7 à 10 kW : au-dessus.

### 4. « Combien de kWh représente mon fioul ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> Votre relevé (1 500 litres de fioul par an) représente environ 15 000 kWh.

**Juste.** 15 000 kWh, le chiffre du pré-audit. Au lot précédent : « pas possible », puis le facteur 10 kWh/L.

### 5. « Quelle puissance de pompe à chaleur pour ma maison ? » (dernier audit en v2.5)

Voie : `local`.

> Pour déterminer la puissance de chaleur adéquate pour votre maison, il est essentiel de prendre en compte plusieurs facteurs, notamment la surface habitable, le nombre d'occupants, les besoins en chauffage et l'efficacité de la construction.
>
> Puisque nous n'avons pas de détails précis sur ces éléments pour votre maison, je vais vous fournir une orientation générale. La puissance de chaleur est généralement exprimée en kilowatts (kW) et dépend du nombre de kW de chaleur nécessaire pour équilibrer la perte de chaleur par unité de surface habitable à une température d'environ 20°C.
>
> Pour un foyer de 3 pièces avec 3 occupants, une estimation de base pourrait être :
>
> *   Forêt ( zone H3) :
>     *   surface habitable supérieure ou égale à 50 m² : 20 kW à 40 kW
>     *   surface habitable inférieure à 50 m² : 10 kW à 20 kW
>
> Cependant, il est crucial de prendre en compte les conditions spécifiques de votre maison, notamment son isolement, sa construction et les éléments qui façonnent votre besoin en chauffage. Il est également important de noter que ces estimations sont des hypothèses et qu'une évaluation plus précise par un professionnel serait nécessaire pour déterminer la puissance exacte de chaleur appropriée.
>
> Il est également important de noter que le coût et le coût de installation de la chaleur varient en fonction des options de chauffage choisis, notamment l'énergie utilisée.
>
> Je vous recommande de consulter un professionnel pour une évaluation plus précise de vos besoins en matière de chauffage et pour déterminer la puissance de chaleur appropriée et les coûts associés.

**Voie juste, réponse fausse.** Aucun bloc puissance : la question suit la voie habituelle (le LLM), comme le prévoit le brief. Mais le modèle local invente « 20 kW à 40 kW » malgré la consigne du lot précédent. Hors de ce lot ; inscrit au point 42.

### 6. « 6 kW, c'est assez ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Voie : `preaudit`.

> D'après votre pré-audit du 22/10/2026 :
>
> 6 kW, c'est en dessous de la plage que calcule votre pré-audit (7 à 10 kW). Demandez à l'installateur comment la maison sera chauffée les jours les plus froids.

**Juste.** 6 kW comparé à la plage 7 à 10 kW : en dessous.

### 7. « Quelle marque de PAC choisir ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Voie : `local`.

> Je ne peux pas vous aider à choisir une marque de PAC.

**Voie juste.** Question générale : elle va au LLM, comme voulu. La réponse du modèle local est sèche, mais elle ne promet rien et ne nomme aucune marque.

## Bilan

Les quatre questions du lot précédent, plus le cas « en dessous » de la plage, reçoivent les
chiffres exacts du pré-audit, sans LLM et en un instant. La question générale va bien au LLM. Reste
le cas d'un foyer sans bloc puissance : le modèle local y invente encore une puissance. Il suit la
voie habituelle comme le demande le brief, et attend le crédit Anthropic (point 42 de `TODO.md`).

## Ce qui attend Stéphane

- Valider le lot.
- **Point 42** : recharger le crédit Anthropic ; ou, si l'invention d'une puissance pour un audit
  ancien gêne d'ici là, décider d'une réponse directe « refaites le pré-audit » pour ce cas.
