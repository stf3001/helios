# Base de connaissances — Remplacer son chauffage par une pompe à chaleur (source action_pac_remplacement)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source action_pac_remplacement).
# Fiche « action » du pré-audit. Le dimensionnement, les émetteurs, la loi d'eau et le devis détaillé
# sont dans pac_air_eau.md : cette fiche ne les répète pas, elle y renvoie.
# Aucune marque, aucun installateur.

---

### Q: Remplacer mon chauffage par une pompe à chaleur est-il rentable dans mon cas ?
`cat: chauffage | tags: pac, remplacement, rentabilite, pre_audit, fioul, gaz, convecteurs | verif: generique`
R: C'est souvent le plus gros levier d'un pré-audit, mais pas pour tout le monde. Une pompe à chaleur produit environ trois kWh de chaleur avec un kWh d'électricité. Elle gagne donc beaucoup face à un chauffage cher au kWh :
- **le fioul** : c'est le cas le plus favorable, surtout que la chaudière fioul neuve est interdite depuis 2022 ;
- **les convecteurs électriques** : la facture de chauffage baisse fortement. Attention au type de pompe à chaleur (voir la question suivante) ;
- **le gaz** : le gain existe mais il est plus modeste, et dépend des prix des deux énergies.
Le temps de retour dépend surtout de votre consommation réelle de chauffage. Une maison qui chauffe peu (climat doux, maison bien isolée, chauffage partiel) gagne peu en euros, même avec un bon appareil. Votre pré-audit fait ce calcul avec votre énergie et votre consommation. Il ne propose jamais de remplacer une pompe à chaleur qui fonctionne.

### Q: J'ai des convecteurs électriques : pompe à chaleur air/eau ou air/air ?
`cat: chauffage | tags: pac_air_air, pac_air_eau, convecteurs, emetteurs, choix | verif: generique`
R: C'est la question qui change tout le budget. Une pompe à chaleur **air/eau** chauffe de l'eau qui circule dans des radiateurs ou un plancher chauffant. Avec des convecteurs, ce circuit d'eau n'existe pas : il faut le créer (tuyaux, radiateurs dans chaque pièce, travaux de finition), ce qui peut doubler le coût du projet. Une pompe à chaleur **air/air** (unités intérieures murales, souvent appelée « clim réversible ») se pose sans circuit d'eau, chauffe et rafraîchit, et coûte bien moins cher. Ses limites : elle ne produit pas l'eau chaude, elle souffle de l'air, et elle n'ouvre pas droit à MaPrimeRénov'. Dans le Sud, avec des convecteurs, l'air/air est souvent la solution réaliste. L'air/eau se justifie si un réseau de radiateurs à eau existe déjà, ou dans une rénovation lourde.

### Q: Que faire avant de remplacer son chauffage par une pompe à chaleur ?
`cat: chauffage | tags: pac, ordre_des_travaux, isolation, dimensionnement | verif: generique`
R: Trois choses, dans l'ordre :
1. **Isoler ce qui se rembourse vite**, les combles en général, et régler la programmation. La maison demande alors moins de puissance, et la pompe à chaleur peut être plus petite : moins chère, plus silencieuse, plus efficace.
2. **Mesurer votre besoin réel** à partir de vos factures (voir notre fiche sur le dimensionnement d'une pompe à chaleur air/eau). C'est la base d'une bonne puissance.
3. **Vérifier vos radiateurs** : leur taille décide de la température d'eau nécessaire, donc du rendement.
N'attendez pas la panne de votre chaudière pour y penser : un remplacement dans l'urgence se décide mal, et l'hiver.

### Q: Au-delà des économies, qu'apporte une pompe à chaleur ?
`cat: chauffage | tags: pac, benefices, sortie_fossile, entretien | verif: generique`
R: La **sortie du fioul ou du gaz** : plus de livraison, plus de cuve, plus de dépendance au prix d'un combustible fossile. Une **énergie qui peut venir de vos panneaux solaires**, en partie. Pour une air/air, le **rafraîchissement d'été** avec le même appareil. Et une maison qui émet beaucoup moins de CO₂ : c'est souvent le geste qui fait le plus pour le climat dans une maison chauffée au fioul.

### Q: Quels pièges éviter avec une pompe à chaleur ?
`cat: chauffage | tags: pac, vigilance, bruit, surdimensionnement, electricite | verif: reglementation`
R: Les principaux :
- **Le surdimensionnement**, de loin le plus fréquent : une machine trop puissante coûte plus cher, cycle sans arrêt, s'use plus vite et consomme plus (détails dans notre fiche sur le dimensionnement).
- **Le bruit de l'unité extérieure** : choisissez son emplacement avec soin, loin des chambres et des voisins, sur des supports anti-vibratiles. Le bruit de voisinage est encadré par la loi.
- **L'urbanisme** : une unité extérieure visible depuis la rue peut demander une déclaration préalable, et l'accord de l'architecte des Bâtiments de France en secteur protégé.
- **L'électricité** : une pompe à chaleur peut imposer de revoir la puissance souscrite ou le tableau électrique. Faites-le chiffrer dans le devis.
- **L'entretien** : il est obligatoire, tous les deux ans, pour les pompes à chaleur de 4 à 70 kW.
- **Le démarchage** : il est interdit par téléphone pour ces travaux. Une offre « à 1 € » ou « financée par l'État » reçue par téléphone est un signal d'alerte.

### Q: Quelles aides pour remplacer son chauffage par une pompe à chaleur en 2026 ?
`cat: aides | tags: pac, maprimerenov, cee, renovation_ampleur | verif: date_sensible_20_10_2026`
R: La pompe à chaleur air/eau (et géothermique) fait partie des rares gestes **encore financés par MaPrimeRénov' par geste** après le 1er septembre 2026. Le montant dépend des revenus (voir notre fiche sur les barèmes 2026), et il est nul pour les revenus les plus élevés. S'y ajoutent les **primes CEE**, souvent bonifiées pour le remplacement d'une chaudière au fioul ou au gaz, et la **TVA à 5,5 %**. La pompe à chaleur air/air n'est pas aidée par MaPrimeRénov'. Deux points d'attention : en **rénovation d'ampleur**, depuis le 1er septembre 2026, une maison ne peut plus garder une chaudière au gaz ou au fioul, même en appoint ; et le projet de loi de finances pour 2027, en discussion à l'automne 2026, pourrait encore modifier ces aides. Vérifiez au moment du dépôt.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/action_pac_remplacement.md ». -->

- **pourquoi_rentable** : « Avec {chauffage}, chaque kWh de chaleur vous coûte cher. Une pompe à chaleur en produit environ trois pour un kWh d'électricité : c'est votre plus gros levier. »
- **pourquoi_peu_rentable** : « Votre maison chauffe peu ({cout_chauffage} €/an) : une pompe à chaleur rapporterait peu en euros. Préparez son remplacement à la fin de vie de votre chaudière. »
- **benefices** : sortie du fioul ou du gaz · une énergie qui peut venir de vos panneaux · beaucoup moins de CO₂
- **vigilance** : isoler avant pour une machine plus petite · emplacement de l'unité extérieure (bruit) · puissance justifiée par vos factures
- **devis** : puissance justifiée · désembouage et filtre · mise en service et réglage de la loi d'eau
- **note_convecteurs** : « Avec des convecteurs, il n'y a pas de circuit d'eau : une PAC air/eau impose d'en créer un. Une PAC air/air est souvent la solution réaliste. »
