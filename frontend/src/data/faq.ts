// Extrait de la base (kb/) — au jalon 3 la FAQ sera servie par l'API (RAG).
export interface FaqEntry { q: string; r: string; cat: string }

export const faq: FaqEntry[] = [
  {
    cat: 'HELIOS',
    q: "HELIOS, c'est quoi ?",
    r: "Une plateforme gratuite d'accompagnement à la transition énergétique des logements. Vous décrivez votre maison, Helios — notre IA franche et sans intérêt commercial — analyse et vous oriente : gestes gratuits, priorités de travaux, ordres de grandeur de coûts et d'aides, à votre rythme.",
  },
  {
    cat: 'HELIOS',
    q: "Pourquoi est-ce gratuit ?",
    r: "En toute transparence : si Helios vous préconise des travaux et que vous choisissez de les confier à une entreprise partenaire, celle-ci nous verse une commission d'apport d'affaires. Vous ne payez jamais rien, et les préconisations d'Helios sont strictement indépendantes de ce mécanisme.",
  },
  {
    cat: 'Sobriété',
    q: "Quel est le geste le plus rentable pour réduire ma facture de chauffage ?",
    r: "Baisser la consigne : 1 °C de moins ≈ 7 % de consommation de chauffage en moins. Recommandation : 19 °C pièces de vie, 17 °C chambres, 16 °C en absence. C'est gratuit et immédiat.",
  },
  {
    cat: 'Isolation',
    q: "Par quoi commencer pour isoler sa maison ?",
    r: "Dans une maison non isolée, la toiture représente 25–30 % des déperditions : on commence presque toujours par les combles — meilleur rapport coût/efficacité, souvent amorti en moins de 5 ans.",
  },
  {
    cat: 'Solaire',
    q: "Comment bien dimensionner son installation solaire depuis la réforme 2026 ?",
    r: "Nouvelle règle : production ≈ consommation annuelle. Depuis juin 2026, le surplus n'est racheté que 1,1 c€/kWh : le kWc « en plus pour la revente » détruit de la valeur. La batterie virtuelle est devenue le mode de valorisation de référence du surplus.",
  },
  {
    cat: 'Aides',
    q: "Comment éviter les arnaques à la rénovation ?",
    r: "Le démarchage téléphonique pour la rénovation énergétique est interdit. Signaux d'alerte : « travaux à 1 € », pression à signer vite, crédit intégré. Toujours : plusieurs devis, vérification RGE, jamais de signature le jour même.",
  },
]
