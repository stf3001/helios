// Guides & Aides — gabarits de contenu. Le contenu réel est à rédiger (placeholders `[À rédiger]`).
// Chaque guide = un chapô + des sections. Les montants d'aides/chiffres doivent être vérifiés.

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

const PLACEHOLDER = '[À rédiger — remplacez ce texte par le contenu réel du guide.]'

export const guides: Guide[] = [
  {
    slug: 'par-ou-commencer',
    titre: 'Par où commencer sa rénovation énergétique ?',
    categorie: 'Rénovation',
    chapo: 'La bonne méthode : sobriété, puis isolation, puis systèmes, puis production. On vous explique pourquoi cet ordre.',
    aVenir: true,
    sections: [
      { titre: 'Les gestes gratuits d\'abord', contenu: PLACEHOLDER },
      { titre: 'Isoler avant tout', contenu: PLACEHOLDER },
      { titre: 'Choisir son chauffage', contenu: PLACEHOLDER },
      { titre: 'Et le solaire ?', contenu: PLACEHOLDER },
    ],
  },
  {
    slug: 'maprimerenov',
    titre: 'MaPrimeRénov\' : comment ça marche ?',
    categorie: 'Aides',
    chapo: 'Le principe de l\'aide, qui peut en bénéficier, et comment la demander. Montants à vérifier chaque année.',
    aVenir: true,
    sections: [
      { titre: 'Qui peut en bénéficier ?', contenu: PLACEHOLDER },
      { titre: 'Pour quels travaux ?', contenu: PLACEHOLDER },
      { titre: 'Comment faire sa demande', contenu: PLACEHOLDER },
    ],
  },
  {
    slug: 'isolation-combles',
    titre: 'Isoler ses combles : le meilleur rapport coût/efficacité',
    categorie: 'Isolation',
    chapo: 'Jusqu\'à 30 % des pertes de chaleur passent par la toiture. Souvent le premier chantier à envisager.',
    aVenir: true,
    sections: [
      { titre: 'Pourquoi commencer par les combles', contenu: PLACEHOLDER },
      { titre: 'Combles perdus ou aménagés', contenu: PLACEHOLDER },
      { titre: 'Ordres de grandeur de coût', contenu: PLACEHOLDER },
    ],
  },
  {
    slug: 'pompe-a-chaleur',
    titre: 'La pompe à chaleur, pour qui ?',
    categorie: 'Chauffage',
    chapo: 'Une PAC bien dimensionnée dans une maison bien isolée peut diviser la facture de chauffage. Les conditions à réunir.',
    aVenir: true,
    sections: [
      { titre: 'Le principe', contenu: PLACEHOLDER },
      { titre: 'Isoler d\'abord', contenu: PLACEHOLDER },
      { titre: 'Air/eau ou air/air ?', contenu: PLACEHOLDER },
    ],
  },
  {
    slug: 'autoconsommation-solaire',
    titre: 'Autoconsommation solaire : les bases',
    categorie: 'Solaire',
    chapo: 'Produire son électricité et la consommer sur place. Ce que ça change sur la facture, et comment bien dimensionner.',
    aVenir: true,
    sections: [
      { titre: 'Autoconsommer, c\'est quoi', contenu: PLACEHOLDER },
      { titre: 'Bien dimensionner son installation', contenu: PLACEHOLDER },
      { titre: 'Avec ou sans batterie', contenu: PLACEHOLDER },
    ],
  },
  {
    slug: 'bien-acheter-energie',
    titre: 'Payer son électricité au meilleur prix',
    categorie: 'Énergie',
    chapo: 'Puissance souscrite, heures creuses, tarif dynamique : les leviers pour ne pas payer trop cher.',
    aVenir: true,
    sections: [
      { titre: 'Ajuster sa puissance souscrite', contenu: PLACEHOLDER },
      { titre: 'Heures pleines / heures creuses', contenu: PLACEHOLDER },
      { titre: 'Le tarif dynamique, pour qui', contenu: PLACEHOLDER },
    ],
  },
]

export const guideCategories = Array.from(new Set(guides.map((g) => g.categorie)))
