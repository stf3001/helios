# Base de connaissances — Fin de contrat de rachat et ajout de puissance (source fin_contrat_rachat)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source fin_contrat_rachat).
# Origine : synthèse client d'un conseiller de terrain (septembre 2026), anonymisée.
# Règle de rédaction : aucune donnée client, aucun prix d'installateur, aucune marque mise en avant.
# Sources citées dans le document d'origine : arrêté du 1er juin 2026 modifiant l'arrêté du
# 6 octobre 2021 (publié au JO le 4 juin, applicable depuis le 5 juin) ; Enedis, « Mon contrat
# d'obligation d'achat prend fin ».

---

## 1. La fin d'un contrat de vente totale

### Q: Mon contrat de vente totale arrive à son terme : que se passe-t-il ?
`cat: photovoltaique | tags: vente_totale, edf_oa, fin_contrat, echeance | verif: reglementation | maj: reforme 06/2026`
R: À la date anniversaire, l'acheteur cesse d'acheter votre production. Si votre installation envoie tout sur le réseau par son propre compteur de production, elle continue de produire — mais plus personne ne paie cette électricité, et elle n'alimente pas votre maison. En clair : elle produit pour rien. C'est une échéance qui se prépare avant, pas après. Deux points à retenir : le contrat s'arrête **de lui-même**, il n'y a aucune résiliation à faire ; et si vous avez une seconde installation sous un autre contrat, celle-ci n'est pas concernée par cette échéance. `verif`

### Q: Faut-il résilier un contrat de vente totale qui arrive à échéance ?
`cat: photovoltaique | tags: vente_totale, edf_oa, fin_contrat, resiliation | verif: reglementation`
R: Non, et c'est une confusion fréquente. Un contrat qui arrive à son terme s'éteint seul à sa date anniversaire : aucune lettre, aucune démarche de rupture, aucune indemnité. La résiliation — avec préavis, indemnité éventuelle et remboursement possible de la prime — ne concerne que les contrats qu'on interrompt **avant** leur terme. Ne confondez pas les deux : on ne paie pas pour sortir d'un contrat qui se termine tout seul.

### Q: Que dois-je faire concrètement à la date de fin de mon contrat de rachat ?
`cat: photovoltaique | tags: vente_totale, edf_oa, demarches, fin_contrat | verif: reglementation`
R: Trois choses simples. **Vérifiez la date exacte** de fin sur votre contrat ou sur le courrier de l'acheteur — c'est une date anniversaire, pas une fin d'année civile. **Envoyez votre dernière facture de production**, avec le relevé de l'index du compteur à cette date. Et **n'attendez pas** pour décider de la suite : chaque mois qui passe après l'échéance est un mois où vos panneaux produisent sans que personne n'en profite. Si vous avez plusieurs installations, vérifiez laquelle est concernée : elles ont chacune leur contrat et leur date.

### Q: En fin de contrat, puis-je trouver un autre acheteur pour toute ma production ?
`cat: photovoltaique | tags: vente_totale, fin_contrat, acheteur, marche | verif: offres`
R: En pratique, non : la vente totale, c'est terminé — pour les maisons comme pour les grandes toitures. Les offres du marché portent aujourd'hui sur le rachat du **surplus** d'une installation en autoconsommation, pas sur la totalité d'une production : il n'existe pas d'acheteur sérieux et reconnu pour reprendre l'intégralité de ce que produisent vos panneaux. **Vous disposez de trois mois après la fin du contrat pour trouver un nouvel acheteur et le déclarer ; passé ce délai, c'est l'arrêt.** Le bon réflexe n'est donc pas de chercher à prolonger la vente, mais de préparer la suite avant l'échéance : faire servir cette production à votre propre maison. `verif`

### Q: Que faire de panneaux dont le contrat de rachat est terminé ?
`cat: photovoltaique | tags: vente_totale, fin_contrat, autoconsommation, reemploi | verif: generique`
R: Des panneaux de quinze ou vingt ans produisent encore l'essentiel de leur puissance d'origine : les déposer est un gâchis, et c'est le dernier recours, pas la première idée. La voie qui a du sens aujourd'hui est de **rebrancher cette production sur votre maison** au lieu de l'envoyer au réseau. Concrètement : l'installation ne passe plus par son compteur de production mais alimente votre tableau électrique, un onduleur unique peut reprendre plusieurs champs de panneaux, et l'onduleur se règle pour ne rien réinjecter. Une batterie prolonge l'usage en soirée. La contrepartie à connaître honnêtement : quand la batterie est pleine et que la maison ne consomme plus, la production est bridée et ce surplus-là est perdu — mais il ne serait racheté qu'un centime environ, donc l'arbitrage est vite fait. Décaler le lave-linge, le lave-vaisselle ou le chauffe-eau en journée en récupère une bonne partie.

## 2. Ajouter de la puissance sur une installation existante

