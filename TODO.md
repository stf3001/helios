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

### [x] 3. Helios citait 96 entreprises qui n'existent pas — fait le 06/10/2026

`api/scripts/seed_partenaires.py` contient 96 partenaires, dont **5 réels** :
AD Solar (PACA), Ensol (ailleurs), Hydrolia, Eolia, Energiesto. Les 91 autres
sont des noms tirés au hasard pour remplir l'annuaire pendant la construction.

Ils sont en base avec `statut = "actif"`, et `api/app/routers/chat.py:215` les
lit et **les donne au LLM, qui les nomme au visiteur**.

Deux risques : un visiteur qui cherche une société fantôme, et une vraie
société homonyme qui se découvre « partenaire HELIOS ». Le second n'est pas
théorique — la génération aléatoire a produit une collision **à l'intérieur de
sa propre liste** (« Armor Isolation »), d'où le garde-fou à la fin du script.

**Fait, et il y en avait quatre de plus que prévu.** Le seed pose désormais
`statut = "actif"` pour les seules cinq entreprises réelles (`REELS` dans le script) et
laisse les 92 autres en `en_attente` — statut que l'annuaire public
(`routers/partners.py:29`) et le chat (`routers/chat.py:250`) filtrent déjà tous les deux.

**Quatre partenaires actifs échappaient au seed**, parce qu'ils ne figurent dans aucune
de ses listes : « Armor Solaire » et « Armor Thermique », restes d'un nommage abandonné
(remplacé depuis par Iroise/Brocéliande), puis « Solaris Renov » et « Courtage Energie
Pro », partenaires de test du jalon 8. Tous inventés, tous nommés par Helios. Basculés à
la main, un par un.

Le script **ne les désactive pas d'office** — ce serait défaire une activation faite
depuis `/admin` — mais il **affiche désormais tout partenaire actif qu'il ne connaît
pas**, pour que le trou ne se reforme pas en silence.

**Vérifié en base le 06/10/2026** : 5 actifs (AD Solar, Energiesto, Ensol, Eolia,
Hydrolia), 92 en attente. Le seed relancé est idempotent et ne réactive rien.

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

### [ ] 5. Vérifier les données de vent et le calculateur éolien

`api/app/services/eolien.py`. Les données de vent sont jugées fiables par
Stéphane (sources Météo-France, précisé le 04/10/2026) : il ne s'agit pas de les
remettre en cause, mais **simplement de vérifier** que les données chargées et
le calcul du simulateur donnent bien la production attendue (contrôle sur
quelques villes, dont Brest, où le facteur de charge actuel ressort à 26 %).

Rappel : la production annoncée sera de toute façon confirmée chez le client par
le prêt d'anémomètre d'EOLIA.

### [x] 6. La TVA du stockage par inertie — tranchée à 5,5 % le 06/10/2026

Stéphane a tranché : **5,5 %**. Le réglage `simu_inertie_tva_pct` était en plus **mort** —
le moteur prenait `simu_inertie_cout_ttc_eur = 8500` tel quel et ne lisait jamais le taux.
Changer le seul taux n'aurait donc rien changé à l'écran.

Corrigé en posant le HT que contenait ce devis (8 500 / 1,20 = **7 083 €**, nouveau
`simu_inertie_cout_ht_eur`) et en laissant le moteur appliquer le taux (`_inertie_ttc()`
dans `simu_engine.py`, utilisé aux deux endroits qui affichaient le prix). **Prix affiché :
8 500 € → 7 473 € TTC.** Le repli en dur de `ReglageEquipement.tsx` a suivi.

