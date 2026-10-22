# Base de connaissances — Risques de la commune et vigilance météo (source risques_maison)
# Format identique à la FAQ : ### Q: / `meta` / R: — ingéré par l'agent crawler (source risques_maison).
# Écrit le 22/10/2026 pour les lots « risques de la commune » et « vigilance météo ». Neutre : aucune marque.
# Sources :
#  - Géorisques (ministère de la Transition écologique), API et site georisques.gouv.fr : risques par commune.
#  - Ministère de la Transition écologique, « Mesures de prévention, d'adaptation et de remédiation du phénomène de
#    retrait et de gonflement des sols argileux (RGA) dans la construction » (guide PNACC 3, références 2025).
#  - Météo-France, guide de la vigilance météorologique (conseils de comportement par phénomène, édition 2004) ;
#    la carte en vigueur est sur vigilance.meteofrance.fr.
#  - Service Public, fiche F33298 (débroussaillement, vérifiée le 07/01/2025).
# À RELIRE PAR STÉPHANE : toutes les questions sont `verif: a_verifier`. Aucun chiffre de probabilité ni de coût.

### Q: Comment savoir à quels risques ma commune est exposée ?
`cat: risques | tags: georisques, risques_naturels, commune, etat_des_risques | verif: a_verifier`
R: Le site public **Géorisques** recense, commune par commune, les risques connus : inondation, mouvements de terrain, retrait-gonflement des argiles, feux de forêt, séisme, radon, risques industriels, ainsi que les arrêtés de catastrophe naturelle passés. Hélios affiche ces informations **à l'échelle de votre commune** : elles disent ce qui existe autour de vous, pas ce qui touche précisément votre parcelle. Pour votre adresse exacte, Géorisques produit un rapport, et c'est l'**état des risques** officiel qui fait foi lors d'une vente ou d'une location.

### Q: Ma commune est concernée par le retrait-gonflement des argiles : que faire pour ma maison ?
`cat: risques | tags: argiles, rga, fissures, fondations, secheresse | verif: a_verifier`
R: Les sols argileux gonflent quand ils sont humides et se rétractent quand ils sèchent ; les sécheresses répétées font bouger les fondations. Les gestes de prévention du guide ministériel tiennent en quatre idées. **Éloigner l'eau des murs** : gouttières et descentes en bon état, eau de pluie envoyée loin de la maison, jamais au pied des murs, et réparation rapide de toute fuite de canalisation. **Stabiliser l'humidité autour** : une bande étanche d'environ 1 à 1,5 m autour de la maison, en pente vers l'extérieur, limite les variations du sol. **Tenir la végétation à distance** : pas d'arbre plus près de la maison que 1,5 fois sa hauteur adulte, sauf écran anti-racines ; tailler les haies chaque année. **Surveiller les fissures** et les noter dans votre carnet avec une photo et une date.

### Q: Une fissure apparaît sur ma maison : quand faut-il s'inquiéter ?
`cat: risques | tags: fissures, argiles, diagnostic, carnet | verif: a_verifier`
R: Les signes qui demandent un avis professionnel, d'après le guide ministériel sur les sols argileux : une fissure qui **s'élargit après chaque sécheresse** ; des fissures **en escalier** sur une façade ou autour des ouvertures ; des portes et fenêtres qui **coincent** ou se déforment ; un dallage qui se fissure ou un mur qui s'affaisse. Photographiez la fissure avec une règle à côté, datez-la dans le journal de votre maison et comparez d'une saison à l'autre. Avant de reboucher, faites traiter la cause : un diagnostic par un professionnel qualifié vient en premier.

### Q: Ma commune a un potentiel radon : qu'est-ce que ça change ?
`cat: risques | tags: radon, qualite_air, ventilation | verif: a_verifier`
R: Le radon est un gaz naturel, sans odeur, qui vient de certains sous-sols et peut s'accumuler dans les pièces basses et mal aérées. Un potentiel élevé dans la commune ne dit pas ce qui se passe chez vous. Les gestes simples : **aérer chaque jour**, garder une ventilation en état de marche (bouches propres, entrées d'air dégagées), et soigner l'étanchéité entre le sol et les pièces habitées lors de travaux. Une mesure dans le logement permet de savoir ; Géorisques indique où se renseigner.

