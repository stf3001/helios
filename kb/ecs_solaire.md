# Base de connaissances — Eau chaude et solaire : cumulus piloté, thermodynamique, arbitrages (source ecs_solaire)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source ecs_solaire).
# Origine : synthèses et notes d'aide à la décision d'un conseiller de terrain (sept. 2026), anonymisées.

---

### Q: Combien consomme vraiment mon eau chaude ?
`cat: ecs | tags: ecs, consommation, cumulus, ademe, mesure | verif: generique`
R: La moyenne ADEME retient environ 850 kWh par personne et par an pour un cumulus électrique, soit 2 500 kWh pour trois personnes. C'est un repère, pas une mesure : les foyers économes sont souvent bien en dessous. Avec une chaudière gaz, votre facture d'été permet de le vérifier : la consommation de juin à août, cuisson déduite, c'est essentiellement l'eau chaude. Attention, elle monte un peu l'hiver, car l'eau froide du réseau arrive vers 11 °C au lieu de 20 °C en août. Mieux vaut dimensionner sur votre mesure que sur une moyenne : un chiffre gonflé fausse la puissance de la PAC, du ballon ou des panneaux.

### Q: J'ai des panneaux solaires : dois-je remplacer mon cumulus par un chauffe-eau thermodynamique ?
`cat: ecs | tags: chauffe_eau_thermodynamique, cumulus, pilotage, solaire | verif: prix`
R: Tant que votre cumulus fonctionne, rarement. Sur le papier, un chauffe-eau thermodynamique consomme trois fois moins. Mais avec des panneaux et un cumulus piloté, une grande partie de votre eau chaude est déjà chauffée gratuitement au soleil : le thermodynamique économise surtout des kWh que vous ne payez plus. Exemple chiffré : pour cinq personnes, il économise 3 000 kWh sur le papier, mais seulement 500 à 1 400 kWh réellement achetés selon la taille de l'installation, soit 100 à 270 € par an, pour environ 3 500 à 6 000 € posé. Il ne se rembourse pas toujours sur sa durée de vie (environ 15 ans). Autre point : un cumulus absorbe beaucoup de puissance d'un coup, idéal pour avaler un pic de production à midi, alors qu'un thermodynamique consomme peu, longtemps, et se cale moins bien sur le soleil.

### Q: Quand le chauffe-eau thermodynamique devient-il un bon choix ?
`cat: ecs | tags: chauffe_eau_thermodynamique, remplacement, garage, calcaire | verif: prix`
R: Le jour où votre cumulus rend l'âme. Tant qu'il marche, on compare 3 500 € à zéro. Quand il faut le changer, on compare 3 500 € au remplacement par un cumulus neuf (800 à 1 200 € posé) : le surcoût réel tombe à 2 300-2 700 €, et le retour à dix ou douze ans. Les bonnes conditions : un local non chauffé ou un garage pour que l'appareil prenne ses calories sans refroidir la maison (ou une version gainée sur l'extérieur), un climat doux qui tient son rendement l'hiver, et une eau peu calcaire (ou un adoucisseur), car le calcaire use l'échangeur. Prévoyez l'entretien régulier. Dans un projet d'autonomie ou sans panneaux, c'est en revanche l'un des meilleurs leviers par euro dépensé.

### Q: Isoler mes combles ou installer un chauffe-eau thermodynamique : que faire en premier ?
`cat: isolation | tags: isolation_combles, chauffe_eau_thermodynamique, arbitrage, solaire | verif: prix`
R: Avec des panneaux solaires, les deux ne se valent pas. L'eau chaude se chauffe en journée, sur votre production : elle ne vous coûte déjà presque plus rien. Le chauffage, lui, tombe l'hiver et le soir, quand les panneaux produisent peu : ces kWh-là s'achètent au réseau, au prix fort. L'isolation des combles attaque donc des kWh chers. Sur un cas réel, les deux rapportaient à peu près autant sur leur durée de vie, mais l'isolation coûtait deux fois moins cher à l'entrée (1 500 à 2 500 € contre 3 500 €), se remboursait plus vite (surtout avec les aides) et améliorait en prime le confort d'été sous le toit. À résultat comparable, on commence par le moins cher et le plus rapide. Comptez une quinzaine d'années d'efficacité pour une laine soufflée, qui se tasse avec le temps.

### Q: Mon chauffe-eau thermodynamique est en panne et chauffe sur sa résistance : faut-il le réparer avant de poser des panneaux ?
`cat: ecs | tags: chauffe_eau_thermodynamique, panne, resistance, pilotage | verif: generique`
R: Pas forcément en priorité. En panne, il consomme comme un cumulus classique, environ trois fois plus qu'en état de marche. Mais une fois les panneaux posés et le chauffe-eau piloté sur les heures de soleil, les kWh que la réparation ferait économiser seraient de toute façon en grande partie solaires : le gain financier devient faible. Mettez d'abord en place le pilotage, qui ne coûte presque rien. La remise en état peut suivre si elle reste raisonnable, ou attendre la fin de vie de l'appareil.

### Q: Comment estimer ce que rapporte le pilotage du chauffe-eau sur mes panneaux ?
`cat: ecs | tags: pilotage, chauffe_eau, surplus, calcul | verif: tarifs`
R: Un calcul simple. Prenez la consommation annuelle d'eau chaude (par exemple 2 600 kWh pour trois personnes). Chaque kWh chauffé au soleil au lieu de la nuit vaut la différence entre le prix du kWh acheté (environ 0,20 €) et ce que vous aurait rapporté ce surplus (environ 0,01 € s'il était revendu) : environ 0,19 €. Le plafond théorique est donc d'environ 490 € par an. On n'en capte qu'une partie, 50 à 70 % : l'hiver, il reste peu de surplus, alors qu'au printemps et en été il déborde largement. Si vous avez une batterie virtuelle, le gain du pilotage est plus faible, car le surplus n'était pas bradé : il était déjà restitué.

### Q: Pourquoi l'eau chaude pèse-t-elle autant dans un projet d'autonomie totale ?
`cat: ecs | tags: autonomie, batterie, cumulus, hors_reseau | verif: generique`
R: Parce qu'elle consomme tous les jours, hiver compris. Un ballon électrique à résistance, c'est environ 850 kWh par personne et par an, soit 4 à 5 kWh par jour pour deux personnes : les trois quarts d'une batterie de 7 kWh, avant même d'avoir allumé une lampe. Deux leviers : le faire chauffer en plein midi plutôt que la nuit, automatiquement, grâce à un interrupteur piloté, ce qui peut à lui seul faire basculer la réponse. Puis, quand le ballon sera à changer, passer à un chauffe-eau thermodynamique, qui consomme environ trois fois moins.
