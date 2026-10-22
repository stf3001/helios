# Brief Claude Code — Pré-audit, lot 6 : la puissance de chauffage et les radiateurs pièce par pièce (point 37)

## Contexte (à lire avant tout)

Point 37 de `TODO.md` : les pièces et émetteurs saisis au lot 2 du carnet ne servent à aucun calcul. Le pré-audit chiffre une PAC (coût, économie) **sans jamais dire quelle puissance** il faudrait, ni si les radiateurs en place conviennent à une PAC air/eau.

La fiche `kb/pac_air_eau.md` décrit déjà la bonne méthode : partir du besoin de chauffage, le rapporter aux degrés-jours pour obtenir les pertes par degré, puis la puissance au froid de référence ; le calcul au volume sert de plafond de prudence. `kb/cas_terrain.md` rappelle l'enjeu : trois devis, trois puissances pour la même maison.

Ce lot ajoute au pré-audit un **bloc « Puissance de chauffage »** et un **bilan des radiateurs pièce par pièce**. Il ne change ni les coûts, ni les économies, ni l'ordre des actions.

## Décisions de Stéphane (22/10/2026, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Méthode | **Les deux calculs, affichés en fourchette** : par la consommation, et au volume. |
| Puissance de référence | Calcul par la consommation quand `base_economies == "declaree"` (consommation réelle, aujourd'hui seulement en chauffage électrique) ; sinon calcul au volume. L'autre est toujours affiché à côté. |
| PAC air/eau | Plage conseillée : **80 à 120 %** de la puissance de référence, arrondie au demi-kilowatt. |
| PAC air/air | **Règle actuelle inchangée** : `_quantite` (une unité pour `audit_m2_par_unite_air_air` m², au plus `audit_unites_air_air_max`). Les pièces ne changent rien à l'air/air dans ce lot. |
| Radiateurs | **Test à 50 °C, puis à 55 °C** : la puissance déclarée des radiateurs à eau, ramenée à la température d'eau, est comparée au besoin de la pièce. Sans puissance déclarée, la pièce affiche que l'installateur doit la relever. |
| Surfaces | La puissance totale se calcule sur `surface_habitable` de la fiche. Les pièces servent seulement à **répartir** ce total, au prorata des surfaces des pièces chauffées déclarées. Un écart entre les deux surfaces ne change donc pas le total. |

## Les calculs (déterministes, dans `audit_engine.py`, sans appel réseau)

**Par la consommation** :

```
H (W/K)      = Q_utile (kWh/an) × 1000 / (DJU × 24)
P_conso (kW) = H × (T_int − T_base) / 1000
```

- `Q_utile` = `conso_chauffage_retenue_kwh_an` × rendement de l'appareil actuel (les valeurs que le moteur calcule déjà dans `consommation()`). Quand la base est `estimee`, P_conso est calculée quand même et affichée, avec le statut `suppose`.
- `DJU` : degrés-jours de chauffage (base 18 °C), **supposés** depuis une table par zone (`zone_climatique()`). Pas d'appel à `simu_climat` : le pré-audit reste sans réseau.
- `T_int` = 19 °C.

**Au volume** :

```
P_volume (kW) = S × h × G × (T_int − T_base) / 1000
G             = max(audit_g_min, audit_g_non_isolee × indice_isolation)
```

- `S` = `surface_habitable`, `h` = hauteur sous plafond supposée.
- `indice_isolation` : la somme **avant renormalisation** que `deperditions()` calcule déjà (`DEPERDITION_BASE` × facteurs `QUALITE_ISOLATION`, `QUALITE_MENUISERIES`, `QUALITE_VENTILATION`). Elle vaut 1 pour une maison non isolée et baisse avec l'isolation. Extraire une fonction commune plutôt que dupliquer, sans changer le résultat de `deperditions()`.

**Radiateurs** (la puissance nominale d'un radiateur est donnée pour un écart de 50 K entre l'eau et la pièce) :

```
P_radiateur(T) = P_nominale × (ΔT / 50) ^ n
ΔT             = (T_départ + T_retour) / 2 − T_int
```

- Régimes testés : 50/45 °C, puis 55/50 °C. P_nominale = `puissance_w` × `nombre`, sommée sur les émetteurs à eau de la pièce.
- Besoin d'une pièce = puissance de référence × surface de la pièce ÷ somme des surfaces des pièces chauffées déclarées.
- Verdict par pièce :
  - `ok_50`, `ok_55` ou `insuffisant` ;
  - `inconnu` : puissance non déclarée ou surface manquante ;
  - plancher chauffant à eau → `ok_50` ;
  - convecteurs, panneaux, radiateurs électriques à inertie, sèche-serviettes électriques → `electrique`.
- Pas de pièces saisies : pas de bilan par pièce, le bloc puissance s'affiche seul. Toutes les pièces en émetteurs électriques : une seule phrase, le texte existant `note_convecteurs`.

**Réglages** (`config.py`), chacun commenté « A VALIDER par Stéphane » :

| Réglage | Proposition |
|---|---|
| `audit_t_int` | 19 |
| `audit_t_base_par_zone` | H1 : −10 ; H2 : −7 ; H3 : −5 °C (la fiche PAC parle d'environ −5 °C en climat méditerranéen) |
| `audit_dju_par_zone` | H1 : 2 700 ; H2 : 2 200 ; H3 : 1 500 |
| `audit_hauteur_plafond_m` | 2,5 |
| `audit_g_non_isolee` | 1,6 W/m³.K |
| `audit_g_min` | 0,6 W/m³.K |
| `audit_regimes_radiateurs` | (50, 45) puis (55, 50) |
| `audit_exposant_radiateur` | 1,3 |
| `audit_pac_plage_pct` | (80, 120) |

Chaque valeur utilisée est tracée dans les hypothèses de l'audit (`t.hyp`), avec son statut (`calcule`, `suppose`, `declare`).

## Les textes (fiche d'abord, recopie ensuite)

Les ajouter à la section « Pour le pré-audit » de `kb/action_pac_remplacement.md`, la fiche de l'action PAC qui porte déjà cette section. `kb/pac_air_eau.md` n'en a pas et n'en reçoit pas. Puis les recopier dans `audit_reference.py`, selon la règle de source unique tenue par `test_audit_textes.py`.

- **puissance_declaree** : « Au jour le plus froid de référence ({t_base} °C), votre maison demande entre {p_bas} et {p_haut} kW de chauffage. Le calcul tiré de votre consommation réelle ({p_conso} kW) est le plus juste ; le calcul au volume ({p_volume} kW) sert de repère de prudence. »
- **puissance_estimee** : « Au jour le plus froid de référence ({t_base} °C), votre maison demande entre {p_bas} et {p_haut} kW de chauffage, selon deux calculs faits sans vos relevés. Avec vos factures de chauffage, ce chiffre serait plus juste, et souvent plus bas. »
- **plage_pac** : « Une pompe à chaleur air/eau d'environ {pac_bas} à {pac_haut} kW couvrirait ce besoin. Si un devis propose beaucoup plus, demandez sur quoi repose la puissance choisie. »
- **radiateurs_ok_50** : « {piece} : vos radiateurs suffisent avec une eau à 50 °C. »
- **radiateurs_ok_55** : « {piece} : vos radiateurs suffisent avec une eau à 55 °C. »
- **radiateurs_insuffisant** : « {piece} : vos radiateurs seraient un peu justes, même à 55 °C. Un radiateur de plus, ou plus grand, réglerait la question. »
- **radiateurs_inconnu** : « {piece} : la puissance des radiateurs n'est pas indiquée ; l'installateur doit la relever. »

Le bloc « Puissance de chauffage » s'affiche quand le pré-audit propose une PAC air/eau. Pour une maison en convecteurs, où l'action est l'air/air, il affiche la seule phrase de puissance, sans plage air/eau.

## Méthode de travail

- Lire :
  - `services/audit_engine.py` (`_profil`, `consommation`, `deperditions`, `_quantite`, traces) ;
  - `audit_reference.py` et `services/pieces.py` ;
  - `kb/action_pac_remplacement.md`, `kb/pac_air_eau.md` et `kb/cas_terrain.md` ;
  - les débriefs du pré-audit (lots 4 et 5) et du carnet lot 2.
- Plan court, un commit par étape, message en français.
- `audit_version` passe de `"v2.5"` à `"v2.6"`. Les audits stockés ne sont jamais recalculés et s'affichent toujours.
- Juger à l'œil sur les PDF de quatre maisons :
  - la maison de référence, en chauffage électrique avec consommation déclarée ;
  - la maison au fioul (`maison_type()`) avec 6 pièces et des radiateurs à eau déclarés, dont un sans puissance ;
  - une maison en convecteurs ;
  - une maison sans pièces saisies.
- À la fin : s'arrêter et résumer. Joindre les quatre rendus et un tableau qui donne, pour chaque maison, P_conso, P_volume, la référence, la plage PAC et les verdicts par pièce. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-preaudit-lot6.md`. `CLAUDE.md` : 2 lignes au plus.

## Tests

- Formules : trois cas calculés à la main (par la consommation, au volume, radiateur à 50 °C et à 55 °C).
- Référence : `declaree` → calcul par la consommation, texte `puissance_declaree` ; `estimee` → calcul au volume, texte `puissance_estimee`.
- Répartition : la somme des besoins des pièces égale la puissance de référence.
- Verdicts : chaque cas, dont le plancher chauffant, les émetteurs électriques et une pièce sans puissance.
- `deperditions()` donne exactement les mêmes parts qu'en v2.5.
- Comparaison v2.5 / v2.6 sur les quatre maisons : mêmes unités air/air, mêmes coûts, économies, horizons et ordre.
- Aucune variable `{…}` non remplie ; anciens audits v1 à v2.5 toujours affichables.
- Tests existants verts, build front vert.

## TODO.md

Cocher le point 37 après vérification sur les quatre PDF, et cocher aussi le point 63, déjà fait. Ajouter un point : **valider les réglages « A VALIDER » de la puissance** (températures de base, degrés-jours, G, hauteur, exposant).

---

## À ne pas faire

- Ne modifier ni la règle de l'air/air, ni les coûts, ni les économies, ni l'ordre des actions, ni les parts de `deperditions()`.
- Ne pas corriger la fiche maison à partir des pièces.
- Pas d'appel réseau dans le pré-audit (ni `simu_climat`, ni PVGIS).
- Aucun chiffre produit par le LLM ; aucun texte écrit directement dans le code.
- Ne pas recalculer les audits stockés.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Chaque pré-audit qui propose une PAC air/eau donne la puissance en fourchette, dit quel calcul fait référence et affiche la plage de PAC à 80-120 %.
2. Quand pièces et radiateurs sont saisis, le foyer sait, pièce par pièce, si ses radiateurs suffisent à 50 °C ou à 55 °C.
3. Rien d'autre ne change dans l'audit.
4. Tests et build verts, quatre rendus et tableau joints, débrief écrit, points 37 et 63 cochés.
