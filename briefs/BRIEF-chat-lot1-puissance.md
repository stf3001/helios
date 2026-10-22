# Brief Claude Code — Hélios lit la puissance de chauffage et le relevé (point 81)

## Contexte (à lire avant tout)

Depuis les lots 6 et 7, le pré-audit calcule :
- la puissance de chauffage en fourchette ;
- la plage de PAC air/eau ;
- le verdict des radiateurs pièce par pièce ;
- le relevé de fioul, de gaz ou de bois converti en kWh.

Le chat n'en sait rien : `rag.build_audit_context` ne transmet ni le bloc `puissance` ni les nouvelles clés de `consommation`. À « Quelle PAC pour ma maison ? », Hélios répond donc avec les ordres de grandeur généraux des fiches, parfois contraires au pré-audit du foyer.

Ce lot est **petit** : transmettre ces chiffres au chat, avec une consigne claire. Le moteur ne change pas, et `audit_version` reste `"v2.7"`.

## Décisions de Stéphane (22/10/2026)

| Sujet | Décision |
|---|---|
| Point 81 | Facteurs de conversion et eau chaude au gaz **validés en l'état**. Dans `config.py`, « A VALIDER » devient « validé par Stéphane le 22/10/2026 ». Cocher le point 81. |
| Lot | Hélios reprend la puissance, la plage de PAC, les verdicts des radiateurs et le relevé de combustible du dernier pré-audit. |

## 1. Ce que le chat reçoit

Dans `build_audit_context`, pour un audit v2.6 ou plus récent :

- **`consommation`** : ajouter `releve`, `conso_autre_energie_kwh_an` et `eau_chaude_deduite_kwh_an` à la liste des clés recopiées.
- **`puissance`**, un résumé court du bloc du moteur :
  - `reference` (`consommation` ou `volume`), `p_reference_kw`, `p_conso_kw`, `p_volume_kw`, `t_base`, `statuts` ;
  - `texte` : la phrase du pré-audit, telle quelle ;
  - si `affichage == "complet"` : `pac_air_eau_kw` et `texte_plage` ;
  - `radiateurs` : une ligne par pièce, avec seulement `piece`, `verdict` et le besoin en watts ;
  - `note_radiateurs` s'il y en a une.
  - Ne pas transmettre les puissances détaillées à 50 et à 55 °C, ni la puissance nominale : c'est trop lourd pour le modèle local, et le verdict suffit.
- **Audit plus ancien que la v2.6** : pas de clé `puissance`.

Mesurer la taille du contexte avant et après pour les quatre maisons du lot 6. Viser **+700 caractères au plus** pour la maison au fioul à 6 pièces, et l'indiquer dans le débrief.

## 2. La consigne

Ajouter à la consigne de l'audit, dans `rag.py` comme `CONSIGNE_AUDIT_PRIME` (c'est une consigne au modèle, pas un texte affiché au foyer) :

> « Puissance de chauffage et plage de pompe à chaleur : ce sont celles du moteur. Les citer telles quelles, en fourchette, en disant quel calcul fait référence. Ne jamais proposer une autre puissance, ni la recalculer à partir d'un ratio au m². Radiateur "insuffisant" : dire qu'un radiateur de plus ou plus grand règle la question, sans citer de modèle ni de prix. Radiateur "inconnu" : l'installateur doit relever sa puissance. Sans bloc puissance, ne donner aucune puissance de pompe à chaleur : proposer de refaire le pré-audit. Pour une pompe à chaleur air/air, ne pas dimensionner les unités pièce par pièce. »

Ne pas modifier les autres consignes.

## Méthode de travail

- Lire :
  - `services/rag.py` (`build_audit_context`, `CONSIGNE_AUDIT_PRIME`) ;
  - le bloc `puissance` et `consommation` dans `audit_engine.py` ;
  - les fixtures `api/tests/fixtures/audit_v26/` ;
  - les débriefs des lots 6 et 7 du pré-audit et le point 42 de `TODO.md` (vérification Ollama).
- Plan court, un ou deux commits, message en français.
- **Vérification à l'écran, avec Ollama**, sur un foyer jetable au fioul avec ses 6 pièces et un relevé de 1 500 L. Poser cinq questions :
  1. « Quelle puissance de pompe à chaleur pour ma maison ? »
  2. « Mes radiateurs suffiront-ils ? »
  3. « Un installateur me propose 14 kW, c'est normal ? »
  4. « Combien de kWh représente mon fioul ? »
  5. La question 1 sur un foyer dont le dernier audit est en v2.5.
  Recopier les cinq réponses **mot pour mot** dans le débrief, avec, pour chacune, juste ou fausse et pourquoi. Deux ajustements de la consigne au plus. Si le modèle local reste faux, le dire, sans forcer.
- Effacer ensuite le foyer jetable.
- À la fin : s'arrêter, résumer, joindre le débrief avec les réponses. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-chat-puissance.md`. `CLAUDE.md` : 1 ligne au plus.

## Tests

- Audit v2.7 avec pièces : `puissance` présent, avec la référence, la plage et les verdicts ; sans `puissance_50_w` ni `puissance_nominale_w`.
- Affichage « phrase seule » (convecteurs) : sans plage air/eau.
- Audit v2.5 : aucune clé `puissance` ; anciens audits v1 à v2.5 inchangés dans le contexte.
- Relevé de fioul : `releve` et `conso_autre_energie_kwh_an` présents.
- Taille du contexte : sous le seuil choisi pour la maison au fioul à 6 pièces.
- Tests existants verts. Aucun appel au LLM dans les tests.

## TODO.md

Cocher le point 81. Si la vérification Ollama est mauvaise, l'ajouter au point 42, au lieu d'ouvrir un nouveau point.

---

## À ne pas faire

- Ne pas toucher au moteur, ni à `audit_version`, ni aux audits stockés.
- Ne pas transmettre au chat le bloc complet de traçabilité, ni toutes les puissances par pièce.
- Ne pas écrire de fiche `kb/`, ni modifier `pac_air_eau.md`.
- Ne pas laisser le LLM produire une puissance, un nombre d'unités ou un prix.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Interrogé sur la PAC ou ses radiateurs, Hélios cite les chiffres du pré-audit du foyer, et aucun autre.
2. Sans pré-audit v2.6 ou plus récent, Hélios ne donne aucune puissance.
3. Le contexte reste léger, et sa taille est mesurée.
4. Tests verts, cinq réponses recopiées et jugées dans le débrief, point 81 coché.