### Q: Puis-je ajouter des panneaux à une installation déjà sous contrat de rachat ?
`cat: photovoltaique | tags: extension, ajout_panneaux, edf_oa, contrat_rachat, comptage | verif: CRITIQUE, reglementation | maj: reforme 06/2026`
R: Vous pouvez poser les panneaux, mais **leur production ne sera pas rachetée**, et c'est ce qui change tout. Depuis l'arrêté du 1er juin 2026, la règle est « une installation, un comptage » : ajouter des panneaux sur un branchement qui porte déjà une installation sous contrat ne donne plus droit au rachat, et on ne peut pas rattacher les nouveaux panneaux au contrat existant. Autrement dit, l'extension d'une installation sous contrat n'est plus une opération qui se valorise à la revente. Si vous voulez tout de même plus de production, elle n'a de sens que si vous la **consommez** : ce qui compte alors n'est plus la puissance posée mais votre capacité à l'utiliser sur place. Faites étudier votre cas avant d'engager quoi que ce soit. `verif`

### Q: Puis-je regrouper deux installations derrière un seul compteur pour signer un nouveau contrat ?
`cat: photovoltaique | tags: extension, regroupement, edf_oa, resiliation, comptage | verif: CRITIQUE, tarifs`
R: C'est techniquement envisageable et presque toujours une mauvaise affaire. Regrouper suppose de résilier le contrat en cours, donc d'y renoncer définitivement. Une indemnité de résiliation est alors due : elle combine en général **les reventes déjà perçues depuis le début du contrat, la prime reçue au départ, et des pénalités**. Elle grossit donc avec les années déjà encaissées : plus le contrat est ancien et la puissance élevée, plus la sortie coûte cher. Son montant exact n'est connu qu'après calcul par l'acheteur — demandez-le avant toute décision, c'est gratuit. Vous payez donc pour sortir d'un contrat signé à un tarif qui ne se signe plus, afin d'en signer un nouveau dont le surplus est racheté 1,1 centime le kWh. Avant toute décision : faites chiffrer l'indemnité par l'acheteur, c'est gratuit, et comparez-la à ce que le contrat actuel vous rapporte encore jusqu'à son terme. `verif`

### Q: Pourquoi la règle « une installation, un compteur » change-t-elle mes options ?
`cat: photovoltaique | tags: comptage, reforme, extension, edf_oa | verif: reglementation | maj: reforme 06/2026`
R: Parce qu'elle ferme la porte qui permettait d'agrandir une installation en restant dans son contrat. Depuis l'arrêté du 1er juin 2026 (publié au Journal officiel le 4 juin, applicable depuis le 5 juin), chaque installation doit avoir son propre comptage pour être rachetée. Combinée aux deux autres changements de la même réforme — surplus d'une nouvelle installation racheté 1,1 centime le kWh, et suppression des primes à l'investissement — elle fait qu'une électricité solaire vendue ne vaut presque plus rien, alors que la même électricité consommée chez soi vaut une vingtaine de centimes. Toute la réflexion se déplace donc de « combien je peux produire et vendre » vers « combien je peux réellement consommer ». `verif`

## 3. Les anciens contrats sont-ils menaces

### Q: J'ai entendu que l'Etat pourrait revenir sur les anciens contrats de rachat : suis-je concerne ?
`cat: photovoltaique | tags: edf_oa, contrat_rachat, retroactif, loi_finances, surrentabilite | verif: CRITIQUE, reglementation`
R: Si votre installation est celle d'une maison, non, pas a ce jour. La mesure dont on parle figure a l'article 69 du projet de loi de finances pour 2026 et vise les contrats dits S6 a S10, signes entre 2006 et 2010, pour des centrales de plus de 250 kW : de l'ordre de 436 installations sur les quelque 235 000 contrats d'obligation d'achat existants. Ce sont des tarifs historiques tres eleves, autour de 567 EUR/MWh, que l'Etat veut ramener a environ la moitie au motif de « surrentabilite ». Une mesure comparable avait ete votee en 2021 puis abandonnee apres censure du Conseil d'Etat ; celle-ci a cette fois ete soumise a la Commission europeenne. Deux reserves d'honnetete : le dossier n'est pas clos et peut evoluer, et la filiere en discute au-dela de ce qui est aujourd'hui ecrit dans les textes. Si vous exploitez une grande installation ancienne, faites suivre votre contrat de pres. Pour une installation residentielle, rien n'indique a ce jour que vous soyez concerne. `verif`

### Q: Pourquoi mon surplus solaire ne vaut-il presque rien alors que l'electricite est chere ?
`cat: photovoltaique | tags: surplus, prix_negatifs, midi, reseau | verif: tarifs`
R: Parce que votre surplus arrive au moment ou le reseau en a le moins besoin. Toutes les installations solaires produisent en meme temps, au milieu de la journee, et injectent ensemble un volume dont le reseau ne sait que faire : sur le premier semestre 2026, la France a connu 407 heures de prix negatifs, soit pres de 10 % du temps. C'est la raison de fond du tarif unique de 1,1 centime le kWh applique au surplus residentiel depuis juin 2026 : ce n'est pas la valeur de votre electricite en general, c'est sa valeur a l'heure ou vous l'injectez. La consequence pratique est simple : le meme kWh vaut une vingtaine de centimes si vous le consommez chez vous a ce moment-la. Deplacer vos usages vers le milieu de journee, ou stocker, vaut bien mieux que vendre. `verif`
