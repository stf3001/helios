# Base de connaissances — Conseils de terrain (source terrain)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source terrain).
# Origine : synthèses clients d'un conseiller de terrain (sept. 2026), anonymisées. v2 : 3 fiches déplacées vers pac_air_eau.
# Règle de rédaction : aucune donnée client, aucun prix d'installateur, aucune marque mise en avant.
# On garde le raisonnement, les ordres de grandeur et la manière d'expliquer.

---

## 1. Comprendre sa situation avant de choisir

### Q: Pourquoi partir de mon relevé Linky plutôt que d'une estimation ?
`cat: photovoltaique | tags: linky, enedis, consommation, etude | verif: generique`
R: Parce que votre compteur ne se trompe pas : 12 mois de relevé disent exactement combien vous consommez, et à quelles heures. Une étude sérieuse « rejoue » votre dernière année avec des panneaux sur le toit : mêmes habitudes, mêmes horaires. Ce n'est pas une projection optimiste, c'est un rétro-calcul. Ce que le relevé ne dit pas, c'est ce qui compose la consommation (chauffe-eau, piscine, chauffage, voiture) : c'est ce qu'il faut préciser, car c'est ce qu'on pourra décaler en plein soleil. Si vous avez emménagé depuis moins d'un an, l'hiver manque : mieux vaut alors retenir une hypothèse basse, pour ne rien se promettre de trop.

### Q: Mes économies sont-elles calculées « sans rien changer » à mes habitudes ?
`cat: photovoltaique | tags: autoconsommation, habitudes, pilotage | verif: generique`
R: C'est la bonne façon de les calculer. Un chiffrage honnête reprend vos habitudes actuelles, y compris le chauffe-eau qui chauffe la nuit. Tout ce que vous déciderez ensuite de faire tourner en journée (chauffe-eau, machines, climatisation l'été, filtration de piscine, recharge de voiture) viendra en plus. Méfiez-vous d'une étude qui suppose d'emblée que vous allez tout changer.

### Q: Pourquoi la puissance des panneaux se décide-t-elle dès le départ ?
`cat: photovoltaique | tags: dimensionnement, puissance, evolution | verif: generique`
R: Parce qu'une toiture, c'est une fois. Rajouter des panneaux plus tard, c'est remobiliser une équipe, remonter sur le toit, refaire un dossier en mairie et repasser par le raccordement. Posez-vous donc la question maintenant : véhicule électrique, pompe à chaleur ou climatisation dans les années qui viennent ? Un projet de ce type change la bonne puissance. À l'inverse, une batterie s'ajoute facilement après coup sur la plupart des installations : ce choix-là peut attendre.

### Q: L'étude solaire tient-elle compte des arbres autour de ma maison ?
`cat: photovoltaique | tags: ombrage, masque, visite_technique | verif: generique`
R: Souvent non : les logiciels d'étude modélisent les bâtiments et le relief, rarement la végétation. Sur un terrain arboré, la production réelle peut être plus faible que prévu. Un installateur sérieux fait un relevé du masque solaire sur place, avec un appareil qui mesure l'ombre réelle mois par mois, arbres compris. Demandez-le avant de valider une puissance.

### Q: Des panneaux orientés est et ouest, c'est un mauvais choix ?
`cat: photovoltaique | tags: orientation, est_ouest, production | verif: generique`
R: Pas forcément, c'est même souvent un atout pour l'autoconsommation. Le plein sud produit le plus, mais surtout autour de midi. L'est prend le soleil du matin, l'ouest celui de la fin d'après-midi : la production s'étale sur la journée, là où vous consommez. Sur plusieurs orientations, préférez une technologie où chaque panneau (ou paire de panneaux) travaille indépendamment, comme les micro-onduleurs ou les optimiseurs, pour qu'un pan à l'ombre ne pénalise pas les autres.

## 2. Que faire du surplus solaire

### Q: Que devient la production solaire que je n'utilise pas sur le moment ?
`cat: stockage | tags: surplus, autoconsommation, rachat | verif: tarifs`
R: Tout l'enjeu est là. Les panneaux produisent surtout entre 10 h et 17 h, et une maison consomme surtout le matin et le soir. Sans stockage ni pilotage, la production de midi part sur le réseau, rachetée environ 1 centime le kWh, alors que vous rachetez le vôtre près de vingt fois plus cher le soir. Selon les foyers, c'est la moitié de la production, parfois plus. Trois réponses possibles : décaler vos usages en journée (gratuit), une batterie physique chez vous, ou une réserve (batterie) virtuelle chez un fournisseur.

