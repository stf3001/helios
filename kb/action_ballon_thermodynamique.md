# Base de connaissances — Remplacer son ballon électrique (source action_ballon_thermodynamique)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source action_ballon_thermodynamique).
# Fiche « action » du pré-audit. Complète ecs_solaire.md (conditions du thermodynamique, arbitrage avec
# les combles, pilotage solaire) et faq_maison.md (écogestes) sans les répéter. Aucune marque.

---

### Q: Passer à un ballon thermodynamique est-il rentable dans mon cas ?
`cat: ecs | tags: chauffe_eau_thermodynamique, rentabilite, pre_audit, remplacement | verif: generique`
R: Ça dépend surtout d'une question : votre ballon actuel est-il en fin de vie ?
- **S'il marche bien**, on compare le prix complet d'un ballon thermodynamique à zéro : le retour est long.
- **S'il approche de sa fin de vie**, on compare au prix d'un ballon électrique neuf, qu'il faudra de toute façon acheter. Seul le **surcoût** compte, et le retour devient souvent intéressant.
Un ballon thermodynamique consomme en général deux à trois fois moins d'électricité qu'un ballon classique pour la même eau chaude. Le gain est d'autant plus grand que le foyer est nombreux. Votre pré-audit calcule le temps de retour sur le surcoût quand votre ballon a plus de 12 ans, et sur le prix complet sinon. Il l'indique dans le libellé de l'action.

### Q: J'ai des panneaux solaires : ballon thermodynamique ou ballon électrique piloté ?
`cat: ecs | tags: chauffe_eau_thermodynamique, pilotage, solaire, cumulus | verif: generique`
R: Le principe est simple : avec des panneaux, un ballon électrique classique **piloté pour chauffer en journée**, sur votre production, ne vous coûte presque plus rien en été et une bonne partie de l'année. C'est le levier le plus simple de l'autoconsommation : un petit module de pilotage suffit, sans changer vos habitudes. Le ballon thermodynamique garde son intérêt l'hiver, quand la production baisse, et pour un foyer nombreux. Mais l'écart d'économie entre les deux se réduit beaucoup. À l'heure du remplacement, comparez les deux scénarios avec vos chiffres. Sans panneaux, le thermodynamique reste l'un des meilleurs leviers par euro dépensé (voir notre fiche sur l'eau chaude et le solaire).

### Q: Mon ballon électrique a plus de 12 ans : comment savoir s'il faut le changer ?
`cat: ecs | tags: ballon, cumulus, age, entretien, duree_de_vie | verif: generique`
R: Un ballon électrique vit souvent 10 à 20 ans, beaucoup moins en eau très calcaire. Les signes de fin de vie : une eau tiède ou qui manque plus vite qu'avant, un ballon qui chauffe longtemps (résistance entartrée), de la rouille au pied ou sur les raccords, une eau rouillée, une fuite au groupe de sécurité qui ne cesse pas. Pour le faire durer : **détartrer** et **contrôler l'anode** tous les deux à trois ans par un professionnel, actionner le **groupe de sécurité** une fois par mois, régler la température autour de **55 °C**. Et préparez le remplacement avant la fuite : c'est le moment de choisir calmement entre un ballon neuf identique, un ballon thermodynamique ou un ballon piloté sur vos panneaux.

### Q: Quels pièges éviter avec un ballon thermodynamique ?
`cat: ecs | tags: chauffe_eau_thermodynamique, vigilance, local, bruit, calcaire | verif: generique`
R: Les principaux :
- **Le local** : un appareil sur air ambiant prend ses calories dans la pièce. Dans un garage, une buanderie ou un cellier non chauffé et assez grand, c'est parfait. Dans une pièce chauffée, il refroidit la maison l'hiver. Sinon, choisissez une version gainée sur l'extérieur.
- **Le bruit**, comparable à un réfrigérateur un peu bruyant : pas à côté d'une chambre.
- **Le calcaire** : il use l'échangeur. En eau dure, prévoyez un entretien plus fréquent, voire un adoucisseur.
- **La taille** : un ballon trop petit fait tourner sa résistance électrique d'appoint, et l'économie fond. Dimensionnez sur votre foyer réel.
- **Le réglage** : un mode « boost » laissé en permanence revient à un ballon électrique classique.
- **L'évacuation des condensats**, à prévoir à l'installation.

### Q: Que doit contenir un devis de ballon thermodynamique ?
`cat: ecs | tags: chauffe_eau_thermodynamique, devis, cop, rge | verif: reglementation`
R: Le volume du ballon, le type de prise d'air (air ambiant, gainé, unité extérieure), le rendement annoncé (COP) avec ses conditions de mesure, la puissance de l'appoint électrique, l'emplacement prévu et la gestion des condensats. Il doit aussi indiquer la dépose et l'évacuation de l'ancien ballon, le raccordement (groupe de sécurité neuf), la mise en service avec la programmation, la qualification RGE et la prime CEE éventuelle, avec l'organisme qui la verse.

### Q: Quelles aides pour un ballon thermodynamique en 2026 ?
`cat: aides | tags: chauffe_eau_thermodynamique, maprimerenov, cee | verif: date_sensible_20_10_2026`
R: Pour tout dossier déposé **depuis le 1er septembre 2026**, le ballon thermodynamique **n'est plus financé par MaPrimeRénov' par geste** (décret n° 2026-822 du 25 août 2026). Il reste finançable dans une **rénovation d'ampleur**. Les **primes CEE** restent ouvertes à tous les revenus. Des bonifications temporaires ont été annoncées pour la fin de l'année 2026 : comparez les offres, et faites valider la prime avant de signer.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/action_ballon_thermodynamique.md ». -->

- **pourquoi_au_remplacement** : « Votre ballon a {age} ans : au moment de le changer, le thermodynamique ne coûte que la différence avec un ballon neuf, et consomme deux à trois fois moins. »
- **pourquoi_sinon** : « Votre ballon fonctionne : le remplacer maintenant coûte le prix complet. Préparez le choix pour sa fin de vie. »
- **avec_solaire** : « Avec des panneaux, un ballon électrique piloté sur la production fait déjà une grande partie du travail : comparez les deux au moment du remplacement. »
- **benefices** : deux à trois fois moins d'électricité pour l'eau chaude · un remplacement choisi, pas subi
- **vigilance** : local non chauffé ou version gainée · taille adaptée au foyer · eau calcaire = plus d'entretien
- **devis** : volume et prise d'air · COP et ses conditions · dépose de l'ancien ballon
