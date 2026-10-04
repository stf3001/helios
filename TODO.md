# HELIOS — ce qui reste à faire

**Établie le 30/09/2026** par Claude, après les trois intégrations du simulateur
(eau, inertie, éolien) et la page « Le vent ».

Cette liste est classée par **risque pour l'entreprise**, pas par intérêt technique.
Un point coché est un point vérifié dans le code, pas un point qu'on croit fait.

Convention : chaque ligne dit **quoi**, **pourquoi ça compte**, **où c'est**.

---

## Bloquant — à traiter avant d'ouvrir le site au public

### [ ] 1. Aucun e-mail ne part de HELIOS

`api/app/services/email.py` est un bouchon : sans `EMAIL_API_KEY` (absente de
`api/.env`), les deux fonctions écrivent dans le journal et rendent la main.
Trois promesses tombent d'un coup :

- **Le partenaire ne reçoit jamais son lead.** `leads.py:83` appelle bien
  `send_lead_notification`, mais rien ne sort. Le doc 08 §2 annonce un contact
  sous 5 jours ouvrés : personne n'est prévenu qu'il a 5 jours.
- **Le rendez-vous téléphonique ne prévient personne** (voir le point 2).
- **L'e-mail de vérification de compte ne part pas.** Conséquence mineure :
  rien ne bloque la connexion sur `email_verified`, l'utilisateur entre quand
  même. À savoir quand on branchera le fournisseur : des comptes existants
  seront non vérifiés.

**Un seul branchement (Resend ou Brevo) débloque les trois.** C'est pour ça que
ce point est le premier.

### [ ] 2. Un rendez-vous réservé n'arrive nulle part

Le visiteur choisit son créneau de 30 minutes, la ligne s'écrit en base, et
**aucun écran ne la relit**. Stéphane ne voit pas les appels qu'il manque.

- Côté API : `api/app/routers/rendez_vous.py`, `api/app/services/creneaux.py`.
- Côté écran : `frontend/src/components/RendezVousTel.tsx`.
- Il manque : la notification (point 1) **et** un écran d'administration qui
  liste les réservations à venir.

**Décisions à prendre par Stéphane, elles ne sont pas techniques :**
qui reçoit les réservations, et sur quelles heures. Les plages inscrites dans
`config.py` (`rdv_plages_horaires` : 9 h-12 h 30 et 14 h-18 h, lundi-vendredi)
sont **inventées** — le commentaire du code le dit. Un créneau proposé engage
quelqu'un à décrocher.

### [ ] 3. Helios cite 91 entreprises qui n'existent pas

`api/scripts/seed_partenaires.py` contient 96 partenaires, dont **5 réels** :
AD Solar (PACA), Ensol (ailleurs), Hydrolia, Eolia, Energiesto. Les 91 autres
sont des noms tirés au hasard pour remplir l'annuaire pendant la construction.

Ils sont en base avec `statut = "actif"`, et `api/app/routers/chat.py:215` les
lit et **les donne au LLM, qui les nomme au visiteur**.

Deux risques : un visiteur qui cherche une société fantôme, et une vraie
société homonyme qui se découvre « partenaire HELIOS ». Le second n'est pas
théorique — la génération aléatoire a produit une collision **à l'intérieur de
sa propre liste** (« Armor Isolation »), d'où le garde-fou à la fin du script.

**Correctif d'une ligne** : passer les 91 en `statut = "en_attente"`. Helios ne
nomme plus que les vrais et dit franchement qu'il n'a pas encore de partenaire
référencé dans la région. On les réactive à la signature.

### [ ] 4. Les quatre experts sont des personnes inventées

`frontend/src/pages/HeliosIA.tsx` (constante `EQUIPE`) et `AvatarExpert.tsx` :
nom, âge, secteur, parcours, années de conseil en ENR. Les avatars sont des
dessins, ça se voit ; **les biographies, non**. Un visiteur réserve un appel
« avec Camille, 8 ans d'expérience ».

À remplacer par l'équipe réelle, ou à réduire à une présentation sans personnes
nommées.