**IL RESTE UNE SECONDE QUESTION, NON TRANCHÉE, QUI PÈSE PLUS LOURD.** Ce qui précède ne
concerne que le taux porté par le stockage lui-même. Le moteur continue de supposer
qu'ajouter de l'inertie fait basculer **tout le photovoltaïque** à 20 %, comme le ferait
une batterie lithium (`investissement()`, et le test
`test_l_inertie_fait_basculer_la_tva_comme_une_batterie` qui l'encode). Sur un projet de
6 kWc, cette hypothèse déplace plusieurs milliers d'euros — bien plus que les 1 027 € que
vient de rendre la première. Les deux sont logiquement liées : si l'inertie est à 5,5 %,
il est douteux qu'elle disqualifie le reste. **Laissé à l'hypothèse prudente** (prix
affiché plus élevé) en attendant la réponse.

### [ ] 7. Le rendement aller-retour de l'inertie

Supposé égal au lithium, faute de donnée constructeur. Il commande directement
l'autonomie annoncée. **À demander à Energiesto** — en même temps que la question
fiscale restée ouverte au point 6.

### [x] 8. Les frais d'activation de la batterie virtuelle — 279 €, le 06/10/2026

C'étaient bien **deux réglages pour une seule chose** : ils alimentaient les deux offres
MyLight de `batterie_virtuelle.offres()` (« sur-mesure » à 279 €, « illimité » à 179 €),
alors que l'activation est celle du compte, commune aux deux.

Stéphane a tranché : **279 €**. `simu_msb_activation_eur` est supprimé, les deux offres
lisent `mylight_activation_eur = 279`. **Un seul réglage** — c'est le fait d'en avoir eu
deux qui avait fabriqué le doute.

### [x] 9. La TVA du carport — tranchée le 06/10/2026

Règle de Stéphane : **5,5 % sur la partie solaire, 20 % sur la structure.** Vérifié dans
le code : **c'est déjà exactement ce que fait le moteur**, et ce n'était écrit nulle part.
Les panneaux du carport entrent dans le kWc total (`_kwc_total`) et sont donc facturés sur
la ligne photovoltaïque, au taux du projet ; la ligne carport ne porte que l'acier et la
pose (`simu_carport_cout_par_panneau_eur`, « structure seule, hors panneau »), d'où le
taux plein.

Aucun calcul à changer : le `A CONFIRMER` est remplacé par la règle et son explication,
pour que personne ne « corrige » la ligne à 5,5 % en croyant bien faire.

---

## Contenu à écrire — l'outil est prêt, le texte manque

### [ ] 10. Les guides

`frontend/src/data/guides.ts` : les chapôs sont réels, les sections sont des
placeholders `[À rédiger]`. Choix assumé le 19/07/2026 (« structure seulement »).

### [ ] 11. Le glossaire

`frontend/src/data/glossaire.ts` : les montants d'aides sont marqués
`[à vérifier]`. Un montant d'aide faux engage HELIOS.

### [x] 12. Deux trous connus de la base de connaissances — comblés

Relevés sur le terrain : **la fin de la revente totale** et **l'ajout de
puissance sur une installation existante**. Les deux sont désormais traités, et
c'est vérifié dans la base servie par `/api/faq` le 05/10/2026, pas seulement
dans `kb/` : six fiches répondent (« Mon contrat de vente totale arrive à son
terme », « Faut-il résilier un contrat de vente totale qui arrive à échéance »,
« Ajouter des panneaux plus tard, combien ça coûte », « Puis-je ajouter des
panneaux à une installation déjà sous contrat de rachat », « Puis-je regrouper
deux installations derrière un seul compteur », « Autoconsommation totale, avec
vente de surplus, ou vente totale »). Source : `kb/fin_contrat_rachat.md` et
`kb/dimensionnement_pv.md`.

### [x] 23. Ce que la page « Le soleil » disait et qu'Helios ne savait pas dire — fait le 05/10/2026

Trouvé en écrivant la page, en contrôlant chaque affirmation contre `/api/faq` :
deux sujets de la page n'avaient aucune fiche derrière eux. **13 fiches écrites,
ingérées et vérifiées en conditions réelles.**

- `kb/recyclage_carbone.md` (**7 fiches**) : fin de vie et filière Soren
  (éco-participation déjà payée, 94 % de valorisation dont ~84 % de recyclage
  matière, 13 760 t collectées en 2025), bilan carbone (25 g pour un module
  européen, 44 g pour un module chinois, retour énergétique 1 à 3 ans),
  onduleur et structures, batteries, panneaux d'occasion. **La fiche qui
  justifie le lot** : « Poser des panneaux en France fait-il vraiment baisser
  mes émissions de CO₂ ? » — le réseau français était à 19,6 g de CO₂ par kWh
  en 2025, donc le gain climatique d'un toit solaire va de faible à nul ici.
  La fiche le dit, pose les deux nuances qui jouent en sens inverse, et renvoie
  vers l'isolation. Aucun installateur n'écrira cela à notre place.
- `kb/choisir_installateur.md` (**6 fiches**) : vérifier l'existence et la
  solidité d'une société (SIREN, annuaire-entreprises.data.gouv.fr, comptes
  publiés), lire une attestation de décennale — **et le point mal connu,
  vérifié : la garantie est attachée au chantier, pas à la survie de
  l'entreprise ; liquidée cinq ans après, c'est l'assureur qui répond, à
  condition de pouvoir le nommer, donc on conserve l'attestation dix ans** —,
  lire des avis en ligne, la sous-traitance, les mentions obligatoires d'un
  devis, les acomptes.

