/**
 * Le contenu de la page « Le soleil » (`pages/Soleil.tsx`).
 *
 * POURQUOI UN FICHIER DE DONNÉES ET PAS TOUT DANS LA PAGE : le sujet est vaste — matériel,
 * pose, garanties, dossier administratif, entreprise, stockage, marché, empreinte. Écrit
 * dans le composant, il aurait noyé la mise en page sous huit cents lignes de texte. Ici le
 * texte se relit et se corrige sans toucher au rendu, comme `data/piliers.json` ou
 * `data/glossaire.ts`.
 *
 * D'OÙ VIENNENT LES CHIFFRES. Rien n'est inventé ici :
 *  - base de connaissances d'Helios (`kb/*.md`, servie par `/api/faq`) pour le matériel,
 *    le dimensionnement, les contrats, l'urbanisme et le stockage ;
 *  - étude technico-économique interne de juin 2026 (`KB/KB-stockage-pv-2026.md`) pour les
 *    coûts actualisés du stockage et le cadre tarifaire post-réforme ;
 *  - dossiers de synthèse réels d'un installateur pour la séquence d'un chantier et les
 *    durées de garantie usuelles ;
 *  - Soren (filière de reprise) et le bilan électrique RTE 2025 pour le recyclage et le
 *    carbone, relevés le 05/10/2026.
 *
 * LA RÈGLE DE LA CONSTITUTION TENUE ICI : aucune marque n'est recommandée, aucun chiffre
 * n'est présenté comme certain, et la section sur l'entreprise donne au visiteur les
 * critères que nous appliquons à nos partenaires — pour qu'il puisse les appliquer à
 * n'importe qui, y compris à nous.
 */

import {
  Award, BatteryCharging, Building2, Cable, CalendarClock, CircleDollarSign, ClipboardCheck,
  Cpu, FileCheck2, FileSignature, Gauge, Hammer, HardHat, Landmark, Layers, Leaf,
  type LucideIcon, Plug, PlugZap, Recycle, Ruler, ScanSearch, ShieldCheck, Siren, Sun,
  TrendingUp, Users, Wrench, Zap,
} from 'lucide-react'

/* ------------------------------------------------------------------ Les types */

export type Onglet = 'materiel' | 'pose' | 'garanties' | 'stockage' | 'marche'

/** Une petite carte : une icône, un titre court, trois lignes. Volontairement bref —
 *  le détail vit dans les dépliants juste en dessous. */
export interface Vignette {
  icon: LucideIcon
  titre: string
  texte: string
  /** Le mot à retenir, affiché en couleur sous le texte. Facultatif. */
  retenir?: string
}

/** Un dépliant : une question telle qu'on la pose vraiment, et sa réponse. */
export interface Deplie {
  q: string
  r: string
}

export interface Section {
  id: Onglet
  label: string
  Icone: LucideIcon
  /** La phrase affichée sous les onglets quand celui-ci est actif. */
  phrase: string
  /** Le ton de la section : décide la couleur des icônes de vignettes. */
  teinte: 'primary' | 'sky' | 'leaf' | 'terra'
  titreVignettes: string
  vignettes: Vignette[]
  titreDeplies: string
  deplies: Deplie[]
  /** Le parler-vrai de la section : ce qu'un vendeur ne dirait pas. */
  parlerVrai?: string
}

/* ------------------------------------------- Les conditions d'un projet réussi */

/** Le résumé de toute la page, en tête, pour qui n'ouvrira aucun onglet.
 *  Six conditions : ce sont celles qui reviennent dans tous les dossiers qui se
 *  sont bien passés, et dont l'absence explique la plupart de ceux qui se sont
 *  mal passés. */
export const CONDITIONS: { titre: string; texte: string }[] = [
  {
    titre: 'Une consommation mesurée, pas estimée',
    texte: 'Le relevé de votre compteur, heure par heure, avant toute proposition de '
      + 'puissance. Un dimensionnement bâti sur une facture annuelle est un pari.',
  },
  {
    titre: 'Une production calée sur cette consommation',
    texte: 'Depuis juin 2026, le surplus renvoyé au réseau vaut 1,1 centime le kWh. '
      + 'Couvrir le toit « pour revendre » n’a plus de sens.',
  },
  {
    titre: 'Des usages que vous pouvez déplacer',
    texte: 'Ballon d’eau chaude, voiture, piscine, pompe à chaleur. C’est ce qui '
      + 'transforme des kWh produits en kWh réellement consommés chez vous.',
  },
  {
    titre: 'Une toiture et un tableau en état',
    texte: 'Étanchéité, charpente, mise à la terre. Ce qui se répare avant la pose coûte '
      + 'une fraction de ce que ça coûte après, panneaux déposés.',
  },
  {
    titre: 'Un dossier administratif porté par l’installateur',
    texte: 'Mairie, Enedis, Consuel. Ce sont trois dossiers distincts, et vous ne devriez '
      + 'en monter aucun vous-même.',
  },
  {
    titre: 'Une entreprise que vous pouvez vérifier',
    texte: 'Assurance décennale à jour couvrant le photovoltaïque, qualifications, '
      + 'ancienneté. Une garantie de dix ans ne vaut que si l’entreprise vit dix ans.',
  },
]

/* ---------------------------------------------------------------- Les sections */