---

## Chiffres affichés comme fermes, mais non sourcés

Ils portent tous un `A CONFIRMER` dans `api/app/core/config.py` — ce qui protège
le développeur, pas le client qui lit un prix à l'écran.

### [ ] 5. La hauteur de mesure du vent ERA5

`api/app/services/eolien.py`. Les profils ERA5 repris du projet eolia donnent un
facteur de charge de **26 % à Brest**, ce qui est haut pour de l'éolien
domestique. Si ces vitesses sont mesurées plus haut que le mât réel (1,8 m au
sommet pour rester en simple déclaration), **la production annoncée est
surévaluée**.

C'est le pire endroit du simulateur où se tromper : un client décide sur ce
chiffre. **À demander à EOLIA.**

### [ ] 6. La TVA du stockage par inertie

`simu_inertie_tva_pct = 20.0`. Supposée identique à celle d'une batterie. Si
l'inertie relève des 5,5 %, le prix affiché est faux de 14,5 points.

### [ ] 7. Le rendement aller-retour de l'inertie

Supposé égal au lithium, faute de donnée constructeur. Il commande directement
l'autonomie annoncée. **À demander à Energiesto.**

### [ ] 8. Les frais d'activation de la batterie virtuelle

Deux valeurs coexistent et je ne sais plus d'où elles viennent :
`mylight_activation_eur = 179` et `simu_msb_activation_eur = 279`. Les deux
portent « absent de la grille publique ». Vérifier s'il s'agit de deux choses
différentes, ou d'une seule mal recopiée.

### [ ] 9. La TVA du carport

`simu_carport_tva_pct = 20.0`, « par défaut ». À trancher.

---

## Contenu à écrire — l'outil est prêt, le texte manque

### [ ] 10. Les guides

`frontend/src/data/guides.ts` : les chapôs sont réels, les sections sont des
placeholders `[À rédiger]`. Choix assumé le 19/07/2026 (« structure seulement »).

### [ ] 11. Le glossaire

`frontend/src/data/glossaire.ts` : les montants d'aides sont marqués
`[à vérifier]`. Un montant d'aide faux engage HELIOS.

### [ ] 12. Deux trous connus de la base de connaissances

Relevés sur le terrain, toujours ouverts : **la fin de la revente totale** et
**l'ajout de puissance sur une installation existante**. Helios n'a rien à
répondre sur ces deux sujets, qui reviennent pourtant souvent.

---

## Ménage — sans risque, mais à ne pas oublier

### [ ] 13. Retirer `/potentiel-hydrique`, ou le rebrancher

Il lit encore `water_engine.py`, donc la table climatique inventée (point 14). Son remplaçant (la machine à eau du simulateur)
existe et tourne sur PVGIS. Route dans `frontend/src/App.tsx`, lien dans
`frontend/src/pages/Espace.tsx`.

### [ ] 14. Faire corriger la table climatique chez Hydrolia

`api/data/hydrolia/` : trois profils sinusoïdaux pour douze villes, Toulouse a
exactement le climat de Strasbourg, et **tous culminent en avril**. C'est un
défaut de la donnée d'origine du projet hydrolia, pas de son import ici. Tant
qu'il est là, tout ce qui lit cette table se trompe de saison.

### [x] 15. `.claude/launch.json` n'est pas versionné

**Fait le 30/09/2026 : committé.** Dix lignes qui disent comment lancer l'aperçu
(`npm run dev` dans `frontend/`, port 5173). Il part désormais avec le projet, et
Git ne le signale plus comme en attente.

### [ ] 16. Les images de marque sont restées à l'ancienne charte

La refonte visuelle du 30/09/2026 (direction « carnet de maison ») a changé le
site entier, mais **pas les fichiers PNG** : ils sont produits par un outil
graphique, pas par le code.

- `frontend/public/favicon-32.png`, `apple-touch-icon.png`, `icon-192.png`,
  `icon-512.png`, `icon-maskable-512.png` — l'ancien logo. Le favicon SVG, lui,
  est refait (`public/favicon.svg`) et passe en premier ; les PNG ne servent plus
  qu'aux navigateurs anciens et à l'écran d'accueil d'un téléphone.
