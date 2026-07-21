# Base de connaissances — Revolt : simulateur PV + batterie + tarifs (source revolt)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source revolt).

### Q: C'est quoi le simulateur Revolt d'Helios ?
`cat:revolt | tags:revolt,simulateur,pv,batterie,tarif | verif:generique`
R: Revolt compare, à consommation réelle égale, plusieurs façons de gérer l'électricité de votre logement : ajouter des panneaux solaires seuls, y ajouter une batterie physique, passer en stockage virtuel (MyLight), et/ou changer de tarif (fixe, SOBRY SoFlex ou SoCap). Contrairement au simulateur solaire classique qui raisonne en moyennes annuelles, Revolt simule heure par heure sur une année complète pour donner un résultat plus fin — toujours en ordres de grandeur, jamais en promesse.

### Q: D'où vient ma courbe de consommation dans le simulateur Revolt ?
`cat:revolt | tags:enedis,linky,courbe,consentement | verif:generique`
R: Deux sources possibles. Aujourd'hui, une courbe horaire SIMULÉE à partir de votre profil déclaré (type de chauffage, nombre d'occupants, consommation annuelle) — clairement indiquée comme telle, ce n'est pas une mesure. À terme, Helios pourra se connecter à Enedis DataConnect pour récupérer votre vraie courbe de charge Linky, avec votre consentement explicite — cette connexion nécessite une inscription partenaire encore en cours côté Helios.

### Q: Qu'est-ce que l'offre SOBRY SoFlex ?
`cat:revolt | tags:sobry,soflex,tarif_dynamique | verif:partenaire`
R: SoFlex est une offre à tarif entièrement dynamique : le prix du kWh suit le marché de gros heure par heure, sans plafond. Il peut descendre en dessous de zéro (environ 1000 heures par an à prix négatif, surtout au printemps/été en milieu de journée quand le solaire national produit beaucoup) et monter jusqu'à environ 0,38 €/kWh aux heures de pointe hiver. C'est intéressant si vous pouvez déplacer votre consommation vers les heures creuses (véhicule électrique, ballon d'eau chaude, PAC pilotée) ; risqué sinon.

### Q: Qu'est-ce que l'offre SOBRY SoCap ?
`cat:revolt | tags:sobry,socap,tarif_dynamique | verif:partenaire`
R: SoCap suit la même logique de marché que SoFlex, mais plafonnée dans les deux sens : jamais de prix négatif (le creux solaire du milieu de journée descend au minimum à 0 €/kWh), et jamais au-dessus d'environ 0,25 €/kWh en pointe. C'est un compromis entre le tarif fixe classique et la liberté totale de SoFlex — moins de risque à la hausse, mais aussi moins d'opportunité aux heures à prix négatif.

### Q: Qu'est-ce que la batterie virtuelle MyLight ?
`cat:revolt | tags:mylight,batterie_virtuelle,partenaire | verif:partenaire`
R: MyLight (offre MyBattery) permet de « mettre de côté » tout le surplus solaire non consommé, sans limite de volume ni de durée, pour le récupérer plus tard au prix coûtant. Concrètement : environ 179 € de frais d'activation, un abonnement d'environ 1,20 €/kWc installé par mois, et des frais de restitution d'environ 0,08 €/kWh (TURPE + accise) à chaque récupération. Contrainte importante : cela impose de souscrire l'électricité chez mylight150, leur fournisseur — à mettre en balance avec votre offre actuelle. Tarifs 2026 publics, à confirmer auprès de MyLight avant toute décision.

### Q: Le simulateur Revolt garde-t-il mes résultats ?
`cat:revolt | tags:historique,espace_client,gratuit | verif:generique`
R: Oui. Chaque simulation Revolt est conservée automatiquement et gratuitement dans votre espace client — vous n'avez rien à faire pour ça. Vous retrouvez l'historique de vos comparaisons sur la page du simulateur, et Helios peut s'appuyer sur votre dernière simulation quand vous lui posez une question, pour vous répondre avec vos propres chiffres plutôt qu'une estimation générique.

### Q: Dois-je forcément ajouter une batterie si je fais du solaire ?
`cat:revolt | tags:batterie,arbitrage,pilotage | verif:generique`
R: Non, et Revolt sert justement à vérifier ce qui est pertinent dans VOTRE cas. Une batterie physique augmente l'autoconsommation mais coûte cher et met du temps à s'amortir. Le stockage virtuel MyLight évite l'investissement mais impose de changer de fournisseur et facture la restitution. Souvent, le pilotage intelligent des usages (déplacer le lave-linge, la recharge, le ballon vers les heures de production) apporte un gain important sans rien acheter — à tester en premier avec Revolt avant d'investir.
