# HELIOS — FAQ v1 (base de connaissances RAG)
*v0.1 — 16/07/2026 — format : 1 entrée = 1 chunk. `cat` = catégorie, `tags` = mots-clés, `verif` = à faire vérifier/actualiser par l'agent de veille. Montants = ordres de grandeur France métropolitaine 2026, TOUJOURS à confirmer.*

---

## 1. Sobriété & gestes gratuits

### Q: Quel est le geste le plus rentable pour réduire ma facture de chauffage ?
`cat: sobriete | tags: thermostat, temperature`
R: Baisser la consigne : 1 °C de moins ≈ 7 % de consommation de chauffage en moins. Recommandation : 19 °C pièces de vie, 17 °C chambres, 16 °C en absence. C'est gratuit et immédiat.

### Q: Un thermostat programmable, ça change quoi ?
`cat: sobriete | tags: thermostat, regulation, aides | verif: prime`
R: Programmer des réductions la nuit et en absence permet 10 à 15 % d'économies de chauffage. Un thermostat programmable coûte 60–250 €, un modèle connecté avec sondes 200–500 € pose comprise. Des aides CEE existent selon les périodes.

### Q: Quels écogestes sur l'eau chaude ?
`cat: sobriete | tags: ecs, ballon`
R: Régler le ballon à 55 °C (au-dessus, surconsommation ; en dessous de 50 °C, risque légionelles), installer des mousseurs et une douchette économe (débit 6–8 L/min), privilégier les douches courtes. L'ECS représente 10 à 15 % de la facture d'un foyer.

### Q: Faut-il éteindre le chauffage la journée en absence ?
`cat: sobriete | tags: chauffage, absence`
R: Réduire oui, éteindre rarement : pour une absence de journée, baisser de 2–3 °C est optimal. Éteindre totalement oblige à une relance coûteuse et refroidit les murs. Pour une absence de plus de 48 h, mode hors gel.

### Q: Le talon de consommation électrique, c'est quoi ?
`cat: sobriete | tags: talon, veille, enedis`
R: C'est la puissance consommée en permanence (veilles, box, frigo, VMC…), visible la nuit sur la courbe de charge. Un talon normal : 50–150 W. Au-delà de 200–300 W, il y a un gisement d'économies (veilles inutiles, vieux appareils, chauffe-eau mal programmé).

### Q: Les appareils en veille coûtent-ils vraiment cher ?
`cat: sobriete | tags: veille, electromenager`
R: Les veilles cumulées représentent souvent 300 à 500 kWh/an, soit 80–130 €/an. Multiprises à interrupteur et programmation des box suffisent à en supprimer une bonne partie.

### Q: Comment limiter la surchauffe l'été sans climatisation ?
`cat: sobriete | tags: confort_ete, canicule`
R: Volets/stores fermés le jour côté soleil, ventilation nocturne traversante, brasseurs d'air, végétalisation des abords. Les protections solaires extérieures sont bien plus efficaces que les rideaux intérieurs. La clim doit rester le dernier recours, après isolation et protections.

### Q: Purger ses radiateurs, utile ?
`cat: sobriete | tags: radiateur, entretien`
R: Oui, une fois par an avant l'hiver pour les circuits à eau : l'air accumulé réduit l'émission de chaleur. Vérifier aussi la pression de la chaudière (généralement 1–1,5 bar) et désembouer le circuit tous les 10 ans environ.

---

## 2. Isolation

### Q: Par quoi commencer pour isoler sa maison ?
`cat: isolation | tags: priorite, combles, deperditions`
R: Dans une maison non isolée, les déperditions typiques : toiture 25–30 %, murs 20–25 %, air renouvelé/fuites 20–25 %, fenêtres 10–15 %, planchers 7–10 %. On commence donc presque toujours par les combles/toiture : meilleur rapport coût/efficacité.

### Q: Combien coûte l'isolation des combles perdus ?
`cat: isolation | tags: combles, prix | verif: prix`
R: Par soufflage (laine de verre, roche, ouate) : ordre de grandeur 25–50 €/m² pose comprise, pour 30–40 cm d'isolant (R ≥ 7). Économie possible : 15–25 % sur le chauffage. Souvent amorti en moins de 5 ans.

### Q: Isolation des murs : intérieur ou extérieur ?
`cat: isolation | tags: murs, ITE, ITI | verif: prix`
R: L'ITE (extérieure, ~120–250 €/m²) supprime les ponts thermiques, ne réduit pas la surface habitable et ravale la façade, mais coûte plus cher et peut être contrainte en zone protégée. L'ITI (intérieure, ~50–100 €/m²) est moins chère mais réduit la surface et impose de refaire la déco. Depuis 2026, l'isolation des murs en geste isolé n'est plus aidée par MaPrimeRénov' (seulement en rénovation d'ampleur). `verif: regle 2026`

### Q: Quelle résistance thermique (R) viser ?
`cat: isolation | tags: resistance, R, performance`
R: Repères pour bénéficier des aides et d'un bon confort : combles perdus R ≥ 7, rampants R ≥ 6, murs R ≥ 3,7, planchers bas R ≥ 3. Le R figure sur les fiches produit ; plus il est élevé, mieux c'est.

### Q: Quels isolants choisir ?
`cat: isolation | tags: materiaux, biosource`
R: Laines minérales (verre, roche) : économiques et efficaces. Biosourcés (ouate de cellulose, fibre de bois, chanvre) : meilleur déphasage pour le confort d'été, bilan carbone favorable, 10–30 % plus chers. Le bon isolant est surtout celui qui est bien posé, sans ponts thermiques et avec une étanchéité à l'air soignée.

### Q: Isoler le plancher bas, ça vaut le coup ?
`cat: isolation | tags: plancher, cave, vide_sanitaire | verif: prix`
R: Si cave, garage ou vide sanitaire accessible dessous, c'est simple : panneaux fixés en sous-face, ~30–60 €/m², 5–10 % d'économies et un vrai gain de confort (sol moins froid).

### Q: Peut-on isoler soi-même ?
`cat: isolation | tags: DIY, aides, RGE`
R: Techniquement oui pour les combles perdus ou un plancher de cave. Mais attention : sans professionnel RGE, pas d'aides (MaPrimeRénov', CEE), et les erreurs (pare-vapeur, spots encastrés, ventilation) peuvent créer condensation et moisissures. Comparer le coût réel après aides avant de choisir le DIY.

### Q: Une maison trop isolée peut-elle mal respirer ?
`cat: isolation | tags: ventilation, humidite`
R: Le problème n'est jamais « trop d'isolation » mais une ventilation insuffisante. Toute rénovation d'isolation/menuiseries doit s'accompagner d'une vérification de la VMC : l'humidité doit être évacuée par la ventilation, pas par les fuites d'air.

---

## 3. Chauffage & pompes à chaleur