export const SECTIONS: Section[] = [
  /* ============================================================== 1. Matériel */
  {
    id: 'materiel',
    label: 'Le matériel',
    Icone: Layers,
    phrase: 'Ce qui se pose sur votre toit, et les trois lignes du devis qui méritent '
      + 'qu’on s’y arrête.',
    teinte: 'primary',
    titreVignettes: 'Ce qui compose une installation',
    vignettes: [
      {
        icon: Sun,
        titre: 'Les panneaux',
        texte: 'Un module courant fait aujourd’hui 400 à 500 Wc pour environ 1,9 m², soit un '
          + 'rendement de 20 à 23 %. La dégradation réellement constatée est de l’ordre de '
          + '0,3 à 0,5 % par an.',
        retenir: 'Devenu une commodité fiable',
      },
      {
        icon: Cpu,
        titre: 'L’onduleur, ou les micro-onduleurs',
        texte: 'Un onduleur central est plus simple et moins cher, mais un panneau à l’ombre '
          + 'pénalise toute la chaîne. Des micro-onduleurs coûtent 10 à 20 % de plus et '
          + 'rendent chaque panneau indépendant.',
        retenir: 'Ombrages ou plusieurs pans → micro',
      },
      {
        icon: Wrench,
        titre: 'Les fixations',
        texte: 'Crochets et rails choisis pour votre couverture — tuile, ardoise, bac acier — '
          + 'ou lestage et plots sur une terrasse. C’est la pièce qu’on ne voit jamais et qui '
          + 'tient tout pendant vingt-cinq ans.',
        retenir: 'Jamais le poste où économiser',
      },
      {
        icon: Cable,
        titre: 'Les protections électriques',
        texte: 'Coffrets de protection côté continu et côté alternatif, sectionneur, '
          + 'parafoudre selon l’exposition, et une mise à la terre refaite si besoin. '
          + 'La norme NF C 15-100 encadre tout cela.',
        retenir: 'Ce que le Consuel vient vérifier',
      },
      {
        icon: PlugZap,
        titre: 'Le pilotage',
        texte: 'Un routeur solaire envoie le surplus dans le ballon d’eau chaude plutôt qu’au '
          + 'réseau. Quelques centaines d’euros pour plusieurs points d’autoconsommation : '
          + 'c’est l’euro le mieux dépensé d’un projet solaire.',
        retenir: 'Avant la batterie, toujours',
      },
      {
        icon: Gauge,
        titre: 'Le suivi',
        texte: 'Une passerelle de mesure et son application : production, consommation, '
          + 'autoconsommation réelle. Sans elle, vous ne saurez jamais si votre installation '
          + 'tient ses promesses.',
        retenir: 'Vérifiez qu’il est inclus, et gratuit',
      },
    ],
    titreDeplies: 'Les questions qu’on se pose devant un devis',
    deplies: [
      {
        q: 'Faut-il choisir une marque de panneau en particulier ?',
        r: 'Non, et c’est une bonne nouvelle. Les écarts de rendement entre marques sérieuses '
          + 'se jouent à un ou deux points, invisibles sur votre facture. Regardez plutôt trois '
          + 'choses, écrites noir sur blanc : la garantie produit (25 ans est le standard, '
          + '30 chez certains), la garantie de rendement et son pourcentage de fin de période, '
          + 'et l’ancienneté du fabricant — une garantie de 25 ans n’engage que ceux qui '
          + 'existeront encore. Ce qui fait vraiment la différence entre deux installations au '
          + 'même prix, c’est la pose, pas le logo sur le panneau.',
      },
      {
        q: 'Comment se décompose le prix d’une installation ?',
        r: 'Pour une installation posée, les ordres de grandeur sont stables : les panneaux '
          + 'représentent environ 30 % du total, l’onduleur ou les micro-onduleurs 15 à 20 %, '
          + 'la structure et le câblage autour de 10 %, et la main-d’œuvre avec les démarches '
          + 'administratives 30 à 40 %. Autrement dit, la moitié de ce que vous payez n’est pas '
          + 'du matériel. C’est pour cela qu’un devis très bas sur un matériel équivalent doit '
          + 'faire se demander ce qui a été retiré de la pose, des protections ou du dossier.',
      },
      {
        q: 'Micro-onduleurs ou onduleur central : comment trancher ?',
        r: 'La règle tient en une phrase : ombrages partiels ou panneaux répartis sur plusieurs '
          + 'orientations → micro-onduleurs ; toiture uniforme et dégagée → onduleur central. '
          + 'Un point budgétaire est souvent passé sous silence : un onduleur central dure '
          + 'généralement 10 à 15 ans, il faut donc prévoir son remplacement une fois dans la '
          + 'vie de l’installation, alors que les micro-onduleurs sont souvent garantis 20 à '
          + '25 ans. Demandez que ce remplacement soit chiffré dans la comparaison, sinon vous '
          + 'comparez deux choses différentes.',
      },
      {
        q: 'Que vérifier, ligne par ligne, sur la partie matériel du devis ?',
        r: 'La marque ET le modèle exact des panneaux comme de l’onduleur — « panneaux 500 W de '
          + 'marque européenne » n’est pas une référence, c’est une esquive. Le nombre exact de '
          + 'modules et de micro-onduleurs. Le plan de calepinage, c’est-à-dire l’implantation '
          + 'panneau par panneau sur votre toiture, et non une surface. Le type de fixation '
          + 'retenu pour votre couverture. Les durées de garantie, avec pour chacune ce qu’elle '
          + 'couvre. Et la mention du dossier administratif : mairie, Enedis, Consuel.',
      },
      {
        q: 'Que penser des kits à brancher sur une prise ?',
        r: 'Les kits de 300 à 800 W, entre 400 et 900 €, se déclarent simplement auprès '
          + 'd’Enedis et se rentabilisent souvent en 5 à 8 ans parce que tout est autoconsommé. '
          + 'Les limites sont nettes : pas d’aides, pas de valorisation du surplus, et une '
          + 'fixation comme une couverture d’assurance à vérifier sérieusement s’il est posé '
          + 'en hauteur. C’est une bonne porte d’entrée, en particulier pour un locataire — '
          + 'pas un substitut à une installation en toiture.',
      },
    ],
    parlerVrai: 'Un bon matériel mal posé donne une mauvaise installation ; un matériel '
      + 'honnête bien posé donne une bonne installation pendant vingt-cinq ans. Si vous ne '
      + 'devez arbitrer qu’une chose entre deux devis, arbitrez sur l’entreprise avant '
      + 'd’arbitrer sur la marque.',
  },

  /* =================================================================== 2. Pose */
  {
    id: 'pose',
    label: 'La pose et le dossier',
    Icone: HardHat,
    phrase: 'Six étapes, trois dossiers administratifs, et une seule chose à faire de votre '
      + 'côté : ouvrir la porte.',
    teinte: 'sky',
    titreVignettes: 'De la signature à la première production',
    vignettes: [
      {
        icon: ScanSearch,
        titre: '1. La visite technique',
        texte: 'Toiture et charpente, tableau électrique, ombrages relevés sur place, chemin '
          + 'de câbles. Elle valide — ou corrige — ce que l’étude supposait.',
        retenir: 'Avant la commande, pas après',
      },
      {
        icon: Ruler,
        titre: '2. Le calepinage',
        texte: 'Le plan d’implantation panneau par panneau, orientation et nombre exacts. '
          + 'C’est la pièce qui engage l’installateur sur ce qu’il va réellement poser.',
        retenir: 'À exiger avec le devis définitif',
      },
      {
        icon: Landmark,
        titre: '3. La mairie',
        texte: 'Déclaration préalable dans la quasi-totalité des cas, instruction d’un mois — '
          + 'deux en secteur protégé, avec l’avis de l’architecte des bâtiments de France.',
        retenir: 'Le délai qui commande tout le reste',
      },
      {
        icon: Plug,
        titre: '4. Le raccordement',
        texte: 'Demande à Enedis et convention d’autoconsommation, avec ou sans injection du '
          + 'surplus. L’installateur agit par mandat de représentation.',
        retenir: 'Monté en parallèle de la mairie',
      },
      {
        icon: Hammer,
        titre: '5. Le chantier',
        texte: 'Un à trois jours selon la puissance et la couverture. Les deux points qui '
          + 'comptent vraiment : l’étanchéité à chaque traversée, et la mise à la terre.',
        retenir: 'La partie la plus courte du projet',
      },
      {
        icon: FileCheck2,
        titre: '6. Consuel et mise en service',
        texte: 'L’attestation de conformité visée par le Consuel, puis la mise en service par '
          + 'Enedis, et la prise en main de votre application de suivi.',
        retenir: 'C’est là que la production démarre',
      },
    ],
    titreDeplies: 'Ce que personne ne pense à demander',
    deplies: [
      {
        q: 'Combien de temps entre la signature et la première production ?',
        r: 'Comptez un ordre de grandeur de deux à quatre mois, et sachez d’où vient ce délai : '
          + 'presque entièrement de l’instruction en mairie et du raccordement, pas du chantier '
          + 'qui ne dure qu’un à trois jours. Un installateur qui vous promet « posé le mois '
          + 'prochain » parle de son planning de pose, pas de votre mise en service. En secteur '
          + 'protégé, ou si la mairie demande des pièces complémentaires, le délai s’allonge '
          + 'sans que personne n’y puisse rien — et c’est exactement pour cela que le dossier '
          + 'doit partir complet du premier coup.',
      },
      {
        q: 'Qui monte le dossier d’urbanisme, et que doit-il contenir ?',
        r: 'C’est à l’installateur de le faire, et c’est inclus dans les prix du marché. Le '
          + 'dossier de déclaration préalable comprend le formulaire, un plan de situation, un '
          + 'plan de masse, une vue de la toiture avec l’implantation des panneaux, un '
          + 'photomontage et une notice décrivant l’aspect. Vous signez un mandat qui '
          + 'l’autorise à déposer en votre nom. Demandez une copie du dossier déposé et du '
          + 'récépissé : c’est votre preuve de date, et le point de départ du délai '
          + 'd’instruction.',
      },
      {
        q: 'On me propose de poser sans rien déclarer. Qu’est-ce que je risque ?',
        r: 'Plus que ce qu’on vous laisse entendre, et la décharge qu’on vous fera signer ne '
          + 'vous protège pas : elle n’a aucune valeur face à la mairie, et elle n’engage pas '
          + 'votre assureur. Trois conséquences concrètes : l’administration peut exiger une '
          + 'remise en état, votre assurance habitation peut refuser sa garantie sur un ouvrage '
          + 'non déclaré en cas de sinistre, et le notaire posera la question à la revente — un '
          + 'acquéreur qui découvre une installation non déclarée négocie ou renonce. Une '
          + 'déclaration préalable coûte un timbre et un mois d’attente.',
      },
      {
        q: 'Étanchéité : qui garantit quoi, exactement ?',
        r: 'Sur une toiture en pente, l’installateur qui pose en surimposition devient '
          + 'responsable de l’étanchéité aux points qu’il traverse, et sa décennale doit le '
          + 'couvrir. Sur une toiture-terrasse, le sujet est plus délicat : si l’étanchéité '
          + 'existante est percée ou modifiée, deux entreprises se partagent la responsabilité, '
          + 'et c’est précisément là que naissent les litiges. La bonne pratique est simple — '
          + 'une pose lestée qui ne perce rien, ou un relevé d’étanchéité réalisé par un '
          + 'étancheur, avec par écrit qui garantit quoi. Si l’étanchéité est en fin de vie, '
          + 'on la refait avant : la reprendre sous les panneaux coûte bien plus cher.',
      },
      {
        q: 'Que faut-il vérifier le jour de la réception ?',
        r: 'Prenez le temps, c’est le seul moment où tout est encore ouvert. Vérifiez que '
          + 'l’implantation posée correspond au calepinage signé et que le nombre de panneaux '
          + 'est le bon. Faites-vous montrer le point de coupure d’urgence et expliquer la '
          + 'procédure. Demandez les attestations — conformité Consuel, décennale à jour — et '
          + 'la fiche de l’installation avec les références réelles du matériel posé. '
          + 'Connectez-vous à l’application devant l’installateur et vérifiez que la production '
          + 'et la consommation remontent toutes les deux. Notez les réserves sur le '
          + 'procès-verbal de réception plutôt qu’au téléphone le lendemain.',
      },
      {
        q: 'Faut-il nettoyer les panneaux, et les faire entretenir ?',
        r: 'Dans la plupart des régions, la pluie suffit, et les contrats d’entretien annuels '
          + 'vendus avec l’installation sont rarement justifiés sur une maison. Deux cas font '
          + 'exception : une forte exposition aux poussières, aux pollens, aux embruns ou aux '
          + 'fientes d’oiseaux, et une pente très faible qui ne se rince pas seule. Ce qui est '
          + 'utile, en revanche, c’est de regarder votre application : une production qui '
          + 'décroche d’un panneau ou d’une chaîne se voit immédiatement, et c’est le seul '
          + 'entretien qui compte vraiment — surveiller plutôt que frotter.',
      },
    ],
    parlerVrai: 'Un chantier solaire dure deux jours et un dossier solaire dure deux mois. '
      + 'L’entreprise que vous cherchez n’est pas celle qui pose le plus vite, c’est celle qui '
      + 'tient les trois dossiers administratifs sans que vous ayez à les relancer.',
  },

  /* ============================================================== 3. Garanties */
  {
    id: 'garanties',
    label: 'Garanties et installateur',
    Icone: ShieldCheck,
    phrase: 'Cinq garanties qui se superposent, et dix minutes pour vérifier que celle qui '
      + 'compte existe vraiment.',
    teinte: 'leaf',
    titreVignettes: 'Qui garantit quoi, et pendant combien de temps',
    vignettes: [
      {
        icon: Sun,
        titre: 'Garantie produit du panneau',
        texte: 'Le remplacement d’un module défectueux. Le standard du marché est de 25 ans, '
          + 'parfois 30 chez certains fabricants.',
        retenir: '25 ans, par le fabricant',
      },
      {
        icon: TrendingUp,
        titre: 'Garantie de rendement',
        texte: 'Un engagement sur la puissance restante en fin de période : de l’ordre de 85 à '
          + '90 % de la puissance initiale après 25 à 30 ans.',
        retenir: 'Lisez le pourcentage, pas la durée',
      },
      {
        icon: Cpu,
        titre: 'Garantie de l’onduleur',
        texte: 'De 8 à 12 ans pour un onduleur central, souvent 20 à 25 pour des '
          + 'micro-onduleurs. La vraie question est ailleurs : pièce seule, ou pièce, '
          + 'main-d’œuvre et déplacement ?',
        retenir: 'Là se joue la facture réelle',
      },
      {
        icon: BatteryCharging,
        titre: 'Garantie de la batterie',
        texte: 'Typiquement 10 ans, parfois 15. Elle s’exprime toujours de deux façons à la '
          + 'fois : une durée ou un nombre de cycles, ET une capacité restante — souvent 70 %.',
        retenir: 'Les deux conditions comptent',
      },
      {
        icon: HardHat,
        titre: 'Les garanties de l’installateur',
        texte: 'Parfait achèvement un an, biennale deux ans sur les équipements, et surtout '
          + 'décennale dix ans — celle qui couvre l’étanchéité de votre toiture.',
        retenir: 'La décennale est la seule qui vous sauve',
      },
      {
        icon: Siren,
        titre: 'Ce qui n’est garanti par personne',
        texte: 'Une production inférieure à l’étude si le devis ne l’engage pas, un ombrage '
          + 'apparu depuis, et un défaut sur un ouvrage non déclaré en mairie.',
        retenir: 'Les trous à connaître avant de signer',
      },
    ],
    titreDeplies: 'Vérifier l’entreprise qui va poser, en dix minutes',
    deplies: [
      {
        q: 'L’attestation d’assurance décennale — le seul document vraiment indispensable',
        r: 'Demandez-la à chaque entreprise consultée, et regardez deux choses : qu’elle soit '
          + 'en cours de validité à la date prévue des travaux, et que la liste des activités '
          + 'couvertes mentionne explicitement le photovoltaïque. Une décennale d’électricien '
          + 'générale qui ne cite pas la pose en toiture ne vous couvre pas là où le risque se '
          + 'trouve, c’est-à-dire sur l’étanchéité. Une entreprise sérieuse transmet son '
          + 'attestation sur simple demande, sans discuter. Un refus ou un délai est une '
          + 'réponse en soi.',
      },
      {
        q: 'Les qualifications : lesquelles, et où les vérifier',
        r: 'RGE QualiPV pour la pose photovoltaïque, Qualifelec pour la partie électrique, '
          + 'QualiPAC si une pompe à chaleur est au programme. Le label RGE conditionne '
          + 'l’accès à la plupart des aides publiques, et il doit couvrir précisément le type '
          + 'de travaux concerné : une entreprise peut être RGE sur l’isolation et pas sur le '
          + 'solaire. Ne vous fiez pas au logo sur le devis, vérifiez le numéro dans l’annuaire '
          + 'officiel de france-renov.gouv.fr — l’opération prend deux minutes et personne ne '
          + 'la fait.',
      },
      {
        q: 'La solidité de l’entreprise : ancienneté, taille, comptes',
        r: 'Une garantie de dix ans ne vaut que si l’entreprise existe encore dans dix ans, et '
          + 'c’est vérifiable gratuitement. Le numéro SIREN donne accès à la date de création '
          + 'et aux comptes publiés sur annuaire-entreprises.data.gouv.fr. Regardez l’année '
          + 'd’immatriculation, l’évolution du chiffre d’affaires et, si les comptes sont '
          + 'déposés, les capitaux propres. Une société jeune peut être excellente et une '
          + 'société ancienne peut être en difficulté : ce n’est pas un verdict, c’est un '
          + 'élément du dossier. Méfiez-vous surtout d’une société créée il y a six mois qui '
          + 'vend des garanties de vingt-cinq ans.',
      },
      {
        q: 'Qui viendra réellement poser sur mon toit ?',
        r: 'Posez la question telle quelle, et demandez le nom de l’entreprise qui monte sur le '
          + 'toit. La sous-traitance n’est pas un défaut — beaucoup d’entreprises sérieuses y '
          + 'ont recours hors de leur zone — mais elle doit être annoncée, et le sous-traitant '
          + 'doit avoir sa propre décennale, que vous pouvez demander aussi. Ce qui doit '
          + 'alerter, c’est l’enchaînement de plusieurs intermédiaires entre le commercial qui '
          + 'vous fait signer et l’équipe qui pose : plus la chaîne est longue, plus il est '
          + 'difficile de savoir qui répond en cas de problème.',
      },
      {
        q: 'Les avis en ligne : comment les lire sans se faire avoir',
        r: 'La note moyenne est la donnée la moins utile. Regardez le nombre d’avis et leur '
          + 'étalement dans le temps — trente avis en deux semaines, puis plus rien, raconte '
          + 'une campagne, pas une réputation. Lisez les avis négatifs en priorité, et surtout '
          + 'les réponses de l’entreprise : une entreprise qui répond précisément à une '
          + 'critique sur un chantier en dit plus long qu’une page de cinq étoiles. Demandez '
          + 'enfin deux ou trois références locales récentes, que vous pouvez appeler. Les '
          + 'installateurs qui travaillent bien ont des clients contents d’en parler.',
      },
      {
        q: 'Les signaux qui doivent vous faire arrêter net',
        r: 'Un démarchage que vous n’avez pas sollicité, par téléphone, SMS, courriel ou '
          + 'message privé : c’est interdit en rénovation énergétique depuis la loi du '
          + '30 juin 2025, et un contrat signé à la suite d’une sollicitation interdite est nul '
          + 'de plein droit. Une signature demandée le jour même, avec une remise qui expire ce '
          + 'soir. Des « travaux à 1 euro » ou « intégralement remboursés par l’État ». Un '
          + 'crédit présenté comme une formalité administrative. Un acompte important réclamé '
          + 'avant l’accord de la mairie. Et le refus de laisser le devis pour réflexion : vous '
          + 'disposez de quatorze jours de rétractation sur un contrat signé chez vous, sans '
          + 'motif ni frais.',
      },
    ],
    parlerVrai: 'Helios ne vous dira jamais qu’une entreprise est bonne parce qu’elle est '
      + 'partenaire. Les critères ci-dessus sont exactement ceux que nous appliquons à nos '
      + 'partenaires, et nous vous les donnons pour que vous puissiez les appliquer à '
      + 'n’importe qui — y compris à ceux que nous vous présentons.',
  },

  /* =============================================================== 4. Stockage */
  {
    id: 'stockage',
    label: 'Le stockage',
    Icone: BatteryCharging,
    phrase: 'Quatre façons de garder son surplus pour plus tard, dont une seule est '
      + 'aujourd’hui économiquement évidente.',
    teinte: 'terra',
    titreVignettes: 'Les quatre familles, et ce que chacune tient vraiment',
    vignettes: [
      {
        icon: BatteryCharging,
        titre: 'La batterie physique',
        texte: 'Du lithium-fer-phosphate, 5 à 15 kWh, un rendement proche de 95 %, garantie '
          + 'une dizaine d’années. Elle vous appartient, et elle seule vous donne du courant '
          + 'pendant une coupure.',
        retenir: 'Confort et résilience, pas placement',
      },
      {
        icon: CircleDollarSign,
        titre: 'La batterie virtuelle',
        texte: 'Aucun matériel : votre surplus devient un crédit de kWh chez un fournisseur, '
          + 'que vous récupérez plus tard. C’est aujourd’hui la formule la moins chère au kWh '
          + 'restitué.',
        retenir: 'Impose un fournisseur précis',
      },
      {
        icon: Zap,
        titre: 'Le volant d’inertie en béton',
        texte: 'Un cylindre de béton qui tourne sous vide, de l’ordre de 10 kWh dont 7 '
          + 'utilisables, rendement annoncé autour de 70 %, durée de vie visée 40 ans et '
          + 'aucun métal critique.',
        retenir: 'Chiffres à confirmer au lancement',
      },
      {
        icon: Leaf,
        titre: 'Le sodium-ion',
        texte: 'Une chimie sans lithium ni cobalt, plus sûre et plus abondante, mais plus '
          + 'volumineuse à capacité égale. L’offre domestique est encore jeune.',
        retenir: 'À suivre, pas encore un standard',
      },
      {
        icon: Plug,
        titre: 'Le secours en cas de coupure',
        texte: 'Il ne s’obtient qu’avec une batterie physique et un câblage prévu pour : un '
          + 'tableau de circuits secourus, et une puissance de sortie en kW suffisante pour '
          + 'les appareils concernés.',
        retenir: 'Regardez les kW, pas que les kWh',
      },
      {
        icon: Gauge,
        titre: 'Le pilotage, qui n’est pas du stockage',
        texte: 'Déplacer le ballon, la piscine ou la voiture vers les heures de production '
          + 'coûte quelques centaines d’euros et produit souvent plus d’effet qu’une batterie '
          + 'de plusieurs milliers.',
        retenir: 'À faire en premier, dans tous les cas',
      },
    ],
    titreDeplies: 'Les arbitrages, posés honnêtement',
    deplies: [
      {
        q: 'Physique ou virtuelle : la réponse honnête',
        r: 'Les deux ont de vrais avantages, et le choix n’est pas seulement financier. La '
          + 'batterie physique permet de garder du courant en cas de coupure, ne dépend '
          + 'd’aucun opérateur, et vous appartient — ce rapport à « sa » propre énergie compte '
          + 'pour beaucoup de foyers, et c’est légitime. La batterie virtuelle ne demande aucun '
          + 'matériel ni entretien et coûte aujourd’hui nettement moins par kWh restitué, mais '
          + 'elle impose de passer chez un fournisseur précis, ce que beaucoup refusent. '
          + 'Surtout, l’écart économique entre les deux dépend de votre courbe de charge, pas '
          + 'de la théorie. C’est pourquoi Helios simule les deux à consommation réelle égale, '
          + 'vous montre les deux résultats, et vous laisse décider.',
      },
      {
        q: 'Pourquoi dit-on qu’une batterie n’est pas un placement ?',
        r: 'Parce qu’on peut calculer ce que coûte chaque kWh qui en sort, en ramenant son prix '
          + 'd’achat à l’énergie qu’elle restituera dans sa vie. Pour une batterie physique '
          + 'résidentielle, l’étude que nous avons menée en juin 2026 situe ce coût entre 0,31 '
          + 'et 0,40 € par kWh restitué — donc au-dessus du prix auquel vous achetez '
          + 'l’électricité au réseau, autour de 0,20 €. Mécaniquement, elle ne peut pas être '
          + 'rentable à ce prix-là, et un vendeur qui vous annonce le contraire a changé les '
          + 'conventions de calcul. Cela n’enlève rien à son intérêt : l’autonomie en cas de '
          + 'coupure et l’indépendance ont une valeur, simplement ce n’est pas une valeur '
          + 'financière.',
      },
      {
        q: 'Ce qu’une batterie virtuelle ne fait pas',
        r: 'Elle ne vous donne pas de courant pendant une coupure — sans matériel chez vous, '
          + 'il n’y a rien à décharger. Elle ne permet pas, en pratique, de stocker l’été pour '
          + 'consommer l’hiver : les formules facturent la restitution ou plafonnent les '
          + 'reports, et un crédit de kWh accumulé en juin se révèle rarement intact en '
          + 'janvier. Enfin ses conditions sont révisables : le prix de restitution, '
          + 'l’abonnement et les plafonds peuvent changer. Deux précautions simples en '
          + 'découlent : préférez une offre sans engagement, et ne thésaurisez pas vos crédits '
          + 'au-delà d’un hiver.',
      },
      {
        q: 'Et si l’opérateur de ma batterie virtuelle disparaît ?',
        r: 'C’est une question qu’il faut poser, parce que le marché est jeune : ces dernières '
          + 'années ont vu des levées de fonds importantes chez certains opérateurs et des '
          + 'recapitalisations chez d’autres. Vos panneaux, eux, restent les vôtres quoi qu’il '
          + 'arrive : la batterie virtuelle est un service de fournisseur, pas une hypothèque '
          + 'sur votre installation. En cas de défaillance, vous perdez le crédit de kWh non '
          + 'consommé et vous changez de fournisseur, comme pour n’importe quel contrat '
          + 'd’électricité. C’est précisément pour cela que le sans-engagement et la prudence '
          + 'sur les crédits accumulés sont les deux bons réflexes.',
      },
      {
        q: 'Ajouter une batterie à une installation déjà posée ?',
        r: 'C’est techniquement possible dans presque tous les cas, par ce qu’on appelle un '
          + 'couplage en courant alternatif : la batterie et son onduleur viennent se greffer à '
          + 'côté de l’existant, sans toucher aux panneaux. Deux points à vérifier avant de '
          + 's’engager. D’abord la fiscalité : sur une installation existante, l’ajout d’une '
          + 'batterie seule ne bénéficie généralement pas de la TVA réduite, ce qui change le '
          + 'prix final. Ensuite votre contrat : si vous vendez votre surplus sous un ancien '
          + 'contrat d’obligation d’achat avantageux, stocker ce surplus réduit ce que vous '
          + 'vendez — il faut faire le calcul avant, pas après.',
      },
    ],
    parlerVrai: 'Dans l’ordre : on pilote d’abord ses usages, on dimensionne ensuite ses '
      + 'panneaux sur ce qu’on consomme, et on ne regarde le stockage qu’après. Un projet qui '
      + 'commence par la batterie commence par le poste le plus cher et le moins rentable.',
  },

  /* ================================================================= 5. Marché */
  {
    id: 'marche',
    label: 'Marché et empreinte',
    Icone: TrendingUp,
    phrase: 'Ce qui a changé en 2026, où va le marché, et ce que vaut vraiment une '
      + 'installation côté climat.',
    teinte: 'primary',
    titreVignettes: 'Le paysage de 2026',
    vignettes: [
      {
        icon: FileSignature,
        titre: 'La réforme du 5 juin 2026',
        texte: 'Le rachat du surplus résidentiel est tombé à 1,1 centime le kWh et la prime à '
          + 'l’autoconsommation a été supprimée. Un kWh injecté vaut environ dix-sept fois '
          + 'moins qu’un kWh évité.',
        retenir: 'Vendre son surplus n’est plus une stratégie',
      },
      {
        icon: CircleDollarSign,
        titre: 'Le prix que vos panneaux effacent',
        texte: 'Le tarif réglementé se situe autour de 0,20 € le kWh en 2026. C’est ce '
          + 'prix-là, celui que vous n’aurez pas à payer, qui fait aujourd’hui toute la '
          + 'rentabilité d’une installation.',
        retenir: 'Autoconsommer, et rien d’autre',
      },
      {
        icon: CalendarClock,
        titre: 'Les tarifs dynamiques',
        texte: 'Des prix qui suivent le marché heure par heure : très bas, parfois négatifs, '
          + 'au milieu des journées de printemps ; très élevés aux pointes d’hiver. Gagnants si '
          + 'vous pouvez déplacer des usages.',
        retenir: 'À fuir si rien n’est pilotable',
      },
      {
        icon: TrendingUp,
        titre: 'Le « canard solaire »',
        texte: 'Plus un pays s’équipe, moins le kWh solaire de midi vaut cher. Le phénomène est '
          + 'déjà installé en Espagne et progresse en France : ce qui est rentable aujourd’hui '
          + 'doit être réévalué régulièrement.',
        retenir: 'Préférez le sans-engagement',
      },
      {
        icon: Recycle,
        titre: 'Le recyclage',
        texte: 'La filière française Soren reprend gratuitement les panneaux en fin de vie — '
          + 'l’éco-participation est déjà payée dans le prix du module. Taux de valorisation '
          + 'moyen annoncé : 94 %, dont environ 84 % de recyclage matière.',
        retenir: 'Organisé et financé d’avance',
      },
      {
        icon: Leaf,
        titre: 'Le bilan carbone',
        texte: 'De l’ordre de 25 g de CO₂ par kWh pour un module fabriqué en Europe, environ '
          + '44 g pour un module chinois, et un à trois ans pour rembourser l’énergie de sa '
          + 'fabrication.',
        retenir: 'À comparer au réseau, voir ci-dessous',
      },
    ],
    titreDeplies: 'Les questions de fond',
    deplies: [
      {
        q: 'Le solaire est-il vraiment bon pour le climat, en France ?',
        r: 'La réponse honnête est nuancée, et vous ne la lirez pas souvent sous la plume d’un '
          + 'vendeur. Une installation résidentielle émet de l’ordre de 25 à 44 g de CO₂ par '
          + 'kWh produit sur tout son cycle de vie. Or l’électricité française est déjà '
          + 'très peu carbonée : la production nationale est descendue à 19,6 g par kWh en '
          + 'moyenne sur 2025, autour de 29 g si l’on compte le cycle de vie complet des '
          + 'installations. Autrement dit, en France, poser des panneaux sur son toit apporte '
          + 'un gain climatique faible, voire nul selon l’heure et l’origine des modules — '
          + 'alors que le même geste dans un pays dont l’électricité vient du charbon ou du gaz '
          + 'est massivement bénéfique. Ce qui reste solide ici, c’est l’intérêt économique, '
          + 'la baisse de la tension sur la pointe, et la part d’autonomie que vous gagnez. Et '
          + 'si votre motivation première est le climat, la sobriété et l’isolation font '
          + 'davantage, pour moins cher — c’est l’ordre que nous défendons partout.',
      },
      {
        q: 'Que deviennent mes panneaux dans vingt-cinq ans ?',
        r: 'Ils produisent encore. Les garanties de rendement engagent 85 à 90 % de la '
          + 'puissance initiale après 25 à 30 ans, et la dégradation réellement constatée est '
          + 'de 0,3 à 0,5 % par an : une installation de 2026 produira encore l’essentiel de ce '
          + 'qu’elle produit aujourd’hui en 2050. Les deux points de vigilance ne sont pas les '
          + 'panneaux mais l’onduleur, à remplacer une fois, et l’étanchéité, qui dépend de la '
          + 'qualité de pose. Le jour où vous les déposerez, la reprise est organisée et déjà '
          + 'financée : la filière Soren a collecté 13 760 tonnes de panneaux en France en '
          + '2025, et a sélectionné en mars 2026 six opérateurs capables d’en traiter plus de '
          + '45 000 tonnes par an — en prévision de la vague d’installations arrivant en fin de '
          + 'vie vers 2030.',
      },
      {
        q: 'Faut-il attendre que les prix baissent encore ?',
        r: 'Les prix du matériel baissent effectivement, en particulier ceux des batteries, de '
          + 'quelques pourcents par an. Mais trois choses jouent dans l’autre sens : '
          + 'l’électricité que vous n’achetez pas aujourd’hui est une économie acquise et '
          + 'perdue si vous attendez, le cadre des aides se resserre plutôt qu’il ne '
          + 's’élargit, et la valeur du surplus continue de s’éroder. En pratique, attendre se '
          + 'justifie si votre consommation va changer prochainement — arrivée d’une voiture '
          + 'électrique, d’une pompe à chaleur, d’une piscine — parce qu’alors la bonne '
          + 'puissance n’est pas celle d’aujourd’hui. Attendre « que ça baisse » sans autre '
          + 'raison vous fait surtout perdre des années de production.',
      },
      {
        q: 'Pourquoi mon surplus ne vaut-il presque rien alors que l’électricité est chère ?',
        r: 'Parce que le prix que vous payez et la valeur de ce que vous injectez n’ont presque '
          + 'rien à voir. Votre facture comprend l’acheminement, les taxes et la '
          + 'commercialisation ; votre injection, elle, n’est rémunérée que comme de l’énergie, '
          + 'au moment précis où tout le monde en produit. Aux heures solaires de printemps, la '
          + 'production nationale dépasse par moments la demande et le prix de marché peut même '
          + 'passer en négatif. Le tarif de 1,1 centime fixé en juin 2026 reflète cette '
          + 'réalité : le réseau n’a pas besoin de votre kWh de midi. C’est exactement pour '
          + 'cela que tout l’intérêt s’est déplacé vers l’autoconsommation et le décalage des '
          + 'usages.',
      },
      {
        q: 'Un marché jeune : à quoi faut-il s’attendre ?',
        r: 'À du mouvement. Le cadre tarifaire a changé deux fois en cinq ans, les opérateurs '
          + 'de stockage virtuel sont des sociétés récentes qui lèvent des fonds ou se '
          + 'recapitalisent, et les fournisseurs à tarif dynamique apparaissent et '
          + 'disparaissent. Rien de tout cela ne remet en cause votre installation, qui est un '
          + 'actif physique sur votre toit — mais cela doit vous rendre prudent sur tout ce qui '
          + 'est contractuel et de longue durée. Trois réflexes : préférer les offres sans '
          + 'engagement, refuser d’immobiliser de la valeur chez un tiers au-delà de ce que '
          + 'vous accepteriez de perdre, et re-simuler votre situation à chaque évolution '
          + 'tarifaire. Le matériel vous appartient ; les contrats, non.',
      },
    ],
    parlerVrai: 'Nous préférons vous dire que le gain climatique du solaire est modeste en '
      + 'France plutôt que de vous vendre une bonne conscience. Le bon argument reste solide : '
      + 'vous produisez une électricité que vous n’achetez pas, chez vous, pendant vingt-cinq '
      + 'ans. C’est déjà beaucoup.',
  },
]

/** Les deux pastilles de l'en-tête : où le visiteur se trouve dans la maison d'Helios. */
export const REPERES: { icon: LucideIcon; texte: string }[] = [
  { icon: ClipboardCheck, texte: 'Aucun chiffre certain : des ordres de grandeur, et leur source' },
  { icon: Users, texte: 'Aucune marque poussée : les critères, pour que vous jugiez vous-même' },
  { icon: Award, texte: 'Les mêmes exigences pour nos partenaires que pour les autres' },
  { icon: Building2, texte: 'Gratuit, et jamais facturé au foyer' },
]