### Q: Batterie physique, batterie virtuelle ou rien : comment comparer ?
`cat: stockage | tags: batterie, batterie_virtuelle, comparaison, arbitrage | verif: prix, tarifs`
R: Comparez les trois sur votre consommation réelle, à même toit. **Sans stockage** : le moins cher à l'achat, vous gardez votre fournisseur et votre contrat, mais une grande part de la production part à 1 centime. **Batterie physique** : elle vous appartient, sans abonnement ni changement de fournisseur, mais sa capacité est vite saturée dès le printemps (quelques kWh), elle perd environ 10 % à chaque cycle, et elle coûte souvent 4 000 à 8 000 € de plus. **Batterie virtuelle** : un réservoir bien plus grand, sans pertes, pour un surcoût faible à l'installation, mais il faut changer de fournisseur et payer un forfait mensuel. Aucune n'est bonne dans l'absolu : le budget, vos projets et votre attachement à votre contrat actuel tranchent.

### Q: Une batterie virtuelle, concrètement, comment ça marche ?
`cat: stockage | tags: batterie_virtuelle, fonctionnement, fournisseur | verif: tarifs, partenaire`
R: L'image la plus juste, c'est un compte en banque pour vos kilowattheures. Ce que vos panneaux produisent en trop à midi est porté à votre crédit, et vous le reprenez le soir. Physiquement, rien n'est stocké chez vous : l'électricité passe sur le réseau, et c'est votre fournisseur qui tient le compte. C'est pour cela qu'il faut souscrire chez lui. Vous changez de fournisseur, pas de réseau : même compteur Linky, mêmes câbles. Les formules varient selon les offres (capacité souscrite et forfait mensuel, ou abonnement plus frais à chaque restitution). Lisez bien ce que coûte un kWh repris et ce qui arrive quand la réserve est pleine.

### Q: Une batterie, physique ou virtuelle, garde-t-elle le soleil de l'été pour l'hiver ?
`cat: stockage | tags: batterie, saisonnalite, hiver, limites | verif: generique`
R: Non, et il vaut mieux le savoir avant d'acheter. Un stockage travaille sur quelques heures ou quelques jours : la production de midi est reprise le soir même ou le lendemain. L'hiver, les panneaux produisent peu et presque tout est consommé en direct : il reste peu de surplus à stocker. Ce qu'on achète encore au réseau dans l'année, ce sont surtout les nuits d'hiver. Les différences entre stockages tiennent à la taille du réservoir, aux pertes, à la TVA et au contrat d'électricité, pas à une capacité de report d'une saison à l'autre.

### Q: Une réserve virtuelle, comment la dimensionner ?
`cat: stockage | tags: batterie_virtuelle, capacite, dimensionnement | verif: tarifs`
R: Quand la formule repose sur une capacité souscrite (par exemple 20 ou 100 kWh), c'est le plafond de ce que votre compte peut garder d'avance. Ce qui déborde d'une réserve pleine repart sur le réseau sans contrepartie. D'où la règle : partir assez large la première année, puis ajuster sur les mesures réelles. Vérifiez qu'on peut changer de capacité en cours de route, et à quel prix.

### Q: Si je prends une batterie virtuelle, suis-je engagé chez ce fournisseur ?
`cat: stockage | tags: batterie_virtuelle, engagement, contrat, tempo | verif: partenaire`
R: Vérifiez-le offre par offre, mais les offres grand public sont en général sans durée d'engagement : on peut repartir comme on change d'opérateur téléphonique, et les panneaux restent à vous. Ce que vous quittez, c'est votre contrat actuel. Si vous êtes en Tempo, vous perdez les jours bleus bon marché, mais aussi les jours rouges chers en hiver, souvent quand la pompe à chaleur tourne. Faites chiffrer ce changement de contrat séparément, et revoyez-le au bout d'un an, chiffres en main.

