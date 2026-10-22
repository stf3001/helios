# Brief Claude Code — Phase 2 : la vigilance météo reliée à la maison

## Contexte (à lire avant tout)

Prérequis : **lot « risques de la commune » validé** (code INSEE et fiche `kb/risques_maison.md` en place).

Quand Météo-France place le département en vigilance **orange ou rouge**, Hélios affiche à ce foyer les gestes utiles pour **sa** maison (vent, orages, pluie-inondation, canicule, grand froid, neige-verglas).

**Source** : l'API « Bulletin Vigilance » de Météo-France (`DonneesPubliquesVigilance`), sur le portail `https://portail-api.meteofrance.fr`. Accès **avec compte** (Stéphane doit créer un compte et souscrire à l'API ; la gratuité et la forme exacte de l'identifiant sont à confirmer à l'inscription), limite de 60 requêtes par minute, produits JSON « carte » (niveaux par département et par phénomène) et « bulletin ». **Lire la documentation du portail avant d'écrire le client.**

Comme le client Enedis du dépôt, ce module est **dormant sans identifiant** : sans clé dans `.env`, il ne fait aucun appel et rien ne s'affiche.

## Décisions (déjà tranchées, à appliquer telles quelles)

| Sujet | Décision |
|---|---|
| Identifiant | `METEOFRANCE_API_KEY` (ou le nom exact qu'impose le portail) dans `.env`, ajouté à `deploy/A-FOURNIR-A-LA-MIGRATION.md`. Vide → module inactif. |
| Fréquence | Une seule collecte pour toute la France, au plus toutes les heures, gardée en base (`vigilance_departements` : département, phénomène, couleur, début, fin, date de collecte). Jamais un appel par foyer. |
| Seuil | Orange et rouge seulement. Jaune : rien. |
| Affichage | Bandeau en haut de l'espace du foyer concerné, et ligne dans « À faire ce mois-ci » tant que la vigilance court : phénomène, couleur, période, puis les gestes de la question correspondante de `kb/risques_maison.md`, avec le lien « Voir la carte de vigilance » (vigilance.meteofrance.fr). |
| Ton | Sobre : la couleur de Météo-France (orange ou rouge) sur une pastille, pas sur tout l'écran. Rouge : ajouter « Suivez les consignes des autorités ». |
| Après l'épisode | Pour vent violent et orages : une ligne proposée « Noter un dégât » (journal, photo), pendant 7 jours après la fin. |
| Chat | Si une vigilance orange ou rouge court pour le département du foyer, `carnet_contexte` l'ajoute (phénomène, couleur, fin), dans le plafond existant. |

## Méthode de travail

- Lire `services/enedis_client.py` (modèle du client dormant), `services/a_faire.py`, `services/carnet_contexte.py`, la documentation du portail Météo-France.
- Plan court, un commit par étape, message en français.
- À la fin : s'arrêter, résumer, captures avec une **réponse enregistrée** (fixture) simulant une vigilance orange vent dans le Var et une vigilance rouge canicule. **Attendre la validation de Stéphane.**
- Débrief `debriefs/AAAA-MM-JJ-p2-vigilance.md`. `CLAUDE.md` : 2 lignes au plus.

---

## 1. Client et collecte

`services/meteofrance_vigilance.py` : dormant sans clé ; collecte réduite aux champs gardés ; normalisation des phénomènes vers une liste fermée (`vent`, `orages`, `pluie_inondation`, `canicule`, `grand_froid`, `neige_verglas`, `autre`) ; tâche de collecte lancée par une commande (script), le planificateur de production viendra à la mise en ligne.

## 2. Fonctions pures

`vigilances_du_foyer(departement, vigilances, maintenant)`, `ligne_a_faire(vigilance)`, `apres_episode(vigilances, maintenant)`.

## 3. Écran

Bandeau, lignes « À faire », « Noter un dégât » après l'épisode.

## 4. Tests

- Sans clé : aucun appel, aucun affichage.
- Fixture orange vent Var : un foyer du Var voit le bandeau, un foyer du Nord non.
- Jaune ignoré ; fin d'épisode → bandeau retiré, « Noter un dégât » 7 jours.
- Aucun appel réseau dans les tests.
- Tests existants verts, build front vert.

## 5. TODO.md

Ligne « Phase 2, vigilance météo » cochée après vérification sur fixture. Point ouvert : **créer le compte Météo-France et vérifier la collecte réelle** (à faire par Stéphane, puis une vérification).

---

## À ne pas faire

- Aucun appel sans clé, aucun appel par foyer.
- Pas de notification, pas d'e-mail, pas de SMS.
- Ne jamais recopier le texte du bulletin officiel en le reformulant : afficher couleur, phénomène, période et nos gestes, et renvoyer vers la carte officielle.
- Ne pas modifier la fiche `kb/risques_maison.md`.
- **Aucune nouvelle dépendance.**
- Pas de journal daté dans `CLAUDE.md`.

## Critères d'acceptation

1. Avec une vigilance orange ou rouge, les foyers du département voient les bons gestes pour leur maison, et eux seuls.
2. Sans identifiant, le module ne fait rien et ne gêne rien.
3. Tests et build verts, captures sur fixture jointes, débrief écrit.
