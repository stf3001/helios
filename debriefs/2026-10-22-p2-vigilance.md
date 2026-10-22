# Débrief — Phase 2 « vigilance météo »

22/10/2026. Commits `a453cc4` → fin du lot sur `main`. Le lot attend la validation de Stéphane.

Consigne reçue en plus du brief : « ne sois pas trop anxiogène, ce lot est un petit plus ». C'est
elle qui a décidé de la place à l'écran (voir plus bas).

| Étape | Commit | État |
|---|---|---|
| Client Météo-France dormant sans clé, table par département (migration 0042), fonctions pures | `a453cc4` | fait |
| Route `GET /houses/me/vigilance`, bloc « À faire », contexte du chat | `6d72ee4` | fait |
| Écran : une ligne sobre dans « À faire », « Noter un dégât » après vent ou orages | `6132349` | fait |
| Test d'API rendu indépendant des données de dev, TODO (75 coché, 76 ouvert), CLAUDE.md, ce débrief | dernier commit | fait |

**811 tests au vert** : `test_vigilance.py` (7, sans réseau ni base) et `test_vigilance_api.py`
(3, contre la base de dev). `tsc -b` et `npm run build` passent (520 URL, inchangé).

## Ce qui n'est PAS vérifié : la vraie réponse de Météo-France

Il n'y a pas de clé, donc **aucun appel réel n'a été fait**. La carte de test
(`api/tests/fixtures/meteofrance/carte_simulee.json`) est **écrite à la main** d'après le format
documenté, et le fichier le dit (`_avertissement`). Elle contient du vent orange et des orages
orange dans le Var, une canicule rouge dans les Bouches-du-Rhône, du jaune dans le Nord (ignoré),
une zone littorale du Var (ignorée) et du vert dans le Finistère. Le jour où la clé existe, il faut
vérifier le format sur une vraie réponse et remplacer la fixture : c'est le point 76 de `TODO.md`.

Sans clé : `collecter_si_besoin` répond « dormant » sans même lire la base, la table reste vide et
rien ne s'affiche nulle part. Testé.

## Le principe : une collecte, beaucoup de lectures

- Seul `python -m scripts.collecter_vigilance` appelle Météo-France, **une fois pour toute la
  France**, au plus une fois par heure (`vigilance_collecte_min_minutes`). Jamais par foyer.
- La route du foyer, le bloc « À faire » et le chat **lisent la table**. Une panne de collecte ne
  casse rien : la table garde la dernière carte, les épisodes finis cessent de s'afficher seuls.
- Seuls l'orange et le rouge sont gardés. Les créneaux contigus d'un même phénomène sont fusionnés
  (J et J+1), avec la couleur la plus forte.
- Le texte du bulletin officiel n'est jamais repris : on affiche la couleur, le phénomène, l'heure
  de fin, et les gestes de **notre** fiche (`kb/risques_maison.md`, lue telle quelle, non modifiée),
  plus un lien vers la carte officielle.

## Sobre, comme demandé

- **Une seule apparition.** La vigilance est une ligne du bloc « À faire », pas un bandeau. Elle
  n'apparaît en haut de l'espace que pour un futur acheteur, qui n'a pas de bloc « À faire ». Jamais
  les deux.
- Une pastille de la couleur de Météo-France (jetons `--h-vigi-orange` et `--h-vigi-rouge` dans
  `index.css`), pas de fond coloré ni d'icône d'alerte.
- Les gestes sont **repliés** (« Les gestes pour votre maison »).
- En rouge seulement, une ligne de plus : « Suivez les consignes des autorités. »
- Rien sous l'orange, aucune notification, aucun e-mail.

## Vérifié dans le navigateur (foyers de `scripts/seed_risques_demo.py`, carte simulée chargée)

- **Var, vent orange** : une ligne dans « À faire », pastille orange, heure de fin, gestes repliés
  qui se déplient sur le texte de la fiche → `debriefs/captures/p2-vigilance-var-orange-vent.jpg`.
- **Marseille, canicule rouge** : pastille rouge et « Suivez les consignes des autorités. » →
  `debriefs/captures/p2-vigilance-marseille-rouge-canicule.jpg`.
- **Lille** : rien, ni ligne ni place réservée (vérifié dans le DOM).
- **« Noter un dégât »** (orages finis depuis moins de 7 jours) : le bouton bascule sur « Ma maison »
  et ouvre le journal pré-rempli (« Dégât après orages », intervenant « moi »). Le journal arrive à
  80 px du haut de l'écran. **Vérifié dans le DOM, pas en capture** : le panneau d'aperçu rend des
  captures blanches aussi bas dans la page. Premier essai raté : le défilement partait avant que
  « Ma maison » ait fini de charger. Le journal défile désormais lui-même, une fois ouvert.
- **375 px** : aucun débordement horizontal.
- Console sans erreur.

Après les captures, **les lignes simulées ont été effacées de la base de dev**. Pour les recharger,
depuis `api/` :

```bash
.venv/Scripts/python.exe -m scripts.collecter_vigilance --force --fixture tests/fixtures/meteofrance/carte_simulee.json
```

Les dates de la carte sont fixées au 22/10/2026 : passé cette date, les épisodes sont finis et
seul « Noter un dégât » reste visible, pendant 7 jours.

## Un piège trouvé en fin de lot

Avec la carte simulée chargée, le test d'API voyait deux « vent » dans le Var : celui qu'il pose,
plus celui de la collecte de dev. Le test travaille maintenant sur la Lozère (absente de la carte)
et purge ce département avant de poser ses épisodes.

## Reste ouvert

- **Point 76** : la clé Météo-France (à créer par Stéphane), puis une collecte réelle à vérifier,
  et la collecte horaire au déploiement (ligne ajoutée à `deploy/A-FOURNIR-A-LA-MIGRATION.md`).
- La neige-verglas n'a pas de question dans la fiche : elle s'affiche sans gestes.
- Point 74 (relire `kb/risques_maison.md`) : les gestes affichés en dépendent.