### Q: Pourquoi la TVA change-t-elle quand on ajoute une batterie physique ?
`cat: aides | tags: tva, batterie, photovoltaique, devis | verif: TVA, reglementation`
R: La TVA réduite à 5,5 % sur le photovoltaïque vise les petites installations (jusqu'à 9 kWc) qui respectent certaines conditions, dont un système de pilotage. Une batterie physique n'est jamais éligible au taux réduit : si elle figure dans le même devis, tout le devis bascule à 20 %, panneaux compris. Le vrai coût d'une batterie, c'est donc son prix plus la différence de TVA sur le reste, souvent 1 000 à 1 700 € de plus sur une installation de 6 à 7 kWc. Demandez à l'installateur le taux appliqué et pourquoi. Une attestation est à signer pour bénéficier du taux réduit.

## 3. Pilotage : les économies sans rien acheter

### Q: Pourquoi le chauffe-eau est-il le meilleur « stockage » d'une maison solaire ?
`cat: ecs | tags: chauffe_eau, pilotage, surplus, cumulus | verif: generique`
R: Parce qu'il chauffe quand on lui dit et qu'il garde la chaleur. Un foyer de trois personnes consomme de l'ordre de 2 500 kWh par an pour l'eau chaude (ordre de grandeur ADEME). Aujourd'hui, le cumulus chauffe souvent la nuit en heures creuses. Piloté, il chauffe sur le surplus de midi, qui sinon partirait à un centime. Comptez que seule une partie du gain théorique est réellement captée (50 à 70 %) : l'hiver, il reste peu de surplus. C'est souvent la première chose à mettre en place, avant toute batterie.

### Q: Quels usages décaler en journée quand on a des panneaux ?
`cat: sobriete | tags: pilotage, usages, piscine, recharge, climatisation | verif: generique`
R: Par ordre d'impact habituel : le chauffe-eau (piloté automatiquement), la filtration de piscine, la recharge du véhicule, la climatisation l'été, le chauffage l'hiver, puis les machines. La **piscine** filtre souvent la nuit par habitude d'heures creuses : en plein midi, elle ne coûte plus rien, et c'est là que l'eau en a le plus besoin. La **voiture** : le week-end, c'est immédiat. En semaine, tout dépend des trajets. La **climatisation** : la lancer en début d'après-midi plutôt qu'en soirée, c'est rouler au soleil. Le **chauffage** : faire monter la maison d'un degré entre 11 h et 15 h plutôt que le soir. Les **machines** : départ différé en fin de matinée.

### Q: Pourquoi climatisation et panneaux solaires vont-ils bien ensemble ?
`cat: photovoltaique | tags: climatisation, pac_air_air, autoconsommation, ete | verif: generique`
R: Parce que les besoins de rafraîchissement tombent pile aux heures où les panneaux produisent le plus. Une bonne part de la consommation de la clim est donc couverte directement par le toit. C'est un argument pour une PAC air/air réversible quand on a (ou prévoit) du solaire, à condition d'avoir d'abord travaillé les protections solaires (volets, stores extérieurs) : la clim reste le dernier recours pour le confort d'été.

## 4. Sortir du gaz

### Q: Avec une pompe à chaleur, ma consommation d'électricité va augmenter : est-ce normal ?
`cat: chauffage | tags: pac, sortie_gaz, consommation, cop | verif: generique`
R: Oui, et c'est voulu. La pompe à chaleur reprend le travail du gaz en consommant environ 3 à 4 fois moins d'énergie pour le même confort, parce qu'elle puise l'essentiel de sa chaleur dans l'air extérieur. Ordre de grandeur : 7 000 kWh de gaz remplacés par 1 700 à 2 300 kWh d'électricité. Votre facture d'électricité monte, celle du gaz disparaît, abonnement et entretien de chaudière compris. Et une consommation électrique, contrairement au gaz, votre toit peut la couvrir : c'est pour cela que PAC et solaire se pensent ensemble.

### Q: Chaudière déposée : comment produire l'eau chaude ensuite ?
`cat: ecs | tags: sortie_gaz, pac_double_service, cumulus, thermodynamique | verif: generique`
R: Deux options principales. Un **cumulus électrique** classique : simple et peu cher, mais pour quatre personnes il consomme de l'ordre de 3 000 à 3 500 kWh par an selon la moyenne ADEME (souvent moins chez un foyer économe : mesurez-le sur votre facture d'été). Une **pompe à chaleur double service** (ballon intégré) ou un **chauffe-eau thermodynamique** : environ trois fois moins d'électricité pour la même eau chaude. Si le toit est déjà très sollicité l'hiver, le kWh qu'on n'a pas besoin de consommer est le meilleur qui soit. Dans tous les cas, faites programmer la chauffe en milieu de journée si vous avez des panneaux. Vérifiez aussi le volume du ballon selon vos habitudes (douches ou bains).