### Q: Vigilance orange pour vent violent : que faire pour la maison ?
`cat: meteo | tags: vigilance, vent, toiture, panneaux | verif: a_verifier`
R: Avant le coup de vent, **rangez ou attachez tout ce qui peut s'envoler** : mobilier de jardin, parasols, bacs, poubelles, trampoline. Fermez volets et stores bannes. **Ne montez pas sur le toit**, ni pendant ni juste après : une tuile, une fixation de panneau ou une antenne se vérifient depuis le sol, puis par un professionnel si quelque chose a bougé. Après l'épisode, notez dans votre carnet ce que vous avez constaté, photo à l'appui : c'est utile pour l'assurance.

### Q: Vigilance orange pour orages : que faire pour la maison ?
`cat: meteo | tags: vigilance, orage, foudre, electricite | verif: a_verifier`
R: Mettez à l'abri ce qui craint la grêle et le vent (véhicule, objets de jardin). Pendant l'orage, **évitez d'utiliser les appareils électriques branchés au réseau** et le téléphone filaire ; débranchez si possible les appareils sensibles (box, ordinateur, télévision). Si un onduleur solaire ou un appareil s'est mis en défaut après l'orage, ne l'ouvrez pas : notez le message affiché et appelez l'installateur.

### Q: Vigilance orange pour pluie-inondation : que faire pour la maison ?
`cat: meteo | tags: vigilance, inondation, pluie, sous_sol | verif: a_verifier`
R: **Restez chez vous et évitez les déplacements.** Si votre maison est en zone habituellement inondable, montez à l'étage ce qui craint l'eau (papiers, appareils, produits), vérifiez que les gouttières et les regards ne sont pas bouchés, et préparez-vous à couper l'électricité dans les pièces basses si l'eau monte. Ne descendez pas dans un sous-sol ou un garage en train d'être inondé.

### Q: Vigilance canicule : comment protéger la maison et ceux qui y vivent ?
`cat: meteo | tags: vigilance, canicule, chaleur, confort_ete | verif: a_verifier`
R: Fermez volets et stores **côté soleil dès le matin**, et fenêtres pendant les heures chaudes ; ouvrez en grand la nuit, quand l'air dehors est plus frais. Pour les personnes : passer au moins trois heures par jour dans un endroit frais, boire souvent, se rafraîchir plusieurs fois par jour, éviter de sortir aux heures les plus chaudes (conseils de Météo-France). Pensez aux voisins âgés ou isolés. Notre fiche sur le confort d'été détaille les protections solaires.

### Q: Vigilance grand froid : que vérifier dans la maison ?
`cat: meteo | tags: vigilance, grand_froid, chauffage, monoxyde_de_carbone | verif: a_verifier`
R: Veillez au **bon fonctionnement du chauffage** et à la **qualité de l'air** : ne bouchez jamais les entrées d'air, et n'utilisez pas en continu un chauffage d'appoint à combustion, ni un appareil qui n'est pas fait pour chauffer (four, barbecue, groupe électrogène à l'intérieur). Protégez du gel les canalisations et compteurs exposés, et la pompe à chaleur selon sa notice (unité extérieure dégagée de la neige). En résidence secondaire, pensez à la mise hors gel.

### Q: Ma commune est exposée aux feux de forêt : qu'est-ce que je dois faire ?
`cat: risques | tags: feux_de_foret, debroussaillement, old | verif: a_verifier`
R: Si votre terrain est à moins de 200 m de bois, landes, maquis ou garrigues classés à risque, le **débroussaillement** autour de la maison est une obligation (fiche Service Public F33298), à entretenir chaque année. Indiquez-le dans votre fiche : votre carnet ajoutera la tâche au bon moment. En été, les jours de vigilance feux de forêt, ne faites aucun travail qui produit des étincelles près de la végétation (disqueuse, soudure, débroussailleuse à lame métallique).