**Deux quasi-doublons trouvés et fusionnés au passage.** Le contrôle par
voisinage vectoriel (chaque nouvelle fiche confrontée à sa plus proche voisine
en base) a sorti deux paires au-dessus de 0,72 : « Quel acompte est raisonnable
avant travaux ? » (0,776) et « Quelles mentions obligatoires sur un devis de
rénovation ? » (0,728), toutes deux dans `faq_maison`. Leurs apports concrets
— 10 à 30 % à la commande, jamais plus de la moitié avant le début effectif,
accord écrit des aides avant signature, mention RGE quand les aides en
dépendent — ont été reversés dans les nouvelles fiches, et les anciennes
retirées de `kb/faq_maison.md` (108 → 106). `_elaguer` les a bien supprimées de
la base au ré-crawl (« 2 retirés »). **Ce contrôle est à refaire à chaque lot de
fiches** : deux fiches qui se disputent la même question font répondre Helios
différemment selon celle qui remonte.

**Vérifié réellement** : base à 388 fiches publiques (375 + 13, moins les 2
doublons), `/api/faq` les sert, et trois questions posées au vrai chat
retrouvent les bonnes fiches — réponse instantanée sans LLM sur « le solaire
baisse-t-il vraiment mes émissions » et « que deviennent les panneaux en fin de
vie », et pour une question plus large sur l'entreprise, les deux nouvelles
fiches remontent dans les sources données au modèle. Pré-rendu : 388 pages de
fiches, plan de site à 420 URL.

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

### [x] 16. Les images de marque sont passées à la charte — fait le 06/10/2026

La refonte du 30/09/2026 avait changé le site entier mais **pas les fichiers PNG**. Ils
sont désormais **produits par le code** (`frontend/scripts/brand_assets.py`, à relancer
quand la charte bouge) : le même soleil au trait que `MarqueHelios.tsx` et
`public/favicon.svg`, en terracotta `--h-accent` sur l'ivoire `--h-sable`, tracé en
sur-échantillonnage ×4 pour que les bords soient lissés.

