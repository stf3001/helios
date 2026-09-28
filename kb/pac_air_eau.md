# Base de connaissances — Pompe à chaleur air/eau : dimensionnement, émetteurs, mise en service (source pac_air_eau)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source pac_air_eau).
# Origine : notes de dimensionnement et synthèses d'un conseiller de terrain (sept. 2026), anonymisées.
# Aucune donnée client, aucun prix d'installateur, aucune marque mise en avant.

---

### Q: Comment dimensionner une pompe à chaleur air/eau à partir de ma facture de gaz ?
`cat: chauffage | tags: pac_air_eau, dimensionnement, sortie_gaz, degres_jours | verif: generique`
R: Partez de 12 mois de relevés de gaz, mois par mois. La consommation d'été (juin à août) représente l'eau chaude et la cuisson. Tout ce qui dépasse ce talon en hiver, c'est le chauffage. On convertit ensuite en chaleur réellement utile : gaz × 0,9 (passage PCS → PCI) × rendement de la chaudière (souvent 0,85 à 0,92). En rapportant cette chaleur aux degrés-jours de votre commune, on obtient ce que perd la maison par degré d'écart, puis la puissance nécessaire au froid de référence (autour de −5 °C en climat méditerranéen). Ordre de grandeur : une maison de 120 m² bien isolée qui brûle 7 000 kWh de gaz par an demande souvent 3 à 4 kW seulement par grand froid. Le calcul « au volume » (volume × coefficient d'isolation × écart de température) sert de plafond de prudence. Demandez toujours à l'installateur sur quoi repose la puissance qu'il propose.

### Q: Trois devis proposent trois puissances différentes pour ma maison : qui croire ?
`cat: chauffage | tags: pac_air_eau, devis, dimensionnement, surdimensionnement | verif: generique`
R: Celui qui justifie sa puissance par votre consommation réelle. Des écarts du simple au double (6, 8 et 10 kW pour la même maison) viennent souvent d'un ratio forfaitaire au m², du type « 70 à 80 W/m² maison ancienne », appliqué à une maison qui est en réalité bien isolée. Trois questions à poser à chaque installateur : d'où vient votre besoin de chauffage (facture, calcul de déperditions, ratio) ? Quelle puissance la machine rend-elle à −7 °C à la température d'eau dont mes radiateurs ont besoin ? Et que se passe-t-il à +7 °C, quand la maison ne demande presque rien ? Une machine trop grosse coûte plus cher, fait plus de bruit, tire plus de courant et s'use plus vite.

### Q: Pourquoi la puissance d'une PAC par temps doux compte-t-elle autant que par grand froid ?
`cat: chauffage | tags: pac, cycles, rendement, surdimensionnement | verif: generique`
R: Parce que l'essentiel de l'hiver se passe par temps doux. Dans le Sud, autour de +7 °C dehors, une maison bien isolée ne demande parfois que 1,5 à 2 kW. Une PAC de 8 ou 10 kW est alors 4 à 6 fois trop puissante : elle s'allume et s'éteint sans cesse (on dit qu'elle « cycle »), perd en rendement et use son compresseur. La bonne machine couvre le jour le plus froid avec un peu de marge, et travaille près de sa puissance réelle le reste de la saison. L'appoint électrique intégré, souvent 3 kW, sert de secours pour les rares journées extrêmes, pas de muscle principal.

### Q: Mes radiateurs actuels suffiront-ils avec une pompe à chaleur ?
`cat: chauffage | tags: pac_air_eau, radiateurs, emetteurs, temperature_depart | verif: generique`
R: Ça se calcule, pièce par pièce. On relève chaque radiateur (type, hauteur, nombre d'éléments) pour connaître sa puissance nominale, donnée pour une eau très chaude (ΔT 50). Puis on regarde ce qu'il rend à plus basse température. Exemple réel : des radiateurs aluminium totalisant environ 10 kW à ΔT 50 ne rendent plus que 2,5 kW avec une eau à 40 °C, mais 4,6 kW à 50 °C et 5,7 kW à 55 °C. Si le besoin au pire jour est de 4 kW, une eau à 50 °C suffit, et 35 à 45 °C la majeure partie de l'hiver. Des radiateurs généreux (beaucoup d'éléments) sont un atout : ils permettent de chauffer plus bas, donc avec un meilleur rendement. Un radiateur rouillé ou fuyard se remplace pendant le chantier, circuit déjà vidangé.

### Q: PAC haute, moyenne ou basse température : laquelle choisir ?
`cat: chauffage | tags: pac_air_eau, haute_temperature, moyenne_temperature, scop | verif: generique`
R: La plus basse qui couvre le jour le plus froid avec vos émetteurs. Une PAC haute température (eau jusqu'à 70-75 °C) remplace une chaudière sans toucher à rien, mais coûte plus cher et consomme davantage. Une moyenne température (jusqu'à 55 °C) suffit très souvent avec des radiateurs récents. Une basse température (35-45 °C) vise le plancher chauffant ou des radiateurs très surdimensionnés. L'écart de rendement est réel : sur une même gamme, le rendement saisonnier (SCOP) tombe d'environ 4,4 avec une eau à 35 °C à environ 3,2 avec une eau à 55 °C. Avant la visite, un conseiller prudent peut annoncer de la haute température faute de connaître les radiateurs. Le relevé des émetteurs permet souvent de redescendre d'un cran, et de payer moins cher.

### Q: Qu'est-ce que la loi d'eau d'une pompe à chaleur, et pourquoi la régler au plus bas ?
`cat: chauffage | tags: pac, loi_d_eau, reglage, mise_en_service | verif: generique`
R: C'est la courbe qui fixe la température de l'eau envoyée dans les radiateurs selon la température extérieure : plus il fait froid dehors, plus l'eau part chaude. Chaque degré d'eau en moins améliore le rendement de la machine. À la mise en service, l'installateur doit régler cette courbe au plus bas possible, puis l'ajuster après quelques semaines selon votre confort réel. Une loi d'eau laissée trop haute fait tourner la machine dans sa zone la moins efficace tout l'hiver : c'est une surconsommation silencieuse, qui ne se voit que sur la facture. Si une pièce reste froide, on regarde d'abord son radiateur et sa tête thermostatique avant de remonter toute la courbe.

### Q: Le désembouage est-il vraiment nécessaire avant de poser une pompe à chaleur ?
`cat: chauffage | tags: pac_air_eau, desembouage, filtre, inhibiteur, garantie | verif: generique`
R: Sur un circuit ancien, oui, et ce n'est pas négociable. Un réseau de radiateurs de 15 ou 20 ans, surtout s'il mélange aluminium et acier, contient forcément des boues. Sans traitement, on les envoie dans l'échangeur de la PAC : colmatage, perte de rendement, et souvent un refus de garantie le jour où il casse. Le trio à exiger : un désembouage complet du circuit, un filtre magnétique (pot à boues) sur le retour de la PAC, et un inhibiteur de corrosion compatible avec vos radiateurs après remplissage. C'est aussi le poste que les devis oublient le plus : demandez qu'il figure en ligne distincte, pour comparer les offres à périmètre égal.

### Q: Que doit contenir un devis de pompe à chaleur air/eau pour être complet ?
`cat: chauffage | tags: pac_air_eau, devis, perimetre, comparaison | verif: generique`
R: Au minimum : la machine fournie et posée (unité extérieure sur support ou dalle avec plots anti-vibratiles, liaisons, évacuation des condensats, sonde extérieure, thermostat d'ambiance) ; la dépose de la chaudière, la neutralisation de l'arrivée de gaz et l'obturation du conduit ; le désembouage, le filtre et l'inhibiteur ; une ligne électrique dédiée avec ses protections ; la mise en service avec réglage de la loi d'eau et programmation de l'eau chaude. Le devis doit aussi dire ce qui est hors prix et chiffré à part si besoin : travaux hydrauliques lourds, renforcement électrique, amiante, levage, pompe de relevage. Sur une PAC, c'est la visite technique qui fige la machine et le prix. Un devis qui affiche un prix ferme sans visite doit vous interroger.

### Q: Des têtes thermostatiques sont-elles utiles avec une pompe à chaleur ?
`cat: chauffage | tags: pac, robinets_thermostatiques, confort, regulation | verif: generique`
R: Oui, c'est le moyen le plus simple d'avoir le confort pièce par pièce sans monter la température de l'eau pour toute la maison : chambres plus fraîches, séjour à 20 °C. On en équipe tous les radiateurs sauf celui de la pièce où se trouve le thermostat d'ambiance, qui doit rester libre pour piloter la machine. Posées pendant le chantier, circuit vidangé, elles coûtent peu. C'est un poste que les devis prévoient rarement : demandez-le si vous voulez plus de confort.

### Q: Pompe à chaleur « chauffage seul » ou « double service » avec l'eau chaude ?
`cat: chauffage | tags: pac_air_eau, ecs, double_service, cumulus | verif: generique`
R: Les deux se défendent, et la présence de panneaux solaires change la réponse. Une PAC double service (ballon intégré) produit l'eau chaude avec environ trois fois moins d'électricité qu'un cumulus : c'est le bon choix quand la chaudière faisait aussi l'eau chaude et qu'il faut la remplacer. Si vous avez déjà un cumulus en bon état et des panneaux, le garder et le piloter sur le soleil est souvent plus malin : c'est le meilleur « radiateur à surplus solaire » qui existe, et la PAC s'occupe seulement de l'hiver. Vérifiez aussi le volume : un ballon de 190 L convient bien à quatre personnes qui se douchent, il est juste pour des bains.

### Q: Faut-il prendre une pompe à chaleur plus puissante pour produire aussi l'eau chaude ?
`cat: chauffage | tags: pac, ecs, dimensionnement | verif: generique`
R: Non. Sur une PAC double service, l'eau chaude est produite en priorité, par cycles courts, idéalement programmés en milieu de journée. Pendant ce temps le chauffage s'arrête, et l'inertie de la maison et des radiateurs absorbe la pause sans que vous la sentiez. On ne rajoute donc pas de kilowatts pour l'eau chaude. Un installateur qui gonfle la puissance « pour l'eau chaude » surdimensionne la machine pour tout le reste de l'année.

### Q: Mon abonnement électrique suffira-t-il après l'installation d'une pompe à chaleur ?
`cat: chauffage | tags: pac, puissance_souscrite, kva, delestage | verif: generique`
R: Souvent oui, à condition d'éviter que tout démarre en même temps. Regardez sur la fiche technique le courant maximal de l'unité extérieure : il peut passer de 13 A pour une machine de 5-6 kW à 18 A pour une 8 kW, plus un appoint électrique de 3 kW. Sur un abonnement de 9 ou 12 kVA qui porte déjà une recharge de voiture, une plaque à induction ou une piscine, on organise les usages : recharge la nuit ou sur les heures solaires, appoint de la PAC délestable. C'est un point à faire vérifier au tableau électrique pendant la visite, avant de signer, plutôt qu'à découvrir le premier soir de grand froid.

### Q: Pourquoi certains devis de pompe à chaleur déduisent des aides et d'autres non ?
`cat: aides | tags: pac_air_eau, maprimerenov, cee, rge, qualipac | verif: aides`
R: MaPrimeRénov' et les primes CEE pour une PAC air/eau exigent que les travaux soient réalisés par une entreprise RGE qualifiée pour ce geste (QualiPAC ou équivalent). Un installateur qualifié en photovoltaïque mais pas en PAC ne peut pas les faire bénéficier. Pour comparer honnêtement : vérifiez la qualification de chaque entreprise sur france-renov.gouv.fr, comparez le reste à charge aides déduites, mais aussi le périmètre (désembouage, filtre, têtes thermostatiques, réglages) et la puissance proposée. Pour un ménage aux revenus modestes, les aides peuvent faire une différence de plusieurs milliers d'euros. Pour un ménage aux revenus élevés, un devis sans aides mais mieux dimensionné peut rester le plus intéressant.

### Q: La TVA à 5,5 % s'applique-t-elle à une pompe à chaleur ?
`cat: aides | tags: tva, pac_air_eau, pac_air_air, attestation | verif: TVA, reglementation`
R: Pour une PAC air/eau, souvent oui, sous conditions : logement achevé depuis plus de deux ans, matériel fourni et posé par la même entreprise, attestation signée par le client, et un équipement qui respecte les seuils de performance (efficacité saisonnière, dite ETAS) fixés par arrêté. Ces seuils ont été modifiés en 2026 : l'installateur doit vérifier la fiche technique de la machine exacte, dans le régime de température prévu. Le taux réduit ne dépend pas du RGE. Pour une PAC air/air (climatisation réversible), le taux de 5,5 % ne s'applique généralement pas : demandez le taux appliqué et sa justification. Sur un devis de 10 000 €, l'écart entre 5,5 % et 20 % dépasse 1 400 €.

### Q: Que faire de mon contrat de gaz après l'installation d'une pompe à chaleur ?
`cat: energie | tags: sortie_gaz, abonnement, induction, resiliation | verif: generique`
R: Si plus rien ne fonctionne au gaz, résiliez-le : plus d'abonnement, plus d'entretien annuel de chaudière, une seule énergie. Si la cuisson reste au gaz, vous continuerez à payer un abonnement pour quelques centaines de kWh par an. Le passage aux plaques à induction referme alors le dossier gaz. Regardez la ligne « abonnement » de votre facture de gaz : c'est de l'argent qui part chaque année sans rien consommer. Le jour du chantier, l'installateur doit neutraliser proprement l'arrivée de gaz en chaufferie et obturer ou déposer le conduit de la chaudière.

### Q: Mes panneaux solaires couvriront-ils la consommation de ma future pompe à chaleur ?
`cat: chauffage | tags: pac, solaire, hiver, consommation, etude | verif: generique`
R: En partie seulement, et il faut le savoir avant de lire une étude. Une PAC consomme environ 70 % de son électricité de novembre à mars, quand les panneaux produisent peu et qu'il n'y a presque plus de surplus. Le solaire couvre donc très bien l'eau chaude et la climatisation d'été, beaucoup moins le chauffage d'hiver. Autre piège : certains logiciels d'étude ajoutent une consommation de PAC forfaitaire et étalée sur l'année. Sur un cas réel, l'étude ajoutait 1 750 kWh, quand le calcul à partir des factures de gaz (plus le passage de la cuisson à l'induction) en donnait 2 560, concentrés l'hiver. Le solaire n'en était pas moins rentable, mais la facture finale était plus haute que prévu. Demandez une projection de la consommation de la PAC mois par mois.
