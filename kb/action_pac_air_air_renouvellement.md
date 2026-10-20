# Base de connaissances — Renouveler sa pompe à chaleur air/air (source action_pac_air_air_renouvellement)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source action_pac_air_air_renouvellement).
# Fiche « action » du pré-audit (conseil « âge des équipements »). Complète pac_air_air.md sans le répéter.
# Aucune marque, aucun installateur.

---

### Q: Ma pompe à chaleur air/air a plus de 12 ans : faut-il la remplacer ?
`cat: chauffage | tags: pac_air_air, remplacement, age, duree_de_vie, pre_audit | verif: generique`
R: Pas forcément tout de suite, mais il faut s'y préparer. Une pompe à chaleur air/air vit souvent 12 à 18 ans, selon l'entretien, le climat et l'usage (une machine qui chauffe l'hiver et rafraîchit l'été travaille deux fois). Les signes qu'elle arrive en fin de vie : une puissance qui baisse (des pièces qui peinent à chauffer ou à refroidir), du bruit, des pannes qui se répètent, des recharges de fluide, de l'eau qui coule de l'unité intérieure. Tant qu'elle marche bien, faites-la entretenir et gardez-la. Mais préparez son remplacement : choisir dans l'urgence, en pleine canicule ou en plein hiver, c'est payer plus cher et choisir moins bien.

### Q: Une pompe à chaleur air/air récente consomme-t-elle vraiment moins ?
`cat: chauffage | tags: pac_air_air, scop, rendement, consommation | verif: generique`
R: Oui, en général nettement. Le rendement saisonnier en chauffage (le SCOP, sur l'étiquette énergie) des appareils récents est souvent de l'ordre de 4 à 5 en climat moyen. Une machine de 15 ans, usée et conçue avec une technologie plus ancienne, fait souvent moins bien que ce qu'elle annonçait à l'achat. À usage égal, la consommation d'électricité du chauffage peut donc baisser sensiblement au remplacement. L'économie exacte dépend de ce que consomme votre chauffage aujourd'hui : si votre facture de chauffage est faible, le gain en euros reste modeste, et le remplacement se décide surtout sur l'état de l'appareil. Votre pré-audit vous indique l'âge de votre équipement et sa part dans votre consommation.

### Q: Comment bien choisir la pompe à chaleur air/air qui remplacera l'ancienne ?
`cat: chauffage | tags: pac_air_air, choix, dimensionnement, multisplit, bruit | verif: generique`
R: En repartant de vos besoins, pas de l'ancien appareil.
- **La puissance** : si vous avez isolé ou changé vos fenêtres depuis, la maison demande moins. Une machine trop puissante cycle, s'use et consomme plus.
- **Le nombre d'unités intérieures** : une unité par pièce à chauffer donne un meilleur confort qu'une grosse unité dans le séjour (voir notre fiche sur ce choix).
- **Le bruit** : comparez le niveau sonore des unités intérieures, surtout pour les chambres, et celui de l'unité extérieure, pour vous et vos voisins.
- **L'emplacement de l'unité extérieure** : à l'abri du soleil direct l'été si possible, dégagée, sur des supports anti-vibratiles, avec une évacuation des condensats.
- **La réutilisation des liaisons** existantes : possible dans certains cas, mais seul l'installateur peut le confirmer après contrôle.

### Q: Comment faire durer sa pompe à chaleur air/air ?
`cat: chauffage | tags: pac_air_air, entretien, filtres, duree_de_vie | verif: reglementation`
R: Par un entretien simple et régulier. **Les filtres** des unités intérieures se nettoient tous les mois en période d'usage, à l'eau tiède : un filtre encrassé fait forcer la machine et dégrade l'air. **L'unité extérieure** reste dégagée : pas de feuilles, pas de plantes collées, pas de bâche. **L'entretien par un professionnel** est obligatoire tous les deux ans pour les appareils de 4 à 70 kW : contrôle de l'étanchéité du circuit, nettoyage des échangeurs, vérification des performances. Gardez les attestations : elles comptent pour la garantie et à la revente.

### Q: Quelles aides pour remplacer une pompe à chaleur air/air en 2026 ?
`cat: aides | tags: pac_air_air, aides, cee | verif: date_sensible_20_10_2026`
R: MaPrimeRénov' ne finance pas la pompe à chaleur air/air. Des primes CEE peuvent exister selon l'appareil et l'organisme, à vérifier avant de signer. La TVA applicable dépend de l'équipement et des conditions de pose : l'entreprise doit l'indiquer clairement sur le devis.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/action_pac_air_air_renouvellement.md ».
     Sert au conseil « âge » quand chauffage_principal = PAC_air_air ; une action chiffrée « au remplacement »
     (SCOP neuf contre SCOP ancien) est prévue au lot 4. -->

- **conseil_age** : « Votre pompe à chaleur air/air a {age} ans. Faites-la entretenir et préparez son remplacement : un appareil récent consomme généralement moins, et choisir avant la panne évite de choisir dans l'urgence. »
- **benefices** : moins de consommation à usage égal · plus de silence · un rafraîchissement d'été plus efficace
- **vigilance** : puissance recalculée sur la maison d'aujourd'hui · emplacement de l'unité extérieure · filtres nettoyés chaque mois
- **devis** : puissance justifiée · niveau sonore des unités · contrôle des liaisons existantes
