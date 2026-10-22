# Débrief — Hélios lit la puissance de chauffage et le relevé (point 81)

22/10/2026. Commits `31b94a2` et `1fc6e13`, puis le commit de la documentation, sur `main`, non
poussés. Le lot attend la validation de Stéphane.

**915 tests au vert**, dont 18 dans `test_chat_puissance.py` (aucun appel au LLM). Le moteur,
`audit_version` (v2.7) et les audits stockés n'ont pas changé.

## Ce que le chat reçoit

- `consommation` : en plus des clés d'avant (toujours toutes là, même vides), `releve`,
  `conso_autre_energie_kwh_an` et `eau_chaude_deduite_kwh_an` quand l'audit les porte.
- `puissance` (`rag.resume_puissance`, audit v2.6 et plus) : référence, puissance de référence,
  par la consommation et au volume, température de base, la phrase du pré-audit, le statut de la
  référence ; la plage PAC et sa phrase si le bloc est complet ; une ligne par pièce,
  « Séjour : ok_55, besoin 2839 W » ; la note des convecteurs s'il y en a une. Ni puissances à
  50/55 °C, ni puissance nominale.
- Audit plus ancien : pas de `puissance`, mais `puissance_non_calculee` (voir les ajustements).
- **Retiré** : les hypothèses du calcul de puissance (`puissance_*`, `radiateurs_*`) partaient
  déjà au chat depuis la v2.6, dans la liste des hypothèses. C'est de la traçabilité, en double
  du résumé.
- `CONSIGNE_AUDIT_PRIME` : la consigne du brief, ajoutée telle quelle, plus un ajustement.

## La taille du contexte

| Maison (lot 6) | Avant | Après |
|---|---|---|
| Référence | 14 877 | 15 735 |
| Fioul, 6 pièces | 15 099 | **16 274 (+1 175)** |
| Convecteurs | 15 169 | 16 012 |
| Gaz sans pièces | 14 924 | 15 979 |

**Les +700 visés ne tiennent pas, et voici pourquoi** : la consigne du brief pèse à elle seule
+631, et son ajustement +246. Les données (résumé `puissance`, 814 caractères, moins les
hypothèses de traçabilité retirées) n'ajoutent que **+298**. Le test tient le résumé sous 850 et
le contexte sous 16 300.

## Une fiche générale répondait à la place du pré-audit (risque annoncé, constaté)

Au premier passage, « Mes radiateurs suffiront-ils ? » a reçu la fiche générale sur les
radiateurs, servie telle quelle (`model_used = kb`) : la méthode, pas les verdicts du foyer. Comme
prévu dans le plan, une condition de plus dans `chat.py` : quand le pré-audit du foyer porte un
bloc puissance et que la question parle de puissance, de kW/kWh, de radiateurs, de pompe à
chaleur, de fioul, de granulés, de stères ou de relevé (`_SUJET_PUISSANCE`), pas de réponse
instantanée. Une question sans rapport (« Comment isoler mes combles ? ») garde la sienne.

## Les deux ajustements de consigne (le maximum du brief)

1. **Un audit sans bloc puissance le dit dans ses données** : `puissance_non_calculee` = « Ce
   pré-audit ne calcule pas la puissance de chauffage : n'en donner aucune, proposer de refaire
   le pré-audit. » La règle générale de la consigne ne suffisait pas au modèle local (il inventait
   6 kW et un chauffage au gaz).
2. **Dans la consigne** : une puissance proposée au-dessus de la borne haute de la plage « dépasse
   ce que le pré-audit calcule », et le relevé en kWh est `conso_autre_energie_kwh_an`.

## Vérification réelle : cinq questions, mot pour mot

Deux foyers jetables (maison au fioul de 100 m² à Marseille, relevé 1 500 L, 6 pièces ; l'autre
avec un dernier audit v2.5), pré-audit et questions par les vraies routes, API et Ollama en marche.
Les deux foyers ont été effacés ensuite (conversations, pièces, audits et leurs PDF compris).

**Tout a été répondu par le modèle local** (`llama3.2:3b`) : un foyer avec pré-audit est envoyé à
Claude, mais le compte n'a plus de crédit (« Your credit balance is too low to access the
Anthropic API », relu dans les journaux de l'API), et le chat retombe sur le local. C'est ce que
le brief demandait de vérifier ; c'est aussi la limite du point 42.

Fichiers bruts : `debriefs/2026-10-22-chat-puissance-reponses.json` (second passage, ci-dessous)
et `-reponses-passage1.json` (avant les ajustements).

### 1. « Quelle puissance de pompe à chaleur pour ma maison ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Modèle : `local` (mode simplifié : Claude sans crédit).

> D'après votre dossier, au jour le plus froid de référence (-5 °C), votre maison demande entre 7,3 et 8,5 kW de chauffage.

**Juste mais incomplète.** La fourchette de besoin (7,3 à 8,5 kW) est celle du pré-audit, sans autre chiffre. Mais ni la plage de PAC (7 à 10 kW), ni le calcul qui fait référence (la consommation).