### Q: Quel est le chauffage le plus économique en 2026 ?
`cat: chauffage | tags: comparatif, cout | verif: prix_energie`
R: En coût d'usage, du moins cher au plus cher (ordres de grandeur) : bois bûche/granulés, PAC (grâce au rendement ×3-4), gaz, électrique direct, fioul. Mais le bon choix dépend du logement : une PAC n'est pertinente que dans un logement correctement isolé et avec des émetteurs adaptés.

### Q: Une pompe à chaleur, comment ça marche et qu'est-ce que le COP ?
`cat: chauffage | tags: PAC, COP`
R: Une PAC prélève des calories dans l'air (ou le sol) pour chauffer le logement. Le COP indique le rendement : COP 3-4 = 1 kWh électrique consommé pour 3–4 kWh de chaleur produits. Le COP baisse quand il fait très froid — vérifier les performances à -7 °C dans les régions froides.

### Q: PAC air-eau : prix et économies ?
`cat: chauffage | tags: PAC_air_eau, prix, aides | verif: prix, aides`
R: Ordre de grandeur : 10 000–18 000 € pose comprise selon puissance et ECS intégrée ou non. En remplacement d'un fioul ou d'un électrique direct, la facture de chauffage peut être divisée par 2 à 3. Aides possibles : MaPrimeRénov' selon revenus + CEE « Coup de pouce » en remplacement d'une chaudière fossile.

### Q: PAC air-air (clim réversible), bonne idée pour chauffer ?
`cat: chauffage | tags: PAC_air_air, clim`
R: Très efficace en mi-saison et régions tempérées, coût modéré (2 000–5 000 €/unité posée), et rafraîchit l'été. Limites : pas d'eau chaude sanitaire, aides très limitées, soufflage d'air moins confortable que des radiateurs à eau. Bon complément, ou solution principale dans le Sud.

### Q: Ma chaudière gaz fonctionne, faut-il la remplacer ?
`cat: chauffage | tags: gaz, remplacement`
R: Pas d'urgence si elle est récente et entretenue. Si elle a plus de 15 ans, une condensation moderne consomme 15–25 % de moins, et une PAC peut diviser la facture par 2 — à étudier avant la panne, pour ne pas choisir dans l'urgence. Anticiper aussi la trajectoire de hausse du prix du gaz.

### Q: Le poêle à granulés, quel budget ?
`cat: chauffage | tags: granules, bois, prix | verif: prix, aides`
R: 3 000–7 000 € posé. Combustible parmi les moins chers (~7–9 c€/kWh). Excellent en chauffage principal d'un logement compact ou en complément. Attention : les aides au bois ont baissé en 2026 `verif`, et il faut un stockage et un entretien annuel.

### Q: Radiateurs électriques : lesquels choisir si je garde l'électrique ?
`cat: chauffage | tags: radiateur_electrique, inertie`
R: Remplacer les vieux convecteurs « grille-pain » par des panneaux à inertie avec régulation électronique et détection de présence/fenêtre ouverte : même énergie mais meilleur confort et 10–20 % d'économies par la régulation. Rester sur l'électrique direct n'est pertinent que dans les logements bien isolés ou peu occupés.

### Q: Le fioul est-il encore autorisé ?
`cat: chauffage | tags: fioul, interdiction`
R: Depuis juillet 2022, l'installation de chaudières 100 % fioul neuves est interdite (réparation autorisée). Le remplacement d'un fioul par une PAC ou une chaudière biomasse bénéficie des aides les plus élevées. C'est le premier chantier à envisager si vous êtes au fioul.

---

## 4. Eau chaude sanitaire

### Q: Chauffe-eau thermodynamique : ça vaut le coup ?
`cat: ecs | tags: thermodynamique, prix | verif: prix`
R: Il consomme 2 à 3 fois moins qu'un ballon électrique classique (COP ~3). Prix : 2 500–4 500 € posé, aides possibles. Rentable en 5–8 ans pour une famille. Prévoir un local adapté (volume, bruit) ou une gaine vers l'extérieur.

### Q: Mon ballon électrique consomme trop, que faire sans le remplacer ?
`cat: ecs | tags: ballon, heures_creuses`
R: Vérifier qu'il chauffe en heures creuses (contacteur HC), régler à 55 °C, isoler les premiers mètres de tuyaux, détartrer tous les 3–5 ans (le tartre fait surconsommer). Une jaquette isolante sur un vieux ballon aide aussi.

### Q: Le solaire thermique pour l'eau chaude ?
`cat: ecs | tags: solaire_thermique, CESI | verif: prix`
R: Un chauffe-eau solaire (CESI) couvre 50–70 % des besoins annuels d'ECS. Prix : 4 000–7 000 € posé, aides MaPrimeRénov' possibles. Pertinent surtout dans la moitié Sud et pour les foyers de 3+ personnes. Alternative moderne : le thermodynamique, souvent plus simple et moins cher.

---

## 5. Ventilation & menuiseries

### Q: VMC simple ou double flux ?
`cat: ventilation | tags: VMC, double_flux | verif: prix`
R: Simple flux hygroréglable : 500–1 500 € posée, fiable, adaptée à la plupart des rénovations. Double flux : 4 000–8 000 €, récupère 70–90 % de la chaleur de l'air extrait, mais exige un réseau de gaines et une bonne étanchéité à l'air — pertinente en rénovation lourde ou maison très isolée.

### Q: Pas de VMC chez moi : est-ce grave ?
`cat: ventilation | tags: humidite, moisissures`
R: Oui, surtout après isolation ou changement de fenêtres : condensation, moisissures, air intérieur pollué. À minima, installer une VMC simple flux hygro et ne jamais boucher les entrées d'air des fenêtres.

### Q: Changer les fenêtres, est-ce prioritaire ?
`cat: menuiseries | tags: fenetres, double_vitrage | verif: prix`
R: Rarement le premier poste : 10–15 % des déperditions seulement, pour un coût élevé (400–1 000 €/fenêtre posée). Prioritaire si simple vitrage, menuiseries dégradées ou problème de bruit. Sinon, combles et systèmes passent avant. Le gain de confort (parois froides, bruit) reste réel.

### Q: Double ou triple vitrage ?
`cat: menuiseries | tags: triple_vitrage`
R: En France, le double vitrage performant (Uw ≤ 1,3) suffit presque partout. Le triple se justifie en climat froid ou sur des façades nord très exposées ; il est plus lourd et plus cher pour un gain marginal ailleurs.

---

## 6. Photovoltaïque & autoconsommation