- `frontend/public/og-image.png` — l'aperçu partagé sur les réseaux et dans les
  messageries. C'est celui qui se voit le plus : il porte encore le fond orange.
- `frontend/public/brand/logo-mark.png`, `logo-full.png`, `logo-house-sun.png` —
  plus référencés nulle part depuis la refonte. À supprimer ou à refaire.

La marque au trait existe en composant (`frontend/src/components/MarqueHelios.tsx`)
et en SVG (`public/favicon.svg`) : elle peut servir de base à l'export.

### [ ] 17. « hphc » s'écrit en deux orthographes dans le site

`frontend/src/pages/EspaceEnergie.tsx:317` propose `value="hphc"` en minuscules
dans le formulaire de courtage, alors que la fiche Maison et le simulateur
écrivent **`HPHC`** en capitales (`OptionTarifaire` dans
`api/app/schemas/house.py`). Les deux écrans ne parlent donc pas de la même
chose, et une valeur saisie dans l'un ne se relit pas dans l'autre.

Repéré le 01/10/2026 en ajoutant l'option tarifaire au simulateur, qui a été
alignée sur la fiche. Celui de l'espace énergie ne l'est pas : il part dans
`POST /api/energy/courtage`, pas dans la fiche, donc rien n'est cassé
aujourd'hui — mais les deux finiront par se croiser.

### [ ] 18. Le puits canadien n'entre dans aucun calcul

Ajouté à la scène le 01/10/2026 : on peut le poser, il s'affiche, et l'écran
dit franchement qu'il ne change aucun chiffre. C'est honnête, mais c'est un
emplacement qui ne sert qu'à l'image.

Lui donner un effet demande une entrée au moteur (`simu_conso`), donc un champ
de plus dans `SimulateurIn` — qui est en `extra="forbid"`. Ce n'est pas une
ligne de code : c'est un modèle thermique de plus, et des hypothèses à assumer
dans `config.py` comme toutes les autres.

### [ ] 19. Le puits canadien ne dit pas ce qu'il fait gagner

La page « La terre » a gagné une partie puits canadien le 01/10/2026
(`frontend/src/pages/Terre.tsx`, sections 4 à 7 de `la-terre` dans
`src/data/piliers.json`). Elle explique le principe, donne les températures
d'entrée et de sortie, et **s'arrête là** : aucun euro, aucun pourcentage sur la
facture. C'est une décision de Stéphane, pas un oubli — le gain dépend du climat,
du sol, de la ventilation et de ce qu'on chauffe, et nous n'avons pas de quoi le
calculer honnêtement.

**Ce qu'il faudra pour un calculateur**, le jour venu : la température de sol de
la commune (profondeur 2 m), le débit de ventilation réglementaire du logement,
la longueur et le diamètre enterrés, et le système de chauffage ou de
climatisation que le puits soulage. Les deux premières données existent déjà à
moitié dans le moteur (`simu_conso` connaît le logement, `pvgis` connaît le
lieu) ; la température de sol, non.

**À confirmer par Stéphane** avant de publier un chiffre : le coût d'une
installation. Le rapport de recherche donne 5 000 à 11 000 € TTC pour une maison,
mais en annonçant lui-même que la valeur est estimée. Elle n'est **pas** sur la
page, volontairement.

Deux textes à relire quand le calculateur arrivera, parce qu'ils promettent qu'il
viendra : la section 7 de `piliers.json` et le bloc « parler-vrai » de la page.

### [x] 20. Helios n'avait aucune mémoire de la conversation — fait le 02/10/2026

Le point disait « la recherche ne voit que le dernier message ». En ouvrant le
code, le défaut était plus large : **Helios ne recevait jamais les tours
précédents**. Le prompt contenait la constitution, les fiches trouvées, la fiche
du foyer, ses études — puis la question seule. « Et pour une maison de 1970 ? »
n'avait aucun sens pour lui ; « tu m'as dit 6 kWc » non plus.

