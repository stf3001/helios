# Base de connaissances — Stockage, contrats de rachat et secours (source stockage_contrats)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source stockage_contrats).
# Origine : notes et synthèses d'un conseiller de terrain (août-sept. 2026), anonymisées.
# Complète les fiches existantes sur batterie physique / virtuelle (faq_maison, autoconso, solutions) sans les répéter.

---

### Q: J'ai déjà des panneaux avec un contrat de rachat EDF OA : ai-je intérêt à passer à une batterie virtuelle ?
`cat: stockage | tags: batterie_virtuelle, edf_oa, contrat_rachat, installation_existante | verif: tarifs`
R: Pas toujours, et souvent non. Une batterie virtuelle ne peut pas coexister avec un contrat de vente du surplus : il faut résilier le contrat OA, définitivement. Or les contrats signés il y a quelques années rachètent le surplus autour de 10 centimes le kWh, contre environ 1 centime pour un raccordement neuf depuis juin 2026 : c'est un contrat qui ne se signe plus. Le calcul dépend du volume de surplus. Exemple réel : une installation de 6 kWc qui autoconsommait déjà 41 % n'aurait gagné qu'environ 66 € par an en passant au virtuel, abonnements déduits, pour 3 000 à 4 500 € de coffret et de frais de sortie. À l'inverse, un gros consommateur qui renvoyait les deux tiers de sa production au réseau pouvait tout rembourser en 5 à 8 ans. Faites chiffrer votre cas précis avant de toucher au contrat.

### Q: Comment résilier un contrat d'obligation d'achat EDF OA, et combien ça coûte ?
`cat: stockage | tags: edf_oa, resiliation, indemnite, prime_autoconsommation | verif: tarifs, reglementation`
R: Par lettre recommandée avec accusé de réception à votre agence Obligation d'Achat (références du contrat et du raccordement, adresse, motif, date souhaitée), avec un préavis de 3 mois minimum. Toutes les factures de vente doivent être régularisées avant la date d'effet. Deux coûts à faire chiffrer d'abord, gratuitement, auprès d'EDF OA : l'indemnité de résiliation anticipée (EDF OA cite environ 500 € pour 3 kWc au bout d'un an et demi, environ 3 500 € pour 9 kWc au bout de 7 ans) et le remboursement éventuel, total ou partiel, de la prime à l'autoconsommation perçue à la mise en service. La résiliation est définitive : le contrat ne sera ni reconduit ni remplacé. Votre raccordement reste en place, vous injectez toujours, simplement vous ne vendez plus. Référence : edf-oa.fr, rubrique « résilier son contrat ».

### Q: Puis-je ajouter une batterie physique à une installation existante et garder mon contrat de rachat ?
`cat: stockage | tags: batterie_physique, installation_existante, couplage_ac, edf_oa | verif: TVA`
R: Oui. Une batterie en couplage AC se raccorde côté courant alternatif, sans remplacer l'onduleur existant, et votre contrat de revente reste en place : ce que la batterie ne peut plus absorber continue d'être vendu. Elle récupère l'écart entre le prix du kWh racheté le soir (environ 20 centimes) et celui auquel vous vendiez votre surplus. Elle apporte aussi, avec l'option adaptée, un secours en cas de coupure. En contrepartie : TVA à 20 %, capacité limitée (vite pleine les belles journées), environ 10 % de pertes par cycle. À comparer avec la solution virtuelle, moins chère à l'installation mais qui impose de résilier le contrat de rachat et d'ajouter un abonnement.

### Q: Batterie virtuelle : quelles sont les différentes formules, et que vérifier ?
`cat: stockage | tags: batterie_virtuelle, formules, abonnement, restitution | verif: tarifs, partenaire`
R: On trouve deux logiques. Dans la première, on paie un abonnement lié à la puissance installée, puis l'acheminement et les taxes sur chaque kWh repris (de l'ordre de 10 centimes) : reprendre ses kWh n'est pas gratuit. Dans la seconde, on souscrit une capacité (par exemple 20 ou 100 kWh) contre un forfait mensuel fixe, et chaque kWh confié est rendu un pour un. Certaines offres convertissent aussi en euros le surplus qui déborde d'une réserve pleine (« cagnottage »). Dans tous les cas : il faut changer de fournisseur d'électricité, l'abonnement est souvent un peu plus cher, et c'est un service, pas un équipement. Lisez le coût réel d'un kWh repris, le sort de ce qui déborde, et la règle d'indexation du prix.