### Q: Le photovoltaïque est-il rentable pour un particulier ?
`cat: photovoltaique | tags: rentabilite, autoconsommation | verif: tarifs | maj: reforme 06/2026`
R: Le plus souvent oui, mais la rentabilité ne vient plus du même endroit et elle est nettement plus lente qu'avant. Depuis la réforme de juin 2026, le surplus n'est racheté que 1,1 c€/kWh et la prime à l'autoconsommation a été supprimée : ce qui rembourse l'installation, ce sont uniquement les kWh que vous ne rachetez plus au réseau (~20 c€). Il n'existe pas de temps de retour « du photovoltaïque » : il se calcule au cas par cas, et l'écart entre deux foyers est énorme. Pour fixer les idées seulement, sur une installation posée de l'ordre de 6 300 € en 3 kWc ou 10 500 € en 6 kWc, le retour se compte aujourd'hui plutôt en quinze à vingt ans que sur les huit à douze ans d'avant la réforme — et il s'allonge encore de plusieurs années quand rien n'est déplacé en journée. Ce qui fait vraiment bouger ce chiffre, c'est votre consommation réelle, sa répartition dans la journée, l'orientation du toit et ce que vous acceptez de piloter (chauffe-eau, lave-linge, recharge). Dimensionnez sur votre consommation (production ≈ consommation annuelle), jamais sur la surface disponible du toit. Attention : si vous avez déjà une installation sous contrat de revente, votre situation ne se raisonne pas comme une installation neuve — voir les fiches sur les contrats EDF OA. Le simulateur d'Helios fait ce calcul sur vos propres chiffres ; c'est la seule réponse qui vaille. `verif`

### Q: Quelle taille d'installation solaire choisir ?
`cat: photovoltaique | tags: dimensionnement, kWc`
R: Dimensionner sur la consommation diurne, pas sur la toiture : 3 kWc couvrent les besoins de base d'un foyer moyen, 6 kWc si PAC, véhicule électrique ou forte conso de jour. Surdimensionner sans stockage réduit la rentabilité (surplus vendu peu cher).

### Q: Une batterie avec mes panneaux, bonne idée ?
`cat: photovoltaique | tags: batterie, stockage | verif: prix`
R: Une batterie augmente l'autoconsommation (60–80 %) mais coûte 4 000–8 000 € : la rentabilité reste souvent limite en 2026. Alternatives : piloter le chauffe-eau et les gros appareils en journée (« batterie virtuelle » comportementale), ou attendre la baisse des prix.

### Q: Mon toit est-il adapté au solaire ?
`cat: photovoltaique | tags: orientation, ombrage`
R: Idéal : sud, pente 30–35°, sans ombrage. Est/ouest reste très correct (-10 à -20 % de production, mieux réparti sur la journée). Vérifier : état de la toiture (la refaire avant si nécessaire), ombres (arbres, cheminées), et les règles d'urbanisme locales (déclaration préalable obligatoire).

### Q: Combien produit 1 kWc en France ?
`cat: photovoltaique | tags: production, kWc`
R: Selon la région : 900–1 100 kWh/an au nord, 1 200–1 450 kWh/an au sud. Une installation de 3 kWc produit donc environ 2 700 à 4 300 kWh/an.

---

## 7. Aides financières 2026

### Q: MaPrimeRénov' en 2026, où en est-on ?
`cat: aides | tags: maprimerenov, 2026 | verif: CRITIQUE`
R: Le guichet a rouvert le 23 février 2026 après l'adoption de la loi de finances, pour tous les parcours et profils de revenus. Changements 2026 : plafonds de ressources relevés d'environ 1 %, plafond de la rénovation d'ampleur abaissé de 70 000 à 40 000 € HT (saut de 3 classes), exclusion du parcours par geste des chaudières biomasse et de l'isolation des murs, baisse des primes bois. Délais d'instruction allongés (jusqu'à 6 mois pour les rénovations d'ampleur). Montants exacts : à vérifier sur france-renov.gouv.fr selon votre profil.

### Q: Quels sont les profils de revenus MaPrimeRénov' ?
`cat: aides | tags: maprimerenov, plafonds | verif: plafonds`
R: Quatre profils selon le revenu fiscal de référence et la composition du foyer : Bleu (très modestes), Jaune (modestes), Violet (intermédiaires), Rose (aisés). Plus le profil est modeste, plus l'aide est élevée. Les plafonds 2026 ont été légèrement relevés — vérifier son profil sur france-renov.gouv.fr.

### Q: Les CEE (certificats d'économies d'énergie), c'est quoi ?
`cat: aides | tags: CEE, prime_energie`
R: Des primes versées par les fournisseurs d'énergie pour vos travaux (isolation, chauffage…), cumulables avec MaPrimeRénov'. Montant variable selon les opérateurs : comparer les offres AVANT de signer le devis, la demande doit précéder les travaux. Les « Coups de pouce » bonifient certains remplacements de chauffage.