Les sept fichiers refaits : `favicon-32.png` (transparent, trait épaissi comme le SVG),
`apple-touch-icon.png` (fond opaque, iOS n'en pose aucun), `icon-192`, `icon-512`,
`icon-maskable-512` (dessin réduit à 45 % du côté pour tenir dans la zone sûre d'Android),
`brand/logo-mark.png` et `og-image.png` (ivoire, « Helios » en Instrument Serif,
l'accroche du site en italique terracotta).

**`logo-mark.png` n'était pas orphelin, contrairement à ce que disait ce point** :
`api/app/services/pdf_audit.py` le met en tête de chaque PDF de pré-audit. Il a donc été
refait, et non supprimé. Au passage, le PDF calculait la position de son titre avec le
rapport `1920/1113` **écrit en dur** ; la marque étant carrée désormais, il lit le rapport
du fichier. Vérifié sur un vrai PDF rendu.

`logo-full.png` et `logo-house-sun.png`, eux, n'étaient référencés nulle part (vérifié sur
tout le dépôt) : supprimés.

**Reste, hors de ce point** : la palette du PDF de pré-audit (`pdf_audit.py`, constantes
`ORANGE` / `INK` / `CREAM`) est encore celle de l'ancienne charte. Trois lignes, mais c'est
un document client — à faire volontairement, pas en passant.

### [x] 17. « hphc » s'écrivait en deux orthographes — fait le 06/10/2026

`frontend/src/pages/EspaceEnergie.tsx:317` propose `value="hphc"` en minuscules
dans le formulaire de courtage, alors que la fiche Maison et le simulateur
écrivent **`HPHC`** en capitales (`OptionTarifaire` dans
`api/app/schemas/house.py`). Les deux écrans ne parlent donc pas de la même
chose, et une valeur saisie dans l'un ne se relit pas dans l'autre.

Repéré le 01/10/2026 en ajoutant l'option tarifaire au simulateur, qui a été alignée
sur la fiche.

**Ils se croisaient déjà**, contrairement à ce qui était écrit ici : `courtage_client.py:29`
retombe sur `house.option_tarifaire` — donc `HPHC`, en capitales — quand le champ du
formulaire est laissé vide. Les deux orthographes finissaient dans le même dictionnaire,
selon que l'utilisateur remplissait le champ ou non.

Aligné sur la fiche Maison, qui est la référence : `<option value="HPHC">` dans
`EspaceEnergie.tsx`, et le `Literal` de `schemas/energy.py` qui l'accompagne.
`energy_advisor.py:92` n'a pas bougé : il compare après `.lower()`, insensible à la casse
volontairement.

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

### [x] 22. Un menu « soleil » à part entière — fait le 05/10/2026

Demandé par Stéphane le 02/10/2026, réalisé le 05/10. « Le soleil » est la
troisième entrée du menu, juste avant « Le vent ». Les trois autres éléments
n'ont pas bougé, comme décidé.

**Ce qui a été tranché, et pourquoi :**

- **Adresse `/solaire`, pas `/le-soleil`.** `/solaire` existait déjà comme page
  chapeau générique issue de la campagne de référencement : elle est au plan de
  site, et 99 fiches de la FAQ pointent dessus par leur ligne « Sujet : ». Créer
  une seconde adresse aurait fabriqué deux pages sur le même sujet — ce que les
  moteurs sanctionnent — et coupé la nouvelle page de tous ses liens entrants.
  `/le-soleil` existe quand même, en redirection, par symétrie avec `/le-vent`.
- **Pas de simulateur**, comme sur « Le vent », « L'eau » et « La terre » : le
  chiffrage reste dans « La maison de demain », et la page y renvoie.
- **Cinq onglets** (matériel, pose et dossier, garanties et installateur,
  stockage, marché et empreinte), chacun avec de petites vignettes et des
  `<details>` natifs pour le détail ; six conditions d'un projet réussi en tête
  pour qui n'ouvrira aucun onglet. L'onglet vit dans l'URL (`?sujet=`), un lien
  peut donc viser directement les garanties.
- **La huitième entrée d'en-tête tient.** Mesuré dans le navigateur à 1024 px,
  la largeur exacte du point de bascule : `scrollWidth` = `clientWidth` = 1009,
  aucun débordement. Vérifié aussi à 1280 px et en mobile (menu burger).

Fichiers : `frontend/src/pages/Soleil.tsx` (mise en page),
`frontend/src/data/soleil.ts` (le texte), entrée `solaire` de
`frontend/src/data/piliers.json` passée en `pageDediee` et réécrite (c'est elle
que lit le pré-rendu SEO), `App.tsx`, `components/layout/Header.tsx`.

**Ce qui reste** : les deux sujets de la page qui n'ont pas de fiche dans la
base de connaissances — voir le point 23.

---

### [x] 24. L'espace client était froid et trop long — refait le 06/10/2026

Trois reproches de Stéphane, tous fondés, tous mesurés avant et après.

**On atterrissait sur le formulaire.** `Login.tsx` envoyait sur `/mon-espace`, c'est-à-dire
46 champs, au lieu de l'accueil de l'espace. Corrigé : `/espace`. Et la page de connexion
honore maintenant le `state.from` que `AdminRoute` et `ProtectedRoute` lui passaient déjà
sans que personne ne le lise — viser `/admin` déconnecté ramène sur `/admin`, plus ailleurs.
`Register.tsx` va lui aussi sur `/espace`, qui met en scène les trois questions de départ
plutôt que d'ouvrir une fiche vide.

**La fiche dépliait ses six blocs d'un coup.** Ils sont repliés, chacun portant son
avancement réel (« ✓ complet », « 9 / 11 », « 1 / 5 ») et une icône. Le résumé est ce qui
rend le pliage utile : fermé, un bloc dit déjà où il en est, donc on ouvre celui qu'on veut
remplir au lieu de les ouvrir tous pour chercher. **Mesuré : 6 244 px → 2 274 px, soit
6,6 écrans de défilement en moins.**

**L'accueil de l'espace était froid et long.** Photo « carnet de maison » en en-tête (la
même que l'accueil du site, donc on reste chez soi en se connectant), résumé de fiche
ramené d'un pavé à une ligne, tuiles resserrées sur deux lignes au lieu de trois, et les
trois rangées pliées sous le même motif. **Mesuré : 981 px gagnés, 1,6 écran.**

**Le bloc de conversation, repris dans la foulée** (« cette section est moche ») : les
trois amorces de questions sont supprimées (`SUGGESTIONS` dans `ChatWidget.tsx`), la boîte
passe de 70 vh à 44 vh via une prop `compact` — la page publique `/helios` garde la grande,
elle n'a que la conversation à montrer —, et le bloc devient lui aussi un dépliant.

**Il est OUVERT à l'arrivée**, volontairement : la conversation est ce pour quoi on vient
dans l'espace, la replier d'office remettrait un clic entre le client et Helios, ce que la
fusion du 30/09 avait justement supprimé. À changer en retirant `ouvert` si Stéphane préfère.

Deux détails qui ne s'inventent pas : les commandes (« Mes conversations », « Nouvelle »)
sont DANS le panneau et non dans l'en-tête, parce qu'un bouton posé dans un `<summary>`
replie le bloc quand on le clique ; et en mode compact le widget perd sa bordure pleine au
profit d'un filet plus clair, sans quoi son cadre et celui du dépliant faisaient **deux
boîtes imbriquées** — précisément ce qui donnait l'impression de « moche ».

**Puis le rail d'onglets a remplacé l'empilement** (« regarde le menu dépliant gauche, je
le trouve super sympa »). « Mon espace » reprend le rail du simulateur : colonne d'icônes à
gauche à partir de `md`, bande horizontale en dessous, cinq sections — Helios, Ma maison,
Simuler, Papiers, Le reste. **Mesuré : 2 173 px → 1 265 px**, la page tient à l'écran.

Trois choses qui ne se voient pas et qu'il ne faut pas défaire :

- **La conversation reste MONTÉE quand on change d'onglet**, simplement cachée. La démonter
  perdrait les messages à l'écran, l'identifiant de conversation et la question en cours de
  frappe dès qu'on va regarder ses documents. Vérifié : un texte saisi est toujours là au
  retour.
- **Le rail ne porte que ce qui vit sur cette page.** Pré-audits, énergie, partenaires et
  pro sont de vraies pages ; en faire des onglets donnerait un `tablist` dont la moitié des
  onglets quittent la page, ce qui ment au clavier comme au lecteur d'écran. Ils sont
  regroupés dans l'onglet « Le reste ».
- **`components/RailOnglets.tsx` n'est PAS le rail du simulateur, et c'est délibéré.**
  Celui de `SimulateurSolaire.tsx` est soudé à sa grille de trois colonnes : bouton
  « Replier », panneau qui s'ouvre en calque flottant sous `xl`, bordures qui changent selon
  qu'il partage ou non la boîte du panneau. Le partager aurait demandé une demi-douzaine de
  props pour piloter tout ça de l'extérieur — plus coûteux que trente lignes dupliquées.
  Ce qui EST partagé, c'est le dessin du bouton, parce que c'est lui qu'on voit.

**Un seul dépliant pour tout le site** : `components/Depliant.tsx`. Il vivait dans
`components/simulateur/Onglets.tsx` (c'est le motif de « La maison de demain », que
Stéphane a demandé de reprendre) ; il en a été sorti plutôt que recopié — trois copies
auraient divergé au premier ajustement, et ça se verrait sur toutes les pages à la fois.
`<details>` natif : clavier, lecteur d'écran et recherche dans la page marchent sans
qu'on les recode. **Ne pas le passer en composant contrôlé.**

**Reste ouvert** : le voile de l'en-tête photo n'a PAS été soumis au relevé de contraste
WCAG qu'on applique au héros de l'accueil (point 21). Le texte est posé sur la partie
pleinement ivoire du dégradé, donc le cas critique de l'accueil ne se présente pas ici —
mais si la photo change, ou si la colonne de texte s'élargit, il faudra mesurer.

---

### [ ] 25. Le champ `zones` d'un partenaire n'a aucun format imposé

Trouvé le 08/10/2026 en rangeant `/admin/partenaires` par région. `partners.zones`
est un tableau de chaînes rempli par un champ de saisie LIBRE
(`frontend/src/pages/DevenirPartenaire.tsx` : `zones.split(',')`). Rien ne dit si on
y met un numéro de département (« 13 ») ou un code postal (« 13100 »). Le seed écrit
des départements, un partenaire de test écrivait des codes postaux — les deux
cohabitent déjà en base.

**Trois endroits le lisent, de trois façons différentes :**

- `api/app/routers/chat.py:252` — `departement not in partenaire.zones`, égalité
  stricte. Un partenaire qui a déclaré des codes postaux n'est JAMAIS proposé par
  Helios. C'est le chemin qui compte : c'est celui qui décide qui est nommé au client.
- `api/app/routers/partners.py:35` — `z.startswith(zone[:2])`, préfixe à deux
  caractères. Tolérant aux deux formes, **sauf en Corse** : une saisie « 20000 »
  donne « 20 », et « 2A » ne commence pas par « 20 ». Vérifié : 20000 et 20200 ne
  retrouvent aucun des partenaires corses du seed. Ce paramètre `zone` n'est appelé
  par aucun écran aujourd'hui — le défaut est donc latent, pas visible.
- `frontend/src/data/regions.ts` — `departementDeLaZone()`, écrit ce jour-là, qui
  applique la règle de `departement_du_code_postal` (Corse comprise) pour ranger les
  partenaires en vignettes.

**Ce qu'il faudrait faire** : normaliser à l'ÉCRITURE, dans `POST /partners/apply`,
avec `regions.departement_du_code_postal` — une zone enregistrée serait alors toujours
un numéro de département, et les trois lecteurs retomberaient d'accord sans rien
changer d'autre. Prévoir la reprise des lignes déjà en base.

Sans risque tant que l'annuaire n'est rempli que par le seed. Devient réel le jour où
une vraie candidature arrive par le formulaire public.

## Le piège à ne pas réintroduire

**Un jeton de rafraîchissement à usage unique ne supporte pas deux appels en même
temps** (trouvé le 06/10/2026, après que Stéphane a signalé qu'il « galérait » à entrer
dans l'espace client et le back-office). Le symptôme : on se connecte, ça marche, puis
on ouvre `/admin` ou on recharge la page — et on retombe sur l'écran de connexion. Une
fois sur deux. Les identifiants sont bons, la session existe, le serveur répond.

La cause tient en deux pièces qui, séparément, sont justes :

- `routers/auth.py` révoque le jeton dès qu'il sert (« un refresh token ne sert qu'une
  fois ») — c'est la rotation, et c'est voulu ;
- `AuthContext.authFetch` relançait un rafraîchissement à **chaque** 401 reçu, sans
  savoir qu'un autre était déjà parti.

Deux appels concurrents se détruisent donc l'un l'autre : le premier consomme le jeton,
le second présente un jeton déjà révoqué, reçoit 401, et son `setUser(null)` **efface la
session que le premier venait de rétablir**. Celui qui répond en dernier gagne. D'où le
pile ou face.

Le back-office le déclenchait le plus souvent parce que son tableau de bord interroge
plusieurs endpoints en parallèle. Et le `StrictMode` de `main.tsx` double tout en
développement : **11 appels de rafraîchissement mesurés pour UN seul chargement de page**,
dont deux 401.

Correctif : `tryRefresh()` garde la promesse en cours dans un `useRef` et tout le monde
attend la même. **Mesuré après : 1 appel par chargement, sur quatre pages d'affilée, zéro
rebond.** Ne pas remplacer par un drapeau booléen — les appelants ont besoin du jeton, pas
seulement de savoir qu'un appel est parti. Et ne pas « régler » le problème en retirant le
`StrictMode` : il ne faisait que rendre visible une course qui existe aussi en production,
dès que deux requêtes expirent ensemble.


**Un uvicorn mort peut continuer à servir l'ancien code** (trouvé le
05/10/2026, après une heure perdue). Deux sources venaient d'être déclarées
dans `agents_engine.SOURCES`, la base contenait bien les 13 nouvelles fiches,
le module importé en ligne de commande les voyait — et `/api/faq` continuait
de servir l'ancienne liste, y compris après avoir tué le processus et l'avoir
relancé. Cause : le rechargement automatique d'uvicorn (`--reload`) lance un
processus enfant par `multiprocessing`, et cet enfant **survit à la mort de son
parent en gardant le port 8000 ouvert**. Trois sockets étaient en écoute sur
127.0.0.1:8000, dont deux appartenant à des processus disparus ; c'est l'orphelin
qui répondait. Le symptôme est trompeur : tout indique que le changement n'a pas
été pris, alors que c'est le serveur qui n'est pas celui qu'on croit.

Le réflexe : `Get-NetTCPConnection -LocalPort 8000 -State Listen` liste les
propriétaires ; tuer **tous** les processus python dont la ligne de commande
contient `uvicorn` ou `spawn_main`, vérifier que le port est libre, puis
relancer. Un bon contrôle d'identité du serveur : poser une requête et regarder
si elle apparaît dans SON journal — si elle n'y est pas, ce n'est pas lui qui
répond.

Et deux formes plus anciennes, trouvées en deux jours :

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