L'historique était pourtant écrit en base depuis le premier jour, et le widget
renvoyait déjà le `conversation_id`. Il n'était simplement jamais relu.

**Deux pièces, dans `rag.py` et `chat.py`** :

- `build_historique_context()` pose les 3 derniers échanges dans le prompt, juste
  au-dessus de la question. Bloc de TEXTE et non tableau de messages : Ollama
  n'a pas de notion de conversation, et un seul bloc sert les deux chemins sans
  toucher à la mise en cache du préfixe Anthropic.
- `question_pour_recherche()` recolle les 2 questions précédentes quand le
  message fait moins de 45 caractères — une relance ne nomme pas son sujet.

**Trois réglages, trois mesures, pas des intuitions** :

- 45 caractères, et non 80 : à 80, « à partir de quelle lettre je ne peux plus
  louer ? » se faisait diluer par « c'est quoi le DPE » et PERDAIT la bonne fiche
  qu'elle trouvait seule.
- 2 questions d'ancrage, et non 1 : au troisième tour, la question précédente est
  souvent elle-même une relance et ne nomme plus le sujet.
- `RELANCE_INSTANT_MIN = 0,70` : une relance exige plus de certitude avant qu'une
  fiche ne soit servie telle quelle, sans modèle. « Et mes panneaux solaires ? »,
  après une question sur le puits canadien, remontait la fiche du PUITS à 0,661 —
  juste au-dessus du seuil normal.

**Mesuré sur 15 conversations** : 3 questions passent de sous le seuil à
au-dessus, 0 l'inverse. Et plusieurs réponses confiantes mais fausses sont
corrigées — « combien ça coûte ? » après le puits canadien partait sur
« PAC air-eau : prix », « et l'hiver ? » sur « que peut-on récolter en hiver ».

**Vérifié de bout en bout** par une vraie conversation de quatre tours : au
dernier, « récapitule ce que tu viens de me dire » produit un vrai résumé des
trois précédents. Avant, Helios ne pouvait qu'inventer.

**Reste ouvert** : le modèle LOCAL (`llama3.2:3b`) reste faible sur un prompt
long, historique compris — il suit, mais il reformule mal. Ce n'est pas une
régression de ce lot, c'est la limite déjà connue du 3B. Si elle devient gênante,
l'historique peut être réservé au chemin API en une ligne.


### [ ] 21. La photo du héros est en 1536 px de large

Héros d'accueil refondu le 02/10/2026 (`frontend/src/pages/Home.tsx`,
`frontend/src/components/CarteMaison.tsx`, photo `frontend/public/maison-hero.webp`).

La photo fournie par Stéphane fait **1536 × 1024** (397 Ko). Plein cadre sur un
écran 1920 elle est agrandie 1,25 fois ; sur un écran à forte densité, davantage —
ça se verra sur les feuilles d'olivier et les arêtes de tuiles. Une version en
2560 ou 3072 de large se déposerait au même chemin **sans toucher à la mise en
page** : tout passe par la constante `PHOTO` en tête de `Home.tsx`.

**CE QU'IL NE FAUT PAS DÉFAIRE EN CHANGEANT L'IMAGE.** Le voile ivoire du héros
décroît du bord gauche jusqu'à 80 % **sans aucun palier d'opacité constante** :
c'est ce qui le fait lire comme une brume et non comme une découpe. Deux versions
antérieures ont été refusées pour la même raison en miroir — un voile opaque
jusqu'à 55 %, puis une photo bornée à un bloc de 58 % — parce que toutes deux
produisaient DEUX zones au lieu d'une image, avec une couture verticale d'autant
plus visible que l'écran est large.

Ses six arrêts ne sont pas un réglage esthétique : ils sont **mesurés**. Un script
de contrôle échantillonne les pixels réels de la photo sous chaque bloc de texte,
les composite avec l'alpha exact du dégradé à cette abscisse et calcule le contraste
WCAG. Relevé du 02/10/2026, sur le pixel le plus sombre de chaque bloc :