Premier passage, avant les ajustements : Chiffres justes (la phrase de la plage, recopiée), sans dire quel calcul fait référence.

### 2. « Mes radiateurs suffiront-ils ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Modèle : `local` (mode simplifié : Claude sans crédit).

> Bonjour !
>
> Pour répondre à votre question, les informations nécessaires pour déterminer si vos radiateurs suffiront à couvrir votre besoin de chauffage sont disponibles sur la page du simulateur de votre foyer.
>
> En regardant le tableau de chauffage, nous voyons que :
>
> - La superficie de votre maison est de 130 m².
> - Le besoin utile de chauffage est de 180 kWh/an par m².
> - La superficie totale de vos radiateurs est de 7,3 m² (valeur calculée à partir de votre consommation réelle de 8,5 kW).
> - Le besoin utile de chauffage par m² est de 180 kWh/an, soit 7,3 m² x 180 kW/m² = 1 262 kW pour une superficie totale de 7,3 m².
>
> Il semble que vos radiateurs devraient suffire pour couvrir votre besoin de chauffage, mais comme indiqué dans le tableau de chauffage, des radiateurs supplémentaires pourraient être nécessaires pour répondre à votre besoin de 1 262 kW.
>
> Il est toujours recommandé de consulter un professionnel pour une évaluation plus précise de vos besoins de chauffage.

**Fausse.** La fiche générale ne passe plus devant (bonne voie), mais le modèle invente une surface (130 m²), une « superficie de radiateurs » et « 1 262 kW ». Les verdicts du contexte (séjour ok à 55 °C, cuisine insuffisant…) ne sont pas cités.

Premier passage, avant les ajustements : Réponse instantanée : la fiche générale sur les radiateurs, servie telle quelle, sans les verdicts du foyer.

### 3. « Un installateur me propose 14 kW, c'est normal ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Modèle : `local` (mode simplifié : Claude sans crédit).

> Non, 14 kW est supérieur au besoin de 7 à 10 kW pour votre foyer.

**Juste.** 14 kW est bien au-dessus de la plage du pré-audit (7 à 10 kW). Il appelle la plage « besoin » : approximatif, sans conséquence.

Premier passage, avant les ajustements : « Oui, 14 kW est réaliste » : faux, au-dessus de la plage.

### 4. « Combien de kWh représente mon fioul ? » (audit v2.7, 6 pièces, 1 500 L de fioul)

Modèle : `local` (mode simplifié : Claude sans crédit).

> Avec les données fournies, il n'est pas possible de déterminer la quantité de kWh que représente le fioul. Cependant, selon les données fournies, le fioul représente 10,0 kWh/litre.

**Fausse.** Le contexte porte `conso_autre_energie_kwh_an` = 15 000 ; le modèle dit que ce n'est pas possible et cite le facteur de conversion (10 kWh par litre), qu'il lit dans les hypothèses.

Premier passage, avant les ajustements : « 10.0 » : le facteur de conversion, pas les 15 000 kWh.

### 5. « Quelle puissance de pompe à chaleur pour ma maison ? » (dernier audit en v2.5)

Modèle : `local` (mode simplifié : Claude sans crédit).

> Bonjour ! Pour estimer la puissance de pompe à chaleur nécessaire à votre maison, nous avons besoin de quelques informations supplémentaires.
>
> Pour commencer, j'aimerais savoir :
>
> - Quel est le nombre de pièces en surface habitable dans votre maison ?
> - Combien d'habitants y a-t-il normalement présents à l'intérieur ? 
> - Quelle est la zone climatique de votre maison ? 
>
> Ces informations nous aideront à mieux comprendre vos besoins énergétiques et à estimer la puissance de pompe à chaleur appropriée. 
>
> Veuillez me donner ces informations pour que je puisse vous donner un aperçu de la puissance de pompe à chaleur qui pourrait vous convenir.

**Juste sur l'essentiel.** Aucune puissance donnée (critère 2 tenu). Mais il redemande des informations que la fiche contient déjà, au lieu de proposer de refaire le pré-audit.

Premier passage, avant les ajustements : Invente « autour de 6 kW » et un chauffage « Gaz (valeur par défaut) ».

## Bilan

Le contexte est juste (testé) : il porte les chiffres du pré-audit, et rien d'autre. Le modèle
local, lui, reste peu fiable : deux réponses justes, une juste mais incomplète, deux fausses. Sur
le devis de 14 kW et sur l'audit ancien, les ajustements ont corrigé ce qui était faux au premier
passage. Sur les radiateurs et sur le relevé, non : le modèle invente ou lit le mauvais chiffre,
alors que les bons sont dans le contexte. Je n'ai pas forcé au-delà des deux ajustements. Ajouté au
point 42 de `TODO.md` (aucun point nouveau), qui attend le crédit Anthropic : avec Claude, ces
questions passeraient par la route API, qui lisait bien les études chiffrées en juillet.

## Ce qui attend Stéphane

- Valider le lot.
- **Point 42** : recharger le crédit Anthropic (Plans & Billing), puis refaire ces cinq questions.