### Q: Quelles autres aides puis-je cumuler ?
`cat: aides | tags: cumul, TVA, eco_PTZ | verif: dispositifs`
R: TVA réduite 5,5 % sur les travaux de rénovation énergétique (appliquée directement sur le devis), éco-PTZ (prêt à taux zéro jusqu'à 50 000 € pour un bouquet), aides locales (région, département, commune — souvent méconnues), exonération partielle de taxe foncière dans certaines communes. Un conseiller France Rénov' peut faire le point gratuitement.

### Q: Pourquoi faut-il un artisan RGE ?
`cat: aides | tags: RGE, conditions`
R: Le label RGE (Reconnu Garant de l'Environnement) est obligatoire pour bénéficier de MaPrimeRénov', des CEE et de l'éco-PTZ. Vérifier la qualification sur l'annuaire officiel france-renov.gouv.fr, et qu'elle couvre bien le type de travaux concerné.

### Q: Comment éviter les arnaques à la rénovation ?
`cat: aides | tags: fraude, demarchage`
R: Le démarchage téléphonique pour la rénovation énergétique est interdit. Signaux d'alerte : « travaux à 1 € », pression à signer vite, offre de crédit intégrée, entreprise lointaine sans références locales. Toujours : plusieurs devis, vérification RGE, jamais de signature le jour même, jamais d'acompte important avant accord d'aides.

---

## 8. DPE & réglementation

### Q: Le DPE, à quoi ça sert et est-il fiable ?
`cat: dpe | tags: diagnostic, classes`
R: Le DPE classe le logement de A à G (consommation et émissions). Opposable depuis 2021, obligatoire pour vendre ou louer, validité 10 ans. Sa fiabilité s'est améliorée mais des écarts existent : Helios peut vous aider à interpréter le vôtre et à prioriser les travaux qui font gagner des classes.

### Q: Qu'est-ce qu'une passoire thermique et quelles interdictions de location ?
`cat: dpe | tags: passoire, location, interdiction | verif: calendrier`
R: Logements classés F et G. Calendrier d'interdiction de mise en location : G interdits depuis janvier 2025, F au 1er janvier 2028, E au 1er janvier 2034. Le gel des loyers s'applique déjà aux F et G. Propriétaires bailleurs : anticiper, les délais d'artisans s'allongent à l'approche des échéances.

### Q: Audit énergétique réglementaire : quand est-il obligatoire ?
`cat: dpe | tags: audit, vente | verif: calendrier`
R: Obligatoire pour la vente des maisons individuelles (mono-propriété) classées F ou G, étendu aux classes E depuis 2025. Réalisé par un professionnel certifié, il propose des scénarios de travaux. Le pré-diagnostic Helios ne remplace pas cet audit réglementaire mais aide à le préparer et à le comprendre.

### Q: Quelles démarches administratives avant travaux ?
`cat: reglementation | tags: urbanisme, declaration`
R: ITE, changement de fenêtres visibles, panneaux solaires : déclaration préalable en mairie dans la plupart des cas. Zones protégées (ABF) : contraintes renforcées. Copropriété : accord d'AG pour tout ce qui touche les parties communes ou l'aspect extérieur. Vérifier le PLU avant de s'engager.

---

## 9. Plateforme HELIOS

### Q: HELIOS, c'est quoi ?
`cat: helios | tags: presentation`
R: Une plateforme gratuite d'accompagnement à la transition énergétique des logements. Vous décrivez votre maison, Helios — notre IA franche et sans intérêt commercial — analyse et vous oriente : gestes gratuits, priorités de travaux, ordres de grandeur de coûts et d'aides, à votre rythme et selon vos objectifs.

### Q: Pourquoi est-ce gratuit ? Comment HELIOS gagne de l'argent ?
`cat: helios | tags: modele, transparence`
R: En toute transparence : si Helios vous préconise des travaux et que vous choisissez de les confier à une entreprise partenaire de la plateforme, celle-ci nous verse une commission d'apport d'affaires. Vous ne payez jamais rien, et les préconisations d'Helios sont strictement indépendantes de ce mécanisme.

### Q: Helios peut-il remplacer un audit énergétique ?
`cat: helios | tags: limites, audit`
R: Non. Helios fournit un pré-diagnostic indicatif basé sur les informations que vous renseignez. Il ne remplace pas un audit réglementaire réalisé par un professionnel certifié, ni un dimensionnement par un bureau d'études. Il vous aide à comprendre, prioriser et préparer ces étapes.

### Q: Que faites-vous de mes données ?
`cat: helios | tags: rgpd, donnees`
R: Vos données servent uniquement à personnaliser les conseils d'Helios. Elles sont hébergées en Union européenne, jamais transmises à un tiers sans votre consentement explicite et spécifique (par exemple pour une mise en relation partenaire que VOUS demandez). Vous pouvez les exporter ou les supprimer à tout moment depuis votre espace.

### Q: À quoi sert de renseigner mon PDL ?
`cat: helios | tags: pdl, enedis, conso`
R: Le PDL (point de livraison, 14 chiffres sur votre facture ou votre compteur Linky) permet, avec votre consentement explicite, de récupérer votre consommation réelle auprès d'Enedis. Helios peut alors analyser votre talon de consommation, détecter le poids du chauffage et évaluer votre potentiel d'autoconsommation solaire. (Fonctionnalité à venir.)

### Q: Comment les entreprises partenaires sont-elles sélectionnées ?
`cat: helios | tags: partenaires, charte`
R: Chaque partenaire signe notre charte : certifications à jour (RGE quand requis), transparence des prix, pas de démarchage, SAV réactif, acceptation de la notation par les clients. Un partenaire qui ne respecte plus la charte est déréférencé.

### Q: L'esprit colibri, c'est quoi ?
`cat: helios | tags: colibri, valeurs`
R: La légende du colibri qui, face à l'incendie, porte ses gouttes d'eau : « Je le sais, mais je fais ma part. » Chez HELIOS, aucun geste n'est trop petit : un réglage de thermostat compte autant qu'une rénovation complète. Helios vous aide à faire votre part, à votre échelle et à votre rythme.

---
---

# LOT 2 — *ajouté le 16/07/2026*

## 10. Devis, chantier & artisans

### Q: Comment comparer plusieurs devis ?
`cat: chantier | tags: devis, comparaison`
R: Comparer à périmètre égal : marque et modèle du matériel, performances (R, COP, Uw…), surface traitée, préparation et finitions incluses, garanties, délais. Un devis doit détailler fourniture et main-d'œuvre séparément. Le moins cher n'est pas toujours comparable : demander 3 devis minimum et exiger les fiches techniques.

### Q: Quelles mentions obligatoires sur un devis de rénovation ?
`cat: chantier | tags: devis, mentions`
R: Identité et SIRET de l'entreprise, assurance décennale avec coordonnées de l'assureur, détail des prestations et quantités, prix HT/TTC avec taux de TVA, durée de validité, mention de la qualification RGE si les aides en dépendent. Sans décennale vérifiable, ne pas signer.

### Q: Quel acompte est raisonnable avant travaux ?
`cat: chantier | tags: acompte, paiement`
R: Usage courant : 10 à 30 % à la commande, jamais plus de 50 % avant le début effectif du chantier, solde à la réception. Se méfier des demandes d'acompte élevées, surtout si l'entreprise a été rencontrée par démarchage. Attendre l'accord écrit des aides (MaPrimeRénov') avant de signer si le plan de financement en dépend.

### Q: Que faire en cas de malfaçon ?
`cat: chantier | tags: litige, garanties`
R: Réception avec réserves écrites, courrier recommandé à l'entreprise, puis : garantie de parfait achèvement (1 an), biennale (2 ans, équipements), décennale (10 ans, gros ouvrage). En cas de blocage : conciliateur de justice (gratuit), association de consommateurs, ou assurance protection juridique. Conserver tous les écrits.

### Q: Dans quel ordre enchaîner les travaux d'une rénovation complète ?
`cat: chantier | tags: ordre, phasage`
R: Ordre technique recommandé : 1) toiture/étanchéité si nécessaire, 2) isolation (combles, murs, planchers) + menuiseries, 3) ventilation, 4) chauffage/ECS dimensionnés sur la maison isolée (une PAC dimensionnée avant isolation sera surdimensionnée), 5) production solaire, 6) finitions. Grouper permet d'accéder à la rénovation d'ampleur, mieux aidée.

## 11. Copropriété & locataires

