# Base de connaissances — Ventiler sa maison (source action_ventilation)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source action_ventilation).
# Fiche « action » du pré-audit. Complète faq_maison.md (« VMC simple ou double flux ? », « Pas de VMC
# chez moi : est-ce grave ? ») sans les répéter. Aucune marque, aucun installateur.

---

### Q: Une VMC double flux est-elle rentable dans mon cas ?
`cat: ventilation | tags: vmc, double_flux, rentabilite, pre_audit | verif: generique`
R: Rarement sur la seule facture, et encore moins dans le Sud. Une double flux récupère une grande partie de la chaleur de l'air extrait, mais elle coûte plusieurs milliers d'euros, consomme un peu d'électricité, demande un réseau de gaines et un entretien régulier. Elle ne tient ses promesses que dans une **maison déjà très étanche à l'air** : sinon, l'air entre et sort par les fuites, sans passer par l'échangeur. Elle devient pertinente :
- lors d'une **rénovation lourde**, quand les plafonds sont ouverts et que l'isolation est refaite ;
- en **climat froid**, où l'air entrant est très froid une bonne partie de l'année ;
- quand la **qualité de l'air** compte beaucoup (allergies, bruit extérieur qui empêche d'ouvrir).
Dans la plupart des maisons, une **simple flux hygroréglable** bien installée règle l'essentiel pour bien moins cher. Votre pré-audit classe la double flux « à l'occasion » quand son temps de retour est trop long.

### Q: Comment savoir si ma maison est bien ventilée ?
`cat: ventilation | tags: vmc, diagnostic, humidite, entrees_air | verif: generique`
R: Quelques signes ne trompent pas.
- **La buée** qui reste longtemps sur les vitres le matin, des **moisissures** dans les angles ou derrière les meubles, une **odeur de renfermé** : l'air n'est pas assez renouvelé.
- **Le test de la feuille** : VMC en marche, posez une feuille de papier sur une bouche d'extraction (cuisine, salle de bain). Si elle ne tient pas toute seule, le débit est insuffisant ou la bouche est encrassée.
- **Les entrées d'air** : il en faut dans les pièces de vie et les chambres, en haut des fenêtres ou dans les murs. Si elles sont bouchées ou absentes, l'air neuf n'arrive pas.
- **Le passage de l'air** sous les portes intérieures (un espace d'environ 1 cm sous la porte) : sans lui, l'air ne circule pas des pièces de vie vers les pièces humides.
Un hygromètre à quelques euros aide beaucoup : une humidité durablement au-dessus de 60 à 65 % en hiver signale un problème de ventilation.

### Q: Pourquoi ventiler davantage après avoir isolé ou changé les fenêtres ?
`cat: ventilation | tags: vmc, isolation, fenetres, humidite, ordre_des_travaux | verif: generique`
R: Parce qu'une maison rénovée est plus étanche. Avant, l'humidité de la douche, de la cuisine et de la respiration s'échappait par les fuites : vieilles fenêtres, plafonds, coffres de volets. Une fois ces fuites bouchées, elle reste dedans si rien ne l'évacue. Résultat classique quelques mois après les travaux : buée, moisissures, et le sentiment que « la maison respire mal ». La règle est simple : **chaque chantier d'isolation ou de fenêtres s'accompagne d'une vérification de la ventilation**, et d'une VMC si la maison n'en a pas.

### Q: Quels pièges éviter avec une VMC ?
`cat: ventilation | tags: vmc, vigilance, entretien, combustion, bruit | verif: generique`
R: Les plus courants :
- **L'arrêter pour « économiser »** : une VMC consomme peu, et la couper fait monter l'humidité. Elle tourne en permanence.
- **Les bouches encrassées** : un nettoyage tous les trois mois à l'eau savonneuse. Pour une double flux, les filtres se changent ou se nettoient selon la notice, souvent deux fois par an.
- **Les appareils à combustion** (chaudière non étanche, poêle, cheminée) : une VMC mal adaptée peut perturber leur tirage. Faites vérifier la compatibilité par un professionnel.
- **La hotte de cuisine** ne se raccorde jamais sur le réseau de la VMC.
- **Le bruit** : un caisson posé sans support anti-vibratile, ou des gaines écrasées, s'entendent dans toute la maison.
- **Les gaines dans des combles froids** : elles doivent être isolées, sinon la condensation coule dans le réseau.

### Q: Que doit contenir un devis de VMC ?
`cat: ventilation | tags: vmc, devis, hygroreglable, rge | verif: reglementation`
R: Le type de VMC (simple flux autoréglable, hygroréglable A ou B, double flux), le caisson et sa consommation électrique, le nombre et l'emplacement des bouches d'extraction, les entrées d'air ajoutées ou remplacées, le détalonnage des portes si nécessaire, le passage et l'isolation des gaines, la sortie en toiture ou en façade, et la mise en service avec la mesure des débits. Pour une double flux, il précise aussi l'emplacement de l'échangeur, les filtres et leur fréquence de remplacement. Vérifiez la qualification RGE et la TVA à 5,5 %.

### Q: Quelles aides pour installer une VMC en 2026 ?
`cat: aides | tags: vmc, double_flux, maprimerenov, cee | verif: date_sensible_20_10_2026`
R: Pour tout dossier déposé **depuis le 1er septembre 2026**, la VMC double flux **n'est plus financée par MaPrimeRénov' par geste** (décret n° 2026-822 du 25 août 2026). La ventilation reste finançable dans une **rénovation d'ampleur**. Des **primes CEE** existent pour les VMC simple flux hygroréglables et les double flux, avec un montant variable selon l'organisme : comparez, et faites-les valider avant de signer. La **TVA à 5,5 %** s'applique.

---

## Pour le pré-audit (textes courts, non ingérés)
<!-- À recopier dans audit_reference.py au lot 4, avec la référence « kb/action_ventilation.md ». -->

- **pourquoi_rentable** : « Votre maison est étanche et vous chauffez cher : une double flux récupère une bonne part de la chaleur de l'air extrait. »
- **pourquoi_peu_rentable** : « Une double flux coûte cher pour une économie modeste dans votre climat. Une simple flux hygroréglable bien réglée assure l'essentiel : un air sain. »
- **benefices** : un air sain · moins de buée et de moisissures · une maison qui garde sa santé après les travaux
- **vigilance** : ne jamais couper la VMC · bouches à nettoyer tous les trois mois · compatibilité avec les appareils à combustion
- **devis** : type de VMC et débits mesurés · entrées d'air · gaines isolées en combles