| largeur | titre (encre) | italique (terracotta) | sous-titre (encre 80 %) |
|---|---|---|---|
| 1024 | 9,06 | 4,70 | 5,77 |
| 1280 | 9,31 | 3,95 | 5,88 |
| 1440 | 8,77 | 3,78 | 5,77 |
| 1920 | 8,73 | 3,62 | 5,88 |

Seuils : 3:1 pour les deux premiers (grand texte), 4,5:1 pour le troisième.
**Le cas critique est l'italique terracotta** : il demande un fond de luminance
0,73 pour tenir 4,5:1, ce qu'aucune photo ne donne — il ne passe que parce qu'il
est en grand corps. Toute photo plus sombre, ou tout élargissement de la colonne
de texte, doit être revérifié par ce relevé.

Deux conséquences à ne pas « simplifier » :
- Le sous-titre est en `text-ink/80` et non en `text-gray-600`. Le gris secondaire
  du site demande un fond de luminance 0,61 : il est calibré pour l'ivoire plein,
  pas pour un flanc de colline vu à travers une brume.
- Le dégradé se termine sur `rgb(var(--h-sable) / 0)` et **jamais** sur
  `transparent`. En CSS `transparent` vaut `rgba(0,0,0,0)` : interpolé en sRGB il
  tire le dégradé vers le noir et salit tout le raccord.

Enfin, `object-[center_30%]` remonte le cadre pour garder la toiture solaire
entière — seul élément de l'image qui porte le propos ; la piscine, elle, sort du
cadre, ce qui ne se regrette pas (voir la réserve ci-dessous).

**Réserve de fond, posée et écartée par Stéphane le 02/10/2026** : la photo montre
une villa avec piscine, alors que la promesse est d'économiser 450 € par an. Le
risque est de ciblage, pas d'esthétique. Décision prise en connaissance de cause,
ne pas y revenir sans qu'il le redemande.

### [ ] 22. Un menu « soleil » à part entière

Demandé par Stéphane le 02/10/2026. Aujourd'hui le solaire n'a pas d'entrée de
menu à lui : il est logé dans « La maison de demain » (`/simulateur-solaire`),
à côté du vent, de l'eau et de la terre, alors que c'est le sujet central du site
et le seul dont le simulateur est complet.

Les trois autres entrées (`Le vent`, `L'eau`, `La terre`) **ne bougent pas** :
décision de Stéphane du 02/10/2026, prise en connaissance de la critique (ces
intitulés ne disent pas ce qu'il y a derrière). Le menu soleil s'ajoutera à côté.

À trancher quand le point sera ouvert : ce que contient cette entrée par rapport à
`/simulateur-solaire` et à `Ville.tsx`, qui parle déjà d'installations en kWc, et
si l'en-tête supporte une huitième entrée — il en porte déjà sept et passe en
`text-[13px]` sous 1280 px pour les faire tenir (`components/layout/Header.tsx`).

---

## Le piège à ne pas réintroduire

Trouvé deux fois en deux jours, sous deux formes :

**Une valeur refusée par l'API doit toujours dire laquelle, et où.** Le
29/09/2026, une fiche Maison portant `orientation_toiture: "SUD"` faisait
échouer *chaque* calcul en silence. Le 30/09, un zéro dans un champ facultatif
faisait la même chose. Dans les deux cas le serveur avait raison, et l'écran
affichait « Le calcul n'a pas abouti » sans rien de plus.

Trois garde-fous existent maintenant, à garder :
`valeurAdmise()` et `nombreAdmis()` dans `SimulateurSolaire.tsx` filtrent ce qui
vient de la fiche ; les bornes `min`/`max` de `Champ` filtrent ce qui est tapé ;
`messageDErreur()` dans `lib/simulateur.ts` traduit ce qui passe quand même.

**Une erreur de validation de FastAPI renvoie `detail` sous forme de LISTE**,
pas de texte. Un écran qui ne lit que le texte restera muet.