### Q: Locataire : que puis-je faire pour réduire mes factures ?
`cat: locataire | tags: droits, gestes`
R: Tous les gestes de sobriété (thermostat, mousseurs, veilles, joints de fenêtres provisoires) sont à votre main. Pour les travaux : le propriétaire ne peut pas s'opposer à des travaux de rénovation énergétique simples à vos frais dans certaines conditions, mais l'intérêt est limité. Le vrai levier : signaler par écrit un logement énergivore — un F ou G engage le bailleur (gel du loyer, calendrier d'interdiction de location).

### Q: Propriétaire bailleur : quelles obligations énergétiques ?
`cat: locataire | tags: bailleur, obligations | verif: calendrier`
R: Interdiction de louer les G depuis 2025, les F en 2028, les E en 2034 ; gel des loyers des F et G ; DPE obligatoire à la mise en location. Les aides MaPrimeRénov' sont ouvertes aux bailleurs (engagement de location). Anticiper : les délais artisans explosent à l'approche des échéances.

### Q: En copropriété, comment lancer des travaux énergétiques ?
`cat: copropriete | tags: AG, DTG`
R: Les travaux sur parties communes (ITE, chaudière collective, toiture) se votent en assemblée générale. Étapes : DPE collectif ou DTG, projet de plan pluriannuel de travaux (PPT, obligatoire selon taille de copro), mise au vote. Un copropriétaire peut faire ses travaux privatifs (fenêtres selon règlement, chauffage individuel) sans AG dans la plupart des cas. MaPrimeRénov' Copropriété aide les travaux collectifs. `verif: dispositif`

### Q: Puis-je installer une PAC ou des panneaux en copropriété ?
`cat: copropriete | tags: PAC, PV, autorisation`
R: Tout ce qui touche l'aspect extérieur ou les parties communes (unité extérieure de PAC en façade, panneaux en toiture commune) nécessite un vote en AG. En maison individuelle au sein d'un lotissement, vérifier le cahier des charges. Les refus abusifs peuvent parfois être contestés — se renseigner avant d'acheter le matériel.

## 12. Compteur, contrat & prix de l'énergie

### Q: À quoi sert le compteur Linky pour mes économies ?
`cat: energie | tags: linky, courbe_charge`
R: Linky enregistre la consommation par demi-heure. En activant la collecte de la courbe de charge (gratuit, depuis votre espace Enedis ou via HELIOS avec votre consentement), on peut repérer le talon de nuit, la part du chauffage, les appareils énergivores — sans rien installer.

### Q: Heures creuses : est-ce toujours intéressant ?
`cat: energie | tags: HPHC, tarif | verif: tarifs`
R: L'option HPHC n'est rentable que si vous déplacez réellement des usages (ballon ECS, lave-linge, VE) : en règle générale il faut 25–30 %+ de sa conso en heures creuses. Avec un ballon électrique ou une borne VE, c'est presque toujours oui. À noter : les plages d'heures creuses évoluent (davantage en journée pour suivre le solaire). `verif`

### Q: Ma puissance souscrite est-elle bien dimensionnée ?
`cat: energie | tags: kVA, abonnement`
R: Beaucoup de foyers paient un abonnement surdimensionné. Repères : 6 kVA suffisent souvent sans chauffage électrique, 9 kVA avec chauffage électrique ou PAC modeste, 12+ kVA avec VE et tout-électrique. Si votre compteur ne disjoncte jamais et que la puissance max relevée (visible sur Linky) est bien sous le seuil, descendre d'un cran économise 30–60 €/an.

### Q: Faut-il changer de fournisseur d'électricité ?
`cat: energie | tags: fournisseur, TRV`
R: Comparer via le comparateur officiel du Médiateur de l'énergie (comparateur-offres.energie-info.fr). Les écarts réels sont de quelques % ; se méfier des remises la première année et des prix indexés volatils. Changer est gratuit, sans coupure, réversible — mais c'est un levier secondaire par rapport à la réduction de la consommation.

## 13. Véhicule électrique & nouveaux usages

### Q: Installer une borne de recharge chez soi, quel budget ?
`cat: ve | tags: borne, irve | verif: prix, credit_impot`
R: Prise renforcée : 300–600 €. Wallbox 7 kW : 1 200–2 000 € posée par un installateur qualifié IRVE (obligatoire au-delà de 3,7 kW). Un crédit d'impôt existe pour l'installation d'une borne pilotable. `verif` Recharger en heures creuses ou sur surplus solaire optimise fortement le coût.

## 14. Humidité, air & confort

### Q: J'ai de la condensation sur les fenêtres, que faire ?
`cat: confort | tags: condensation, humidite`
R: Signe d'un air trop humide et/ou mal renouvelé : vérifier la VMC (aspiration effective aux bouches), ne pas obstruer les entrées d'air, aérer 5–10 min/jour même l'hiver, limiter le séchage du linge à l'intérieur. Si le simple vitrage est en cause, le survitrage ou le remplacement règle le point froid.

### Q: Moisissures dans une chambre : isolation ou ventilation ?
`cat: confort | tags: moisissures, pont_thermique`
R: Souvent les deux : un pont thermique (angle de mur froid) + un air humide mal renouvelé. Traiter d'abord la ventilation (VMC, entrées d'air), puis le pont thermique (isolation). Nettoyer ne suffit jamais si la cause reste. Un logement sain se joue à 40–60 % d'humidité relative.

### Q: Quelle température et humidité idéales chez soi ?
`cat: confort | tags: temperature, hygrometrie`
R: 19 °C pièces de vie, 17 °C chambres, 22 °C salle de bain en usage ; humidité relative 40–60 %. Un thermo-hygromètre coûte 10–15 € et objective le ressenti. Le confort dépend aussi des parois : un mur froid « aspire » la chaleur du corps, d'où la sensation de froid à 20 °C dans une maison mal isolée.

## 15. Financement & stratégie

### Q: L'éco-PTZ, comment ça marche ?
`cat: financement | tags: eco_ptz | verif: plafonds`
R: Prêt à taux zéro sans condition de ressources, jusqu'à 50 000 € pour une rénovation d'ampleur (montants inférieurs par geste), remboursable jusqu'à 20 ans, cumulable avec MaPrimeRénov' et les CEE. Demande auprès d'une banque partenaire avec les devis d'entreprises RGE. Il peut financer le reste à charge après aides.

