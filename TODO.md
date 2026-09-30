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
