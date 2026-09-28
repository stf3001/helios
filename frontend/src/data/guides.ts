// Guides — PARCOURS uniquement. Un guide n'apporte pas de connaissance : il en donne
// l'ordre. Tout le savoir vit dans kb/ (la FAQ et le chat y puisent), et c'est la seule
// source a tenir a jour.
//
// Le 28/09/2026, 12 guides ont ete retires. La comparaison de leurs 43 sections avec les
// 311 fiches de la base n'a trouve AUCUN contenu unique : 35 doublons francs (jusqu'a 0,96
// de similarite), 8 recouvrements partiels, 0 section inedite. Ils redisaient la FAQ en
// moins complet, et n'avaient jamais ete relus alors qu'ils etaient en ligne et indexes.
// Leurs URL sont redirigees en 301 (cf. deploy/nginx.conf) : on ne jette pas le
// referencement acquis.
//
// Les deux qui restent sont ceux que la FAQ ne sait pas faire : enchainer. Une FAQ suppose
// qu'on connaisse deja sa question. A RELIRE par l'equipe : ce sont encore des brouillons.

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
]

export const guideCategories = Array.from(new Set(guides.map((g) => g.categorie)))