### Q: Vaut-il mieux un gros bouquet de travaux ou étaler ?
`cat: financement | tags: strategie, renovation_ampleur`
R: Le bouquet (rénovation d'ampleur) est mieux aidé, plus cohérent techniquement et évite de refaire deux fois (ex. : PAC dimensionnée après isolation). L'étalement préserve la trésorerie et permet d'apprendre en marchant. Critère de décision : si un saut de 2–3 classes DPE est atteignable, le parcours d'ampleur mérite d'être chiffré en priorité — plafond d'aide 40 000 € HT en 2026. `verif`

### Q: Les travaux énergétiques valorisent-ils mon bien ?
`cat: financement | tags: valeur_verte`
R: Oui : les études notariales montrent une décote des passoires (F-G) et une surcote des logements A-B-C, variables selon les régions et la tension du marché (de quelques % à plus de 10 %). Avec le calendrier d'interdiction de location, un F/G se vend de plus en plus difficilement au prix. La rénovation est aussi un investissement patrimonial.

### Q: Quel temps de retour est « bon » pour des travaux ?
`cat: financement | tags: rentabilite, tri`
R: Repères : gestes et réglages < 1 an ; combles 2–5 ans ; chauffe-eau thermodynamique 5–8 ans ; PAC en remplacement fioul/élec 5–10 ans ; PV 14–20 ans depuis la réforme de juin 2026 (contre 8–12 ans avant) ; fenêtres et ITE 15 ans+. Mais le temps de retour ignore le confort, la valeur du bien et la protection contre les hausses de prix — à intégrer au raisonnement.

## 16. Compléments techniques

### Q: Qu'est-ce qu'un pont thermique ?
`cat: isolation | tags: pont_thermique`
R: Une zone où l'isolation est interrompue (jonction plancher/mur, balcon, linteaux) : la chaleur s'y échappe et la condensation s'y forme. Les ponts thermiques peuvent représenter 5–10 % des déperditions. L'ITE les traite mieux que l'ITI. En rénovation, on les limite ; on les supprime rarement tous.

### Q: L'étanchéité à l'air, pourquoi c'est important ?
`cat: isolation | tags: etancheite, infiltrometrie`
R: Les fuites d'air parasites (prises, trappes, jonctions) peuvent peser autant que de gros défauts d'isolation et créent des courants d'air inconfortables. En rénovation lourde, un test d'infiltrométrie (~500 €) objective le problème. Règle : on étanche ET on ventile mécaniquement — jamais l'un sans l'autre.

### Q: PAC géothermique : pour qui ?
`cat: chauffage | tags: geothermie | verif: prix`
R: Le meilleur rendement (COP 4–5, stable même par grand froid) mais l'investissement le plus lourd : 15 000–25 000 € avec capteurs horizontaux (grand terrain requis) ou sondes verticales (forage). Pertinente pour les grandes maisons en climat froid avec un projet long terme. En rénovation courante, l'air-eau reste le choix par défaut.

### Q: Le plancher chauffant est-il compatible avec une rénovation ?
`cat: chauffage | tags: plancher_chauffant`
R: Idéal avec une PAC (basse température = meilleur COP), mais lourd en rénovation : rehausse de 6–10 cm, reprise des sols. Alternatives en rénovation : radiateurs basse température surdimensionnés ou ventilo-convecteurs. À réserver aux rénovations lourdes avec reprise des sols déjà prévue.

### Q: Brasseur d'air ou climatiseur ?
`cat: confort | tags: confort_ete, brasseur`
R: Un brasseur d'air plafond (100–400 €, ~30 W) abaisse la température ressentie de 3–4 °C sans refroidir l'air — imbattable en coût. La clim (fixe : 1 500–4 000 €/pièce) refroidit vraiment mais consomme 50 à 100 fois plus. Stratégie : protections solaires + ventilation nocturne + brasseurs d'abord, clim en dernier recours et bien dimensionnée.

### Q: Récupérer l'eau de pluie, quel rapport avec l'énergie ?
`cat: eau | tags: recuperation, jardin`
R: Indirect mais réel : l'eau potable a un coût énergétique de production/distribution, et arroser ou alimenter les WC à l'eau de pluie réduit la facture d'eau (cuve enterrée 3 000–8 000 €, cuve de jardin dès 100 €). Dans une démarche colibri globale, c'est un geste cohérent — HELIOS reste néanmoins centré sur l'énergie.

### Q: Que penser des « panneaux solaires plug & play » (kits à brancher) ?
`cat: photovoltaique | tags: kit, plug_and_play | verif: reglementation`
R: Kits de 300–800 W à brancher sur une prise : 400–900 €, sans travaux, déclaration simplifiée auprès d'Enedis. Rentabilité correcte (5–8 ans) si bien exposés, car tout est autoconsommé. Limites : pas d'aides, pas de vente de surplus, fixation et assurance à vérifier. Bonne porte d'entrée, notamment pour les locataires.

### Q: L'entretien annuel de ma PAC ou chaudière est-il obligatoire ?
`cat: chauffage | tags: entretien, obligation`
R: Oui : entretien obligatoire tous les 2 ans pour les PAC et climatisations de 4 à 70 kW, tous les ans pour les chaudières gaz/fioul/bois de 4 à 400 kW. Au-delà de l'obligation, un système entretenu consomme 5–10 % de moins et dure plus longtemps. Contrat d'entretien : 150–250 €/an typiquement.

---
---

# LOT 3 — *ajouté le 16/07/2026 — solaire & stockage renforcés, achat d'énergie*

## 17. Solaire — approfondissement

### Q: Autoconsommation totale, avec vente de surplus, ou vente totale : que choisir ?
`cat: photovoltaique | tags: autoconsommation, surplus, obligation_achat | verif: tarifs | maj: reforme 06/2026`
R: Depuis la réforme du 5 juin 2026, le rachat du surplus résidentiel est tombé à 1,1 c€/kWh — soit ~17 fois moins que le kWh acheté : vendre son surplus n'est plus une stratégie, c'est un reliquat. Le standard 2026 : autoconsommation maximisée (pilotage des usages) + **batterie virtuelle** pour valoriser le surplus (cf. entrées stockage virtuel). La vente totale n'a plus de sens pour un particulier.

### Q: Micro-onduleurs ou onduleur central ?
`cat: photovoltaique | tags: onduleur, micro_onduleur`
R: Micro-onduleurs (un par panneau) : production optimisée panneau par panneau, tolérance aux ombrages, suivi fin, mais coût supérieur (~10–20 %). Onduleur central (string) : plus simple et moins cher, mais un panneau ombragé pénalise la chaîne. Règle simple : ombrages partiels ou orientations multiples → micro-onduleurs ; toiture uniforme dégagée → central. Durée de vie onduleur central : 10–15 ans (remplacement à budgéter), micro-onduleurs souvent garantis 20–25 ans.

### Q: Combien coûte une installation PV en 2026, poste par poste ?
`cat: photovoltaique | tags: prix, detail | verif: prix`
R: Pour 3 kWc posés (~7 000–9 000 € TTC) : panneaux ~30 %, onduleur/micro-onduleurs ~15–20 %, structure et câblage ~10 %, main-d'œuvre et démarches ~30–40 %. La pose représente une grande part : comparer plusieurs devis à matériel équivalent. TVA réduite sur les petites installations ≤ 9 kWc depuis 2025 (à vérifier selon configuration). `verif: TVA`

### Q: Existe-t-il encore une prime à l'autoconsommation ?
`cat: photovoltaique | tags: prime, aides | verif: CRITIQUE | maj: reforme 06/2026`
R: Non : la prime à l'autoconsommation a été supprimée par l'arrêté du 1er juin 2026 (réforme S21), qui a aussi abaissé le rachat du surplus à 1,1 c€/kWh. La rentabilité du PV repose désormais entièrement sur l'autoconsommation (kWh évités à ~19 c€) : dimensionnement production ≈ consommation, pilotage des usages, batterie virtuelle. La TVA réduite reste applicable selon configuration. `verif`

### Q: Panneaux au sol, sur pergola, ou façade : alternatives à la toiture ?
`cat: photovoltaique | tags: sol, pergola, carport`
R: Possibles et parfois plus simples : pose au sol (déclaration préalable selon hauteur/zone, pas de travaux de toiture), carport ou pergola solaire (double usage), façade (production hivernale meilleure, annuelle moindre). Attention : les installations au sol ne bénéficient pas de l'obligation d'achat dans les mêmes conditions que la toiture. `verif: conditions`

### Q: Mes panneaux produiront-ils encore dans 25 ans ?
`cat: photovoltaique | tags: duree_vie, garantie`
R: Oui : les garanties constructeur typiques assurent 85–90 % de la puissance initiale après 25–30 ans. La dégradation réelle constatée est de l'ordre de 0,3–0,5 %/an. Les points de vigilance sont plutôt l'onduleur (à remplacer une fois) et la qualité de pose (étanchéité). Le recyclage est organisé et financé en France (éco-participation, filière Soren).

### Q: L'autoconsommation collective, c'est quoi ?
`cat: photovoltaique | tags: autoconsommation_collective, ACC`
R: Partager la production d'une installation entre plusieurs consommateurs proches (voisins, copropriété, commune) via une personne morale organisatrice, dans un rayon de 2 km (extensible jusqu'à 20 km en zone rurale, selon dérogations). Intéressant en copropriété ou pour valoriser une grande toiture. Cadre en évolution — se faire accompagner. `verif: perimetre`

