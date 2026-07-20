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
]

export const guideCategories = Array.from(new Set(guides.map((g) => g.categorie)))