### Q: Batterie virtuelle : faut-il prendre la plus grande capacité possible ?
`cat: stockage | tags: batterie_virtuelle, capacite, dimensionnement, autonomie | verif: tarifs`
R: Non : une plus grande capacité coûte plus cher chaque mois, et ne rapporte que si elle se remplit. Exemple réel : sur une petite maison très autonome, passer d'une réserve de 20 kWh à une réserve étendue faisait grimper l'autonomie de 93 % à 100 %, mais les 277 kWh encore achetés au réseau ne valaient que 55 € par an, pour 108 € d'abonnement supplémentaire. On aurait payé 108 € pour en économiser 55. À l'inverse, une réserve trop petite déborde et le surplus part sans contrepartie. La bonne méthode : partir sur la capacité que la simulation désigne comme la plus rentable, puis l'ajuster au bout d'un an sur les mesures réelles, si le contrat le permet dans les deux sens.

### Q: Et si l'opérateur de ma batterie virtuelle disparaît, ou si je veux en partir ?
`cat: stockage | tags: batterie_virtuelle, risque, resiliation, fournisseur | verif: partenaire`
R: C'est la bonne question à poser. Une batterie virtuelle n'est pas un équipement, c'est un service adossé à un contrat de fourniture d'électricité. Vous n'y immobilisez donc aucun capital : si vous y renoncez, vous changez de fournisseur, et vos panneaux continuent de produire et d'alimenter la maison exactement pareil. Vous perdez le mécanisme de stockage, pas la centrale. Trois points à faire préciser par écrit avant de signer : les conditions de sortie (un contrat de fourniture est en principe résiliable sans frais), le sort du crédit de kWh non consommé (il n'est généralement pas remboursé en euros), et la règle d'évolution du prix du kWh.

### Q: Après l'installation de panneaux, faut-il garder l'option heures creuses ?
`cat: achat_energie | tags: heures_creuses, tarif_base, tempo, stockage | verif: tarifs`
R: Ça dépend du stockage. Avec une batterie virtuelle, on passe généralement en tarif base : la production restituée couvre la soirée, et la distinction jour/nuit perd son intérêt. Avec une batterie physique ou sans stockage, gardez vos heures creuses au moins la première année, puis refaites le calcul sur vos relevés réels : une partie de ce qui chauffait la nuit (chauffe-eau, machines) sera passée en journée sur le soleil. Si vous êtes en Tempo, faites chiffrer à part ce que vous perdez (les jours bleus bon marché) et ce que vous gagnez (plus de jours rouges chers l'hiver).

### Q: Rester chez son fournisseur historique avec une batterie physique, ou passer au virtuel : comment comparer ?
`cat: stockage | tags: batterie_physique, batterie_virtuelle, comparaison, surplus | verif: tarifs`
R: Regardez ce qui repart au réseau. Exemple réel : avec deux batteries physiques de 7 kWh et sans stockage virtuel, 4 400 kWh de production partaient encore au réseau chaque année. Rachetés au tarif du contrat, ils rapportaient 49 € ; consommés, ils auraient évité 879 € d'achats. Avec une réserve virtuelle en plus, il n'en restait que 860. C'est tout l'écart entre les deux solutions : elles se valent quand le surplus est faible, et le virtuel creuse l'écart dès que le surplus est important (belles journées, grosse installation, maison vide en journée). À l'inverse, la batterie physique garde deux avantages : aucun abonnement, et le secours en cas de coupure.

### Q: Une deuxième batterie physique vaut-elle le coup ?
`cat: stockage | tags: batterie_physique, capacite, rentabilite, secours | verif: prix`
R: Rarement pour l'argent. Quand la première batterie, ou une réserve virtuelle, absorbe déjà l'essentiel, la deuxième n'a plus grand-chose à stocker. Exemple réel : une batterie supplémentaire de 7 kWh à 3 600 € ne faisait gagner que 130 € par an, soit 19 à 28 ans de retour pour une garantie de 15 ans. Le facteur limitant n'était plus la capacité de stockage, c'était la production. Elle se défend en revanche pour le secours, si les coupures sont longues et fréquentes chez vous. La bonne question n'est pas « combien de kWh ai-je ? », mais « combien de coupures ai-je eues l'an dernier, et combien de temps ont-elles duré ? ».

### Q: Mes panneaux fonctionnent-ils pendant une coupure de courant ?
`cat: stockage | tags: coupure, secours, backup, ilotage | verif: generique`
R: Non, sauf équipement spécifique. Une installation raccordée au réseau s'arrête automatiquement en cas de coupure, même en plein soleil : c'est une obligation de sécurité pour protéger les techniciens qui interviennent sur la ligne. Une batterie virtuelle ne change rien, elle s'arrête avec le réseau. Pour garder du courant, il faut une batterie physique avec une fonction de secours (back-up) : la maison bascule automatiquement sur la batterie, et avec certains systèmes les panneaux continuent de la recharger en journée. Le schéma de raccordement (circuit secouru ou maison entière) se décide en visite technique.

### Q: Une batterie de secours tient combien de temps pendant une coupure ?
`cat: stockage | tags: secours, backup, autonomie, coupure | verif: generique`
R: Tout dépend de ce qui reste allumé. Sans chauffage électrique, les usages essentiels (réfrigérateur, congélateur, éclairage, box, quelques prises, circulateur) représentent 3 à 5 kWh par jour, une fois le chauffe-eau et la recharge de voiture coupés. Une batterie de 7 kWh tient alors un jour et demi à deux jours, 14 kWh trois à quatre jours. Et si le système permet aux panneaux de la recharger pendant la coupure, même une journée d'hiver couverte rend souvent 8 à 15 kWh : la batterie ne se vide pas, elle se remplit chaque matin. Un chauffage au bois change tout : c'est le chauffage électrique qui vide une batterie en hiver. Le secours est un argument de confort, pas de rentabilité.

### Q: Pour le secours, quelle puissance de batterie faut-il regarder ?
`cat: stockage | tags: secours, puissance, kw, demarrage | verif: generique`
R: Deux chiffres, et pas seulement la capacité en kWh : la puissance continue que la batterie peut fournir en secours (par exemple 4,5 kW pour un module de 7 kWh, 9 à 11 kW pour les plus gros systèmes) et la pointe au démarrage d'un moteur. Pour une maison chauffée au bois, 4,5 kW couvrent largement une coupure, pompe de piscine comprise (généralement moins de 1 kW). Une puissance plus élevée n'est vraiment utile que pour faire tourner en même temps plusieurs gros appareils pendant la coupure : climatisation, plaques, recharge de voiture, pompe à chaleur.

### Q: Batterie avec onduleur intégré ou batterie en couplage AC : quelle différence ?
`cat: stockage | tags: batterie_physique, couplage_ac, onduleur_integre, architecture | verif: generique`
R: Deux architectures. Une batterie à onduleur intégré réunit stockage et conversion dans un seul boîtier : installation compacte, souvent une forte puissance de secours, mais l'électronique de conversion est garantie comme la batterie (souvent 10 ans). Une batterie en couplage AC se raccorde sur une installation qui a déjà ses propres onduleurs ou micro-onduleurs : on peut l'ajouter plus tard sans rien démonter, et l'étendre par modules. Comparez à même capacité : prix installé, garantie de la batterie (10 ou 15 ans, et la capacité garantie à l'échéance), nombre de cycles annoncé, puissance de secours, et garantie de l'électronique. Sur un cas réel, deux systèmes de 13,5 et 14 kWh différaient de 3 500 € et de 5 ans de garantie.

### Q: Une batterie physique fait-elle vraiment un cycle par jour ?
`cat: stockage | tags: batterie_physique, cycles, garantie, rentabilite | verif: generique`
R: Non. En pratique, une batterie domestique fait plutôt 250 à 300 cycles utiles par an : les jours peu ensoleillés, il n'y a pas assez de surplus pour la remplir. C'est un point clé pour juger sa rentabilité : un retour sur investissement de 12 ans sur une batterie garantie 10 ans n'est pas un bon calcul, alors que 10 ans sur une garantie de 15 ans laisse de la marge. Demandez toujours les deux chiffres côte à côte.