### Q: Comment maximiser mon taux d'autoconsommation sans batterie ?
`cat: photovoltaique | tags: pilotage, autoconsommation`
R: Déplacer les usages vers les heures solaires : chauffe-eau piloté en journée (le « stockage » le moins cher qui soit : un routeur solaire coûte 150–500 €), lave-linge/lave-vaisselle programmés, recharge VE en journée, PAC pilotée. Un foyer qui pilote bien passe de ~30 % à 50–70 % d'autoconsommation sans batterie.

## 18. Stockage d'énergie

### Q: Batterie domestique : quelles technologies en 2026 ?
`cat: stockage | tags: batterie, technologies`
R: Le marché résidentiel est dominé par le lithium LFP (lithium-fer-phosphate) : sûr, durable (4 000–8 000 cycles), sans cobalt. Le NMC (plus dense mais moins durable) recule dans le résidentiel. La technologie montante : le sodium-ion, en cours d'industrialisation massive. Prix indicatifs 2026 des batteries installées : ~2 500–4 500 € pour 5 kWh, 5 000–8 500 € pour 10 kWh.

### Q: La batterie sodium-ion, c'est quoi et pourquoi en parle-t-on ?
`cat: stockage | tags: sodium_ion, innovation | verif: marche`
R: Une batterie qui remplace le lithium par du sodium — abondant, bon marché, sans cobalt ni lithium. Atouts : coût de cellule potentiellement 20–30 % inférieur au LFP à terme, excellente tenue au froid, sécurité élevée, matériaux non critiques. Limite : densité énergétique plus faible (~175 Wh/kg), donc des batteries un peu plus volumineuses — peu gênant en stationnaire résidentiel. Les géants (CATL avec sa gamme Naxtra, BYD) ont lancé la production de masse en 2026.

### Q: Quand pourra-t-on acheter une batterie sodium-ion pour sa maison en France ?
`cat: stockage | tags: sodium_ion, disponibilite | verif: CRITIQUE`
R: Mi-2026, l'offre résidentielle sodium-ion en France reste quasi inexistante : la production de masse démarre (CATL ~30 GWh/an visés, usine BYD dédiée) et les premières offres résidentielles crédibles sont attendues vers 2027, avec une vraie concurrence au LFP à l'horizon 2028 (~350–400 €/kWh projetés). Conseil Helios : si votre projet batterie est urgent, le LFP reste le choix rationnel ; s'il peut attendre 1–2 ans, le sodium-ion mérite d'être surveillé — nous suivons le sujet.

### Q: Une batterie est-elle rentable aujourd'hui ?
`cat: stockage | tags: rentabilite, batterie | verif: prix`
R: Le calcul : chaque kWh stocké vous fait économiser (prix du kWh acheté – tarif de rachat du surplus), soit grossièrement 15–20 c€/kWh valorisés. Une batterie 5 kWh bien utilisée valorise 1 200–1 800 kWh/an → 200–350 €/an, pour 2 500–4 500 € d'investissement : rentabilité en 10–15 ans, à la limite de sa durée de vie. Elle devient plus intéressante avec les tarifs dynamiques (charger quand c'est bon marché) et la baisse des prix à venir (sodium-ion). Priorité au pilotage des usages, batterie ensuite.

### Q: Batterie virtuelle ou batterie physique ?
`cat: stockage | tags: batterie_virtuelle, batterie_physique, comparatif, choix | seo_titre:Batterie virtuelle ou physique : comment choisir | seo_desc:Sécurité en cas de coupure, indépendance, coût réel : ce qui sépare vraiment les deux, au-delà de l'argument financier. Sans parti pris commercial.`
R: Les deux ont de vrais avantages, et le choix ne se résume pas à l'argent. Ce que la batterie PHYSIQUE apporte et que la virtuelle ne peut pas : la sécurité d'alimentation (avec un onduleur hybride et une fonction back-up, la maison garde du courant même quand le réseau est coupé), l'indépendance vis-à-vis d'un opérateur, et le sentiment — légitime — de stocker SON énergie chez soi. Ce que la VIRTUELLE apporte : aucun matériel, aucun entretien, aucune perte de capacité dans le temps, et un coût du kWh restitué souvent plus bas (voir la fiche dédiée). Deux réserves fréquentes et parfaitement recevables sur la virtuelle : elle suppose de passer chez un fournisseur alternatif (mylight150, Urban Solar…) alors que beaucoup préfèrent rester chez EDF, TotalEnergies ou Engie, et ses conditions tarifaires sont révisables. Enfin, l'écart économique dépend vraiment de VOTRE foyer : consommation annuelle, mais surtout répartition de cette consommation dans la journée. La méthode d'Helios : simuler votre installation, comparer les deux options à consommation réelle égale (c'est ce que fait le simulateur d'autoconsommation), vous présenter les deux résultats — et vous laisser décider. Helios peut vous interroger sur vos objectifs et vos préférences, mais le choix vous appartient toujours.

### Q: Peut-on utiliser la batterie de sa voiture électrique pour la maison (V2G/V2H) ?
`cat: stockage | tags: v2g, v2h, ve | verif: offres`
R: Le vehicle-to-home arrive : une batterie de VE (40–100 kWh) dépasse largement une batterie domestique. Prérequis : véhicule compatible, borne bidirectionnelle (encore chère, ~3 000–6 000 €), offre fournisseur adaptée. Les premières offres commerciales françaises émergent — pertinent surtout si le véhicule dort à la maison. Technologie à surveiller plutôt qu'à acheter en premier équipement pour la plupart des foyers.

### Q: Où installer une batterie et quelles précautions ?
`cat: stockage | tags: securite, installation`
R: Local tempéré (les performances chutent au froid extrême, hors sodium-ion), ventilé, à l'écart des pièces de vie et des matériaux inflammables ; fixation murale ou au sol selon modèle ; déclaration à l'assureur recommandée. Installation par un professionnel qualifié, protections électriques dédiées. Les LFP et sodium-ion présentent un risque d'emballement thermique très faible comparé aux anciennes chimies.

## 19. Achat d'énergie & tarifs dynamiques