### Q: Une climatisation ou une pompe à chaleur air/air, c'est bruyant ?
`cat: chauffage | tags: bruit, pac_air_air, voisinage, climatisation | verif: generique`
R: C'est la question la plus fréquente, et elle est légitime. Repères : une unité murale en mode silence tourne autour de 20 dB (un chuchotement), une unité extérieure autour de 45-50 dB à 1 mètre (entre un réfrigérateur et une conversation). Le niveau baisse d'environ 6 dB chaque fois qu'on double la distance. Avec la technologie Inverter, le compresseur module sa vitesse et tourne la plupart du temps au ralenti. Le plus important reste l'emplacement : unités extérieures à l'écart des fenêtres de chambre, les vôtres comme celles des voisins, sur des supports adaptés.

## 5. Lire une offre et choisir un installateur

### Q: Comment lire une étude solaire avec plusieurs configurations ?
`cat: photovoltaique | tags: etude, comparaison, autoconsommation, autonomie | verif: generique`
R: Quatre chiffres suffisent. L'**autoconsommation** : la part de votre production utilisée chez vous. L'**autonomie** : la part de vos besoins couverte par le solaire. La **facture restante** par mois, abonnement et forfaits compris. L'**économie nette** sur la durée, investissement déduit. Ne vous fiez pas à un seul : une grosse installation sans stockage a une bonne autonomie mais une autoconsommation faible. Vérifiez l'hypothèse de hausse de l'électricité retenue (souvent 4 % par an) et demandez la facture ligne par ligne : c'est la mécanique qui compte, pas le chiffre final.

### Q: Pourquoi une garantie « pièces, main-d'œuvre et déplacement » compte-t-elle autant ?
`cat: chantier | tags: garantie, onduleur, sav, installateur | verif: generique`
R: Parce que la plupart des garanties couvrent la pièce seule. Le jour où un onduleur lâche, vous recevez l'appareil, mais vous payez l'intervention, le déplacement, parfois la nacelle. Lisez ce que couvre chaque garantie (produit, rendement, main-d'œuvre) et pour combien d'années. Et souvenez-vous qu'une garantie main-d'œuvre ne vaut que si l'installateur existe encore et vient : la proximité et l'ancienneté de l'entreprise comptent.

### Q: Quelles questions poser à un installateur de panneaux solaires ?
`cat: chantier | tags: installateur, decennale, rge, visite_technique | verif: generique`
R: Demandez son attestation d'assurance décennale à jour, et vérifiez qu'elle couvre bien l'activité photovoltaïque : c'est elle qui vous protège pendant dix ans. Vérifiez la qualification RGE (sur france-renov.gouv.fr). Demandez qui vient poser : ses propres équipes ou un sous-traitant ? Demandez s'il vérifie le tableau électrique et la prise de terre avant la pose : des panneaux, c'est une installation électrique pour trente à quarante ans, raccordée à votre tableau. Enfin, demandez s'il gère la mairie, Enedis et le Consuel, et s'il prévoit des visites de suivi.

### Q: Comment se déroule un projet solaire, de la signature à la mise en service ?
`cat: chantier | tags: etapes, mairie, enedis, consuel, delais | verif: calendrier`
R: En général : une visite (toit, ombrages, tableau électrique, vos habitudes), puis le devis définitif avec l'emplacement exact de chaque panneau. Viennent ensuite la déclaration préalable en mairie (environ un mois d'instruction), une visite technique (charpente, électricité), la pose (souvent 1 à 3 mois après signature), puis le raccordement Enedis, le Consuel et la mise en service. Vérifiez qu'en cas de refus de la mairie ou d'obstacle technique, rien ne vous est facturé. Le délai de rétractation de 14 jours s'applique aux contrats signés hors établissement.
