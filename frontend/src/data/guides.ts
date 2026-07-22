// Guides & Aides — BROUILLONS rédigés à partir des fiches validées de la base de
// connaissances (mêmes chiffres que la FAQ / le chat, aucun chiffre inventé).
// À RELIRE par l'équipe avant mise en ligne publique : ton, montants marqués
// « à vérifier », et compléments éventuels. Un guide relu = retirer cette mention.

export interface GuideSection {
  titre: string
  contenu: string // Markdown léger (paragraphes séparés par des sauts de ligne)
}

export interface Guide {
  slug: string
  titre: string
  categorie: string
  chapo: string
  aVenir?: boolean // true tant que le contenu n'est pas rédigé
  sections: GuideSection[]
}

export const guides: Guide[] = [
  {
    slug: 'par-ou-commencer',
    titre: 'Par où commencer sa rénovation énergétique ?',
    categorie: 'Rénovation',
    chapo: 'La bonne méthode : sobriété, puis isolation, puis systèmes, puis production. On vous explique pourquoi cet ordre.',
    sections: [
      {
        titre: 'Les gestes gratuits d\'abord',
        contenu:
          'Avant de dépenser un euro, commencez par ce qui ne coûte rien. Baisser la consigne de chauffage de 1 °C, c\'est environ 7 % de consommation en moins — gratuit et immédiat. Les repères qui marchent : 19 °C dans les pièces de vie, 17 °C dans les chambres, 16 °C en absence.\n\n' +
          'En absence de journée, réduisez de 2 à 3 °C plutôt que d\'éteindre : couper totalement oblige à une relance coûteuse et refroidit les murs. Au-delà de 48 h d\'absence, passez en mode hors gel.\n\n' +
          'Un thermostat programmable (60 à 250 €, ou 200 à 500 € posé pour un modèle connecté avec sondes) automatise ces réductions la nuit et en absence : 10 à 15 % d\'économies de chauffage à la clé.',
      },
      {
        titre: 'Isoler avant tout',
        contenu:
          'Dans une maison non isolée, la chaleur s\'échappe partout, mais pas uniformément : toiture 25–30 %, murs 20–25 %, renouvellement d\'air et fuites 20–25 %, fenêtres 10–15 %, planchers 7–10 %.\n\n' +
          'C\'est pourquoi on commence presque toujours par les combles : c\'est le poste de pertes le plus important et le chantier au meilleur rapport coût/efficacité. Changer les fenêtres en premier, à l\'inverse, est rarement le bon calcul : c\'est le chantier le plus cher pour l\'un des postes de pertes les plus faibles.\n\n' +
          'La règle d\'or : on isole AVANT de changer le chauffage. Un chauffage dimensionné pour une passoire devient surdimensionné (et surcoûté) une fois la maison isolée.',
      },
      {
        titre: 'Choisir son chauffage',
        contenu:
          'Une fois l\'enveloppe traitée, le chauffage. La pompe à chaleur s\'impose souvent : elle prélève des calories dans l\'air ou le sol, et restitue 3 à 4 kWh de chaleur pour 1 kWh d\'électricité consommé (c\'est le COP). En remplacement d\'un fioul ou d\'un électrique direct, la facture de chauffage peut être divisée par 2 à 3.\n\n' +
          'Mais ce n\'est pas automatique : dans une maison mal isolée ou en région très froide, les performances chutent. D\'où l\'ordre : isolation d\'abord, systèmes ensuite.',
      },
      {
        titre: 'Et le solaire ?',
        contenu:
          'La production arrive en dernier — non parce qu\'elle est accessoire, mais parce qu\'elle se dimensionne sur une consommation déjà optimisée. Depuis la réforme 2026, la règle est simple : produire environ ce que l\'on consomme (le surplus revendu ne rapporte presque plus rien).\n\n' +
          'Isoler et sobriser d\'abord, c\'est donc aussi payer son installation solaire moins cher, car mieux dimensionnée. La boucle est bouclée : sobriété → isolation → systèmes → production. C\'est la hiérarchie du colibri, et elle est dans cet ordre pour de bonnes raisons.',
      },
    ],
  },
  {
    slug: 'maprimerenov',
    titre: 'MaPrimeRénov\' : comment ça marche ?',
    categorie: 'Aides',
    chapo: 'Le principe de l\'aide, qui peut en bénéficier, et comment la demander. Montants à vérifier chaque année.',
    sections: [
      {
        titre: 'Qui peut en bénéficier ?',
        contenu:
          'MaPrimeRénov\' distingue quatre profils selon le revenu fiscal de référence et la composition du foyer : Bleu (très modestes), Jaune (modestes), Violet (intermédiaires) et Rose (aisés). Plus le profil est modeste, plus l\'aide est élevée.\n\n' +
          'Les plafonds de ressources 2026 ont été légèrement relevés (environ 1 %). Pour connaître votre profil, une seule référence fiable : le simulateur officiel sur france-renov.gouv.fr.',
      },
      {
        titre: 'Pour quels travaux ?',
        contenu:
          'Le guichet a rouvert le 23 février 2026 pour tous les parcours. Mais les règles ont bougé, et pas dans le détail : le plafond de la rénovation d\'ampleur est passé de 70 000 à 40 000 € HT (avec un saut de 3 classes énergétiques exigé), les chaudières biomasse et l\'isolation des murs sont sorties du parcours « par geste », et les primes bois ont baissé.\n\n' +
          'Concrètement : l\'isolation des murs seule n\'est plus aidée — elle ne l\'est qu\'au sein d\'une rénovation d\'ampleur. Vérifiez toujours la règle en vigueur avant de vous engager, elle change chaque année.',
      },
      {
        titre: 'Comment faire sa demande',
        contenu:
          'Trois réflexes qui évitent les mauvaises surprises. Un : la demande se fait AVANT de signer le devis — des travaux commencés trop tôt perdent l\'aide. Deux : l\'artisan doit être RGE (Reconnu Garant de l\'Environnement), sans quoi l\'aide est refusée. Trois : anticipez les délais — l\'instruction peut prendre jusqu\'à 6 mois pour les rénovations d\'ampleur.\n\n' +
          'Pensez aussi aux CEE (certificats d\'économies d\'énergie) : ces primes versées par les fournisseurs d\'énergie sont cumulables avec MaPrimeRénov\'. Leur montant varie fortement selon les opérateurs : comparez les offres avant de signer, et là aussi, demande avant travaux.',
      },
    ],
  },
  {
    slug: 'isolation-combles',
    titre: 'Isoler ses combles : le meilleur rapport coût/efficacité',
    categorie: 'Isolation',
    chapo: 'Jusqu\'à 30 % des pertes de chaleur passent par la toiture. Souvent le premier chantier à envisager.',
    sections: [
      {
        titre: 'Pourquoi commencer par les combles',
        contenu:
          'L\'air chaud monte : dans une maison non isolée, 25 à 30 % de la chaleur s\'échappe par la toiture — le premier poste de pertes. C\'est aussi, heureusement, le chantier le moins cher au m² traité. Ce cumul (grosses pertes, petit coût) en fait le point de départ presque systématique d\'une rénovation.',
      },
      {
        titre: 'Combles perdus ou aménagés',
        contenu:
          'Pour des combles perdus (non habités), la technique reine est le soufflage : de la laine de verre, de la laine de roche ou de la ouate de cellulose est projetée sur le plancher des combles, sur 30 à 40 cm pour atteindre une résistance thermique R ≥ 7. Chantier rapide, souvent une demi-journée.\n\n' +
          'Pour des combles aménagés, on isole sous rampants (entre et sous les chevrons) — plus cher et plus technique, car il faut préserver la ventilation de la couverture et l\'étanchéité à l\'air.',
      },
      {
        titre: 'Ordres de grandeur de coût',
        contenu:
          'Pour des combles perdus par soufflage : comptez 25 à 50 €/m² pose comprise. L\'économie attendue : 15 à 25 % sur le chauffage. Résultat : le chantier est souvent amorti en moins de 5 ans — un temps de retour rare en rénovation énergétique.\n\n' +
          'Ces chiffres sont des ordres de grandeur 2026, à affiner avec des devis. Helios peut vous aider à les comparer — et un devis correct doit préciser l\'isolant, l\'épaisseur et le R visé.',
      },
    ],
  },
  {
    slug: 'pompe-a-chaleur',
    titre: 'La pompe à chaleur, pour qui ?',
    categorie: 'Chauffage',
    chapo: 'Une PAC bien dimensionnée dans une maison bien isolée peut diviser la facture de chauffage. Les conditions à réunir.',
    sections: [
      {
        titre: 'Le principe',
        contenu:
          'Une pompe à chaleur ne « crée » pas de chaleur : elle en déplace. Elle prélève des calories dans l\'air extérieur (ou le sol) et les restitue dans le logement. Son rendement se mesure au COP : un COP de 3 à 4 signifie que 1 kWh d\'électricité consommé produit 3 à 4 kWh de chaleur.\n\n' +
          'Point de vigilance : le COP baisse quand il fait très froid. Dans les régions froides, vérifiez les performances annoncées à -7 °C, pas seulement la valeur en conditions idéales.',
      },
      {
        titre: 'Isoler d\'abord',
        contenu:
          'Une PAC dans une passoire thermique, c\'est une grosse PAC qui tourne fort par grand froid — là où son rendement est le plus mauvais. Isoler d\'abord permet d\'installer une machine plus petite, moins chère, qui travaille dans sa meilleure plage. C\'est LA condition d\'une PAC réussie.',
      },
      {
        titre: 'Air/eau ou air/air ?',
        contenu:
          'La PAC air-eau alimente des radiateurs à eau ou un plancher chauffant, et peut produire l\'eau chaude sanitaire. Ordre de grandeur : 10 000 à 18 000 € pose comprise. En remplacement d\'un fioul ou d\'un électrique direct, la facture de chauffage peut être divisée par 2 à 3, avec MaPrimeRénov\' et les CEE « Coup de pouce » en soutien selon vos revenus.\n\n' +
          'La PAC air-air (climatisation réversible) souffle de l\'air chaud ou froid : 2 000 à 5 000 € par unité posée, très efficace en mi-saison et régions tempérées, et elle rafraîchit l\'été. Ses limites : pas d\'eau chaude sanitaire, des aides très réduites, et un confort de soufflage inférieur aux radiateurs à eau. Excellent complément — ou solution principale dans le Sud.',
      },
    ],
  },
  {
    slug: 'autoconsommation-solaire',
    titre: 'Autoconsommation solaire : les bases',
    categorie: 'Solaire',
    chapo: 'Produire son électricité et la consommer sur place. Ce que ça change sur la facture, et comment bien dimensionner.',
    sections: [
      {
        titre: 'Autoconsommer, c\'est quoi',
        contenu:
          'Autoconsommer, c\'est consommer sa propre production solaire au moment où elle est produite, au lieu d\'acheter cette électricité au réseau. Chaque kWh autoconsommé est un kWh non facturé — c\'est là que se joue la rentabilité.\n\n' +
          'Repère de production : 1 kWc installé produit selon la région 900 à 1 100 kWh/an au nord, 1 200 à 1 450 kWh/an au sud. Une installation de 3 kWc produit donc environ 2 700 à 4 300 kWh/an — à comparer à votre consommation.',
      },
      {
        titre: 'Bien dimensionner son installation',
        contenu:
          'Depuis la réforme 2026, la règle a changé : le surplus revendu ne rapporte presque plus rien (environ 1 centime le kWh). Le bon dimensionnement vise donc production ≈ consommation annuelle, pas plus.\n\n' +
          'Repères issus de simulations : 3 kWc pour un couple actif (~4 500 kWh/an), 4 kWc pour des retraités présents en journée (~6 000 kWh), 6 kWc pour une famille avec clim ou piscine (~8 500 kWh), 9 kWc pour une famille PAC + voiture électrique (~13 500 kWh).\n\n' +
          'Et une vérité qui fâche, mais Helios est là pour ça : si personne n\'est présent en journée et qu\'aucun usage n\'est pilotable, le photovoltaïque peut ne pas se justifier du tout. Une installation 3 kWc coûte environ 7 000 à 9 000 € posée et s\'amortit en 8 à 12 ans quand la maison est bien orientée — à condition d\'autoconsommer suffisamment.',
      },
      {
        titre: 'Avec ou sans batterie',
        contenu:
          'Sans rien faire, un foyer autoconsomme typiquement ~30 % de sa production. Le levier le moins cher pour monter à 50–70 % n\'est pas la batterie, c\'est le pilotage : chauffe-eau déclenché en journée (un routeur solaire coûte 150 à 500 € — le « stockage » le moins cher qui soit), lave-linge et lave-vaisselle programmés, recharge du véhicule en journée.\n\n' +
          'La batterie physique (4 000 à 8 000 €) monte l\'autoconsommation à 60–80 %, mais sa rentabilité reste souvent limite en 2026. Notre conseil franc : pilotez d\'abord, stockez ensuite — et seulement si les chiffres de VOTRE profil le justifient. Le simulateur solaire d\'Helios fait ce calcul avec vous.',
      },
    ],
  },
  {
    slug: 'bien-acheter-energie',
    titre: 'Payer son électricité au meilleur prix',
    categorie: 'Énergie',
    chapo: 'Puissance souscrite, heures creuses, tarif dynamique : les leviers pour ne pas payer trop cher.',
    sections: [
      {
        titre: 'Ajuster sa puissance souscrite',
        contenu:
          'Beaucoup de foyers paient chaque mois un abonnement surdimensionné. Les repères : 6 kVA suffisent souvent sans chauffage électrique, 9 kVA avec chauffage électrique ou une PAC modeste, 12 kVA et plus pour un foyer tout-électrique avec voiture.\n\n' +
          'Le test est simple : si votre compteur ne disjoncte jamais et que la puissance maximale relevée (visible sur le Linky, rubrique conso) reste bien sous votre seuil, descendre d\'un cran économise 30 à 60 €/an. C\'est l\'un des rares gains totalement sans effort.',
      },
      {
        titre: 'Heures pleines / heures creuses',
        contenu:
          'L\'option heures creuses n\'est intéressante que si vous déplacez réellement des usages : en règle générale, il faut passer 25 à 30 % de sa consommation en heures creuses pour être gagnant. Avec un ballon d\'eau chaude électrique ou une borne de recharge, c\'est presque toujours le cas ; sans usage déplaçable, l\'option coûte plus cher qu\'elle ne rapporte.\n\n' +
          'À suivre : les plages d\'heures creuses évoluent, avec davantage d\'heures en journée pour suivre la production solaire. Un changement qui peut rebattre les cartes pour les foyers équipés.',
      },
      {
        titre: 'Le tarif dynamique, pour qui',
        contenu:
          'Avec une offre à tarification dynamique, le prix du kWh suit le marché heure par heure (les prix sont connus la veille). Les creux solaires de mi-journée et les nuits sont souvent très bon marché ; les pointes d\'hiver (8h-13h, 18h-20h) peuvent être chères.\n\n' +
          'C\'est rentable pour les foyers pilotables — voiture électrique, ballon, batterie, PAC programmable — qui déplacent leur consommation vers les heures creuses. C\'est risqué pour un chauffage électrique non pilotable, qui consomme précisément aux heures chères. Compteur Linky requis.\n\n' +
          'Avant tout changement de contrat, un réflexe : le comparateur public et indépendant energie-info.fr. Helios peut vous donner un avis sur votre situation — et il vous dira aussi quand il vaut mieux ne rien changer.',
      },
    ],
  },
  {
    slug: 'locataire-reduire-factures',
    titre: 'Locataire : quels leviers pour réduire ses factures ?',
    categorie: 'Locataire',
    chapo: 'Pas de travaux lourds à votre main, mais des leviers réels — et un rapport de force qui a changé avec la réglementation.',
    sections: [
      {
        titre: 'Ce qui dépend entièrement de vous',
        contenu:
          'Tous les gestes de sobriété restent à votre portée sans demander la permission à personne : régler le thermostat, ne pas surchauffer, poser des mousseurs sur les robinets, calfeutrer provisoirement une fenêtre qui coulisse mal. Ce sont les mêmes gestes qui font gagner 10 à 15 % sur le chauffage dans n\'importe quel logement, propriétaire ou non.',
      },
      {
        titre: 'Ce que le propriétaire ne peut plus ignorer',
        contenu:
          'Le rapport de force a changé : un logement classé G ne peut plus être mis en location depuis 2025, les F suivront en 2028, les E en 2034. Si votre logement est une passoire thermique, votre loyer est déjà gelé — un point à connaître si votre bailleur en évoque une hausse. Signaler par écrit (lettre recommandée) un logement énergivore n\'est pas un caprice : c\'est rappeler une obligation légale qui pèse de plus en plus sur le propriétaire, pas sur vous.',
      },
      {
        titre: 'Meublé ou nu, même règle',
        contenu:
          'Le DPE et le calendrier d\'interdiction des passoires thermiques s\'appliquent de la même façon, que la location soit meublée ou nue — c\'est le logement qui est concerné, pas le type de bail. Ne vous laissez pas dire le contraire. Pour de petits travaux à vos frais (comme une meilleure isolation d\'un tuyau ou un rideau thermique), aucune autorisation n\'est nécessaire tant que vous ne touchez pas à la structure du logement.',
      },
    ],
  },
  {
    slug: 'copropriete-travaux-collectifs',
    titre: 'Copropriété : lancer des travaux énergétiques collectifs',
    categorie: 'Copropriété',
    chapo: 'ITE, chaudière collective, toiture : ces travaux se décident à plusieurs. Voici comment enclencher le mouvement.',
    sections: [
      {
        titre: 'Individuel ou collectif : la première question',
        contenu:
          'Vos travaux privatifs (chauffage individuel, parfois les fenêtres selon le règlement) ne nécessitent généralement pas de vote. Mais tout ce qui touche l\'aspect extérieur ou les parties communes — isolation par l\'extérieur, panneaux solaires en toiture commune, chaudière collective — doit passer en assemblée générale. Vérifiez d\'abord le règlement de copropriété : il précise ce qui relève de votre lot et ce qui est commun.',
      },
      {
        titre: 'DTG et plan pluriannuel : les bons outils',
        contenu:
          'Le diagnostic technique global (DTG) est un état des lieux complet de l\'immeuble — structure, équipements, performance énergétique. Il sert souvent de base à un plan pluriannuel de travaux (PPT), obligatoire pour certaines copropriétés selon leur taille, qui budgétise et planifie les rénovations sur plusieurs années. Faire réaliser un DTG, même quand ce n\'est pas obligatoire, est le meilleur point de départ pour convaincre en assemblée générale : on discute sur des chiffres, pas des impressions.',
      },
      {
        titre: 'Convaincre en assemblée générale',
        contenu:
          'MaPrimeRénov\' Copropriété existe spécifiquement pour financer les travaux collectifs — un argument à mettre en avant, car il change la perception du coût pour des copropriétaires souvent réticents. Un chauffage collectif au gaz vieillissant, un immeuble mal isolé : ce sont des arguments concrets (confort, charges, valeur des lots) qui parlent davantage qu\'un discours écologique général. Patience nécessaire : ce chantier se joue sur plusieurs assemblées, pas une seule.',
      },
    ],
  },
  {
    slug: 'comprendre-son-dpe',
    titre: 'Comprendre son DPE, ligne par ligne',
    categorie: 'DPE',
    chapo: 'De A à G, ce que dit vraiment l\'étiquette — et ce qu\'elle change concrètement pour vous.',
    sections: [
      {
        titre: 'Ce que mesure le DPE',
        contenu:
          'Le Diagnostic de Performance Énergétique classe un logement de A à G selon sa consommation d\'énergie et ses émissions. Il est opposable depuis 2021 (vous pouvez vous retourner contre un DPE erroné), obligatoire pour vendre ou louer, et valable 10 ans. Sa fiabilité s\'est améliorée avec la réforme, mais des écarts subsistent d\'un diagnostiqueur à l\'autre — Helios peut vous aider à interpréter le vôtre et à identifier les travaux qui font vraiment gagner des classes.',
      },
      {
        titre: 'F ou G : ce qui change dès maintenant',
        contenu:
          'Un logement classé G ne peut plus être mis en location depuis janvier 2025 ; les F suivront en janvier 2028, les E en janvier 2034. Les loyers des F et G sont déjà gelés. Pour la vente, un audit énergétique réglementaire (plus poussé qu\'un simple DPE) est obligatoire pour les maisons individuelles classées F ou G, et désormais E aussi. Ce DPE pèse également sur le prix : plusieurs études notariales montrent une décote pour les logements mal classés, et son absence dans une annonce ou une vente peut engager la responsabilité du vendeur.',
      },
      {
        titre: 'Faire progresser son étiquette',
        contenu:
          'Les postes qui font gagner le plus de classes, dans l\'ordre où Helios les recommande : isolation (combles en priorité, puis murs et fenêtres), puis système de chauffage adapté à un logement désormais bien isolé. Un audit énergétique réglementaire vous donnera une feuille de route chiffrée par un professionnel certifié — Helios ne remplace pas ce document mais vous aide à le préparer et à comprendre ses préconisations.',
      },
    ],
  },
  {
    slug: 'devis-renovation-pieges',
    titre: 'Devis de rénovation : ce qu\'il ne faut jamais accepter',
    categorie: 'Chantier',
    chapo: 'Les mentions obligatoires, l\'acompte raisonnable, et les signaux qui doivent vous faire fuir.',
    sections: [
      {
        titre: 'Ce qu\'un devis doit obligatoirement contenir',
        contenu:
          'Identité et SIRET de l\'entreprise, assurance décennale avec les coordonnées de l\'assureur, détail des prestations et quantités (pas juste un prix global), prix HT et TTC avec le taux de TVA applicable, durée de validité de l\'offre, et la mention de la qualification RGE si vos aides en dépendent. Sans décennale vérifiable, ne signez pas — c\'est la garantie qui vous protège pendant 10 ans sur le gros œuvre.',
      },
      {
        titre: 'Comparer à périmètre égal',
        contenu:
          'Le devis le moins cher n\'est pas toujours comparable à un autre : vérifiez la marque et le modèle du matériel, les performances annoncées (résistance thermique R, COP d\'une PAC, coefficient Uw d\'une fenêtre), la surface réellement traitée, la préparation et les finitions incluses, et les garanties. Demandez systématiquement 3 devis minimum et exigez les fiches techniques — un professionnel sérieux n\'a aucune raison de les refuser.',
      },
      {
        titre: 'Acompte, signature, et malfaçons',
        contenu:
          'Un acompte raisonnable se situe entre 10 et 30 % à la commande, jamais plus de 50 % avant le début effectif du chantier. Si votre plan de financement dépend d\'une aide comme MaPrimeRénov\', attendez l\'accord écrit avant de signer. En cas de malfaçon : réception avec réserves écrites, puis garantie de parfait achèvement (1 an, tout défaut signalé), biennale (2 ans, équipements) et décennale (10 ans, gros ouvrage). Le démarchage téléphonique pour la rénovation énergétique est interdit — une offre à « 1 € », une pression à signer le jour même ou un crédit intégré sans y avoir pensé sont des signaux d\'alarme.',
      },
    ],
  },
  {
    slug: 'apres-le-preaudit',
    titre: 'Après un pré-audit Helios : les premières actions concrètes',
    categorie: 'Rénovation',
    chapo: 'Le pré-audit vous donne une feuille de route. Voici comment la transformer en premières décisions, sans se disperser.',
    sections: [
      {
        titre: 'Relire dans l\'ordre, pas par enthousiasme',
        contenu:
          'Le pré-audit priorise vos postes de travaux selon la hiérarchie sobriété → isolation → systèmes → production — pas selon ce qui vous fait le plus envie. Il est tentant de vouloir commencer par le solaire ou une nouvelle PAC parce que c\'est plus visible et plus gratifiant : résistez, ce sont presque toujours les postes les moins rentables à traiter en premier tant que l\'enveloppe n\'est pas traitée.',
      },
      {
        titre: 'Les gestes gratuits, cette semaine',
        contenu:
          'Avant tout devis, appliquez ce qui ne coûte rien et se fait en un après-midi : réglages de thermostat, programmation des plages d\'absence, purge des radiateurs, vérification des joints de fenêtres. Ce sont des économies immédiates qui financeront une partie de vos travaux futurs, et qui vous donnent une vraie mesure de votre consommation « plancher » avant travaux.',
      },
      {
        titre: 'Le premier devis à demander',
        contenu:
          'Sur la base du poste de déperdition le plus important identifié par votre pré-audit (souvent la toiture), demandez 3 devis à des artisans RGE avant toute autre démarche. C\'est ce premier chantier qui conditionne le dimensionnement de tout le reste : un chauffage ou une installation solaire dimensionnés après l\'isolation seront plus petits, moins chers et mieux adaptés. Utilisez ensuite le chat Helios pour faire relire vos devis avant de signer.',
      },
    ],
  },
  {
    slug: 'produire-son-eau',
    titre: 'Produire son eau chez soi : le guide de l\'eau atmosphérique',
    categorie: 'Eau',
    chapo: 'Un générateur qui transforme l\'humidité de l\'air en eau potable. Ce que ça change, et pour qui c\'est pertinent.',
    sections: [
      {
        titre: 'Le principe, en quatre étapes',
        contenu:
          'Un générateur d\'eau atmosphérique capte l\'humidité de l\'air ambiant, la condense en eau (le même principe physique qu\'un déshumidificateur), filtre et purifie cette eau, puis en vérifie la qualité. Plus l\'air est chaud et humide, plus la production est élevée — la quantité produite dépend donc fortement de votre climat local, pas seulement du modèle choisi.',
      },
      {
        titre: 'Boisson et cuisine, pas la douche',
        contenu:
          'Soyons francs : l\'eau du réseau reste imbattable en prix pour la douche, les toilettes ou le lave-linge. L\'eau atmosphérique se positionne sur l\'eau de boisson et de cuisine, là où elle remplace avantageusement l\'eau en bouteille — moins de déchets plastiques, pas de transport, une eau dont vous pouvez vérifier vous-même la potabilité grâce au kit de certification fourni avec l\'appareil.',
      },
      {
        titre: 'Coupler avec le solaire',
        contenu:
          'Produire de l\'eau à partir de l\'air consomme de l\'électricité — c\'est le principal poste de coût en fonctionnement. La solution prend tout son sens couplée à une production solaire : l\'appareil tourne en journée quand vos panneaux produisent, et votre surplus solaire devient de l\'eau potable plutôt que d\'être revendu pour presque rien. Utilisez le simulateur « Mon potentiel hydrique » d\'Helios pour estimer la production réaliste selon votre ville avant toute décision.',
      },
    ],
  },
  {
    slug: 'vehicule-electrique-guide',
    titre: 'Véhicule électrique : recharge et aides, le guide complet',
    categorie: 'Mobilité',
    chapo: 'Borne à domicile, recharge solaire, aides à l\'achat : les questions qui reviennent le plus.',
    sections: [
      {
        titre: 'Installer une borne chez soi',
        contenu:
          'Une borne de recharge à domicile (wallbox) sécurise et accélère la recharge par rapport à une simple prise domestique. Le budget dépend de la puissance choisie et de la complexité de l\'installation électrique existante — un point que votre électricien doit valider en amont, notamment si votre puissance souscrite est déjà proche de sa limite.',
      },
      {
        titre: 'Recharger avec ses panneaux solaires',
        contenu:
          'C\'est l\'un des meilleurs usages du solaire : recharger le véhicule en journée avec sa propre production augmente fortement l\'autoconsommation et réduit le coût au kilomètre, bien davantage qu\'en revendant ce même surplus au réseau. Avec un pilotage intelligent (recharge programmée sur les heures de production) ou une batterie, l\'effet est encore meilleur. La maison devient, à son échelle, une petite station de recharge alimentée par le soleil.',
      },
      {
        titre: 'Les aides à l\'achat, à vérifier au cas par cas',
        contenu:
          'Deux dispositifs principaux existent, cumulables sous conditions : le bonus écologique (aide directe à l\'achat d\'un véhicule électrique neuf, sous plafond de prix et de revenus) et la prime à la conversion (versée en échange de la mise au rebut d\'un vieux véhicule polluant). Les montants et conditions changent chaque année et selon votre revenu fiscal de référence — vérifiez toujours sur service-public.fr avant d\'acheter, sans vous fier au chiffre annoncé par le vendeur.',
      },
    ],
  },
  {
    slug: 'comprendre-revolt',
    titre: 'Simulateur Revolt : bien interpréter vos résultats',
    categorie: 'Énergie',
    chapo: 'Panneaux, batterie physique ou virtuelle, tarif fixe ou dynamique : comment lire un comparatif Revolt sans se tromper.',
    sections: [
      {
        titre: 'À consommation réelle égale',
        contenu:
          'Contrairement au simulateur solaire classique qui raisonne en moyennes annuelles, Revolt simule heure par heure sur une année complète, à partir d\'une courbe de consommation (aujourd\'hui simulée selon votre profil, demain issue d\'Enedis avec votre consentement). C\'est ce qui permet de comparer plusieurs scénarios sur une base identique : ajouter des panneaux seuls, y ajouter une batterie, ou changer de tarif — sans que la consommation elle-même ne varie d\'un scénario à l\'autre.',
      },
      {
        titre: 'Batterie physique ou virtuelle : deux logiques différentes',
        contenu:
          'Une batterie physique augmente votre autoconsommation immédiatement mais représente un investissement matériel qui prend du temps à s\'amortir. Le stockage virtuel (comme MyLight) évite cet investissement — vous « mettez de côté » votre surplus solaire pour le récupérer plus tard, moyennant un abonnement et des frais de restitution — mais impose souvent de changer de fournisseur d\'électricité. Aucune des deux n\'est meilleure dans l\'absolu : Revolt compare les deux sur VOTRE profil.',
      },
      {
        titre: 'SoFlex, SoCap ou tarif fixe',
        contenu:
          'Un tarif dynamique comme SoFlex suit le marché heure par heure, avec des creux très bon marché (parfois négatifs) aux heures de forte production solaire nationale, mais des pointes plus chères en hiver. SoCap suit la même logique en version plafonnée, moins risquée mais moins généreuse aux heures creuses. Ces grilles restent des grilles de test à confirmer auprès de SOBRY — utilisez Revolt pour comprendre l\'ordre de grandeur de l\'écart avec votre tarif actuel, pas comme un devis final.',
      },
    ],
  },
]

export const guideCategories = Array.from(new Set(guides.map((g) => g.categorie)))