### Q: Qu'est-ce qu'une offre à tarification dynamique ?
`cat: achat_energie | tags: tarif_dynamique, spot`
R: Le prix du kWh suit les prix de marché heure par heure (connus la veille). Les heures creuses solaires de mi-journée et les nuits sont souvent très bon marché ; les pointes d'hiver (8h-13h, 18h-20h) peuvent être chères. Rentable pour les foyers pilotables (VE, ballon, batterie, PAC) qui déplacent leur consommation ; risqué pour un chauffage électrique non pilotable. Compteur Linky requis.

### Q: Courtier en énergie : que peut-il m'apporter ?
`cat: achat_energie | tags: courtage, fournisseur`
R: Un courtier compare les offres du marché sur la base de votre profil réel de consommation (via votre PDL) et négocie parfois des conditions. Points de vigilance : rémunération du courtier (commission fournisseur — demander la transparence), pas d'engagement sans comparaison avec le TRV et le comparateur public. Sur HELIOS, l'étude d'achat d'énergie n'est lancée qu'à votre demande, et Helios vous donne son avis indépendant sur les résultats avant toute décision.

### Q: Le tarif réglementé (TRV) est-il toujours une référence sûre ?
`cat: achat_energie | tags: trv, reference`
R: Le TRV électricité reste le refuge par défaut : prix encadré, pas de mauvaise surprise contractuelle. Les offres de marché peuvent faire mieux (notamment indexées ou dynamiques pour les profils pilotables), mais lisez la durée du prix garanti et les conditions de révision. Règle Helios : ne jamais quitter le TRV pour un gain < 5 % sans autre avantage.

### Q: Mon profil de consommation change après travaux : dois-je revoir mon contrat ?
`cat: achat_energie | tags: optimisation, apres_travaux`
R: Oui, systématiquement : une PAC déplace la consommation vers l'électricité (revoir puissance et option), une isolation la réduit (puissance souscrite peut baisser), le PV change tout (option, heures creuses de jour, tarif dynamique). L'optimisation du contrat est le dernier kilomètre de toute rénovation — souvent 50–150 €/an récupérés sans travaux.

---
---

# LOT 4 — *ajouté le 16/07/2026 — stockage virtuel (source : étude ADSolar 06/2026, cf. KB) & SOBRY*

## 20. Stockage virtuel & valorisation du surplus

### Q: Qu'est-ce qu'une batterie virtuelle, concrètement ?
`cat: stockage | tags: batterie_virtuelle, principe`
R: Votre surplus solaire est injecté au réseau et crédité sur un compte kWh chez un opérateur (Urban Solar Energy, mylight150…) ; vous « récupérez » ces kWh plus tard, en payant selon l'offre les frais de restitution, taxes et acheminement. Pas de matériel (sauf offres spécifiques), pas d'entretien, pas de perte de capacité. Depuis la chute du rachat à 1,1 c€/kWh (juin 2026), c'est devenu LE mode de valorisation du surplus résidentiel.

### Q: Batterie virtuelle ou vente du surplus : que disent les chiffres ?
`cat: stockage | tags: batterie_virtuelle, comparatif | verif: grilles operateurs`
R: Sans appel depuis juin 2026 : tant que la production n'excède pas ~1,5× la consommation annuelle, la batterie virtuelle bat la vente de surplus dans 100 % des cas simulés (étude ADSolar, 196 configurations, sud de la France). Coût complet du kWh restitué : 0,11–0,16 €/kWh selon l'opérateur, contre un kWh réseau à ~0,19 € — alors que le surplus vendu ne rapporte que 0,011 €.

### Q: Quel opérateur de batterie virtuelle choisir ?
`cat: stockage | tags: batterie_virtuelle, operateurs | verif: grilles operateurs`
R: Ça dépend du surplus restitué par an : au-delà d'environ 2 300 kWh/an (en pratique dès 4-6 kWc pour un foyer familial), un forfait avec matériel type MySmartBattery (frais d'entrée ~1 800 €, restitution à 0 €/kWh) devient imbattable ; en dessous, les offres sans matériel (Urban Solar, MyBattery) l'emportent. Points de vigilance communs : offres sans engagement de préférence, ne pas thésauriser les crédits kWh au-delà d'un hiver, re-simuler à chaque évolution tarifaire. Helios peut faire le calcul sur VOS chiffres.

### Q: Batterie physique ou batterie virtuelle en 2026 ?
`cat: stockage | tags: batterie_physique, comparatif | maj: reforme 06/2026`
R: Aux prix 2026 (700–800 €/kWh posé), le coût complet du kWh stocké en batterie physique (0,31–0,40 €) dépasse le prix du kWh réseau : ce n'est pas un placement, c'est un produit de confort (secours coupure, autonomie). La batterie virtuelle fait mieux financièrement dans quasi tous les cas. Et acheter une batterie physique « plus tard quand les prix auront baissé » après souscription d'une BV ne devient rentable à aucun horizon simulé. La donne pourra changer avec le sodium-ion (~2028) — sujet suivi par notre veille.

### Q: Comment bien dimensionner son installation solaire depuis la réforme 2026 ?
`cat: photovoltaique | tags: dimensionnement, reforme | maj: reforme 06/2026`
R: Nouvelle règle : production ≈ consommation annuelle (ratio ~1). Le kWc « en plus pour la revente » détruit désormais de la valeur (surplus payé 1,1 c€). Repères issus de simulations : 3 kWc pour un couple actif (4 500 kWh), 4 kWc pour des retraités présents (6 000 kWh), 6 kWc pour une famille avec clim/piscine (8 500 kWh), 9 kWc pour une famille PAC+VE (13 500 kWh). Et si personne n'est présent en journée sans usages pilotables : le PV peut ne plus se justifier du tout — à vérifier avant d'investir.

## 21. SOBRY & tarification dynamique (partenaire)

### Q: Qui est SOBRY ?
`cat: achat_energie | tags: sobry, fournisseur | verif: offre`
R: SOBRY (sobry.co) est un fournisseur français d'électricité à tarification dynamique : le prix du kWh suit le marché de gros EPEX SPOT heure par heure, sans marge sur le kWh — SOBRY se rémunère uniquement par l'abonnement fixe. Deux offres : SoCap (avec plafond mensuel garanti contre les flambées) et SoFlex (optimisation maximale). Sans engagement, compteur Linky requis, prix du lendemain publiés chaque jour (app + WhatsApp), API publique (intégration Home Assistant). SOBRY est partenaire d'HELIOS : si Helios vous propose une étude, il vous donnera son avis indépendant sur les résultats — y compris s'il est négatif.

### Q: Le tarif dynamique SOBRY est-il fait pour moi ?
`cat: achat_energie | tags: sobry, profil`
R: Profils gagnants : usages pilotables (VE, ballon, PAC, batterie), présence ou pilotage à distance, et idéalement du PV (charger/consommer aux heures solaires bon marché, parfois à prix négatif). Profils à risque : chauffage électrique non pilotable (exposition aux pointes d'hiver). Le test est simple et sans engagement : votre PDL suffit pour une estimation précise sur votre courbe de charge réelle — Helios peut lancer l'étude avec votre accord et analyser le résultat avec vous.
