// Glossaire — définitions courtes et vulgarisées. RÈGLE (19/10/2026) : aucun montant d'aide
// ici. Ils changent chaque année, et un montant faux engage HELIOS ; la définition donne le
// mécanisme, la base de connaissances (kb/baremes_aides.md…) porte les montants datés.
// Termes repris de la base de connaissances (kb/*.md, 05-FAQ-V1.md) déjà utilisés dans les
// réponses d'Helios mais absents jusqu'ici de cette page de référence rapide.

export interface Terme {
  terme: string
  definition: string
}

export const glossaire: Terme[] = [
  { terme: 'DPE', definition: 'Diagnostic de Performance Énergétique : une étiquette (de A à G) qui note la consommation d\'énergie et les émissions d\'un logement. Obligatoire à la vente et à la location.' },
  { terme: 'kWh', definition: 'Kilowattheure : l\'unité de mesure de l\'énergie consommée. C\'est ce que compte votre compteur et ce qui apparaît sur votre facture.' },
  { terme: 'kWc', definition: 'Kilowatt-crête : la puissance maximale d\'une installation solaire dans des conditions idéales. Une installation résidentielle fait souvent 3, 6 ou 9 kWc.' },
  { terme: 'Autoconsommation', definition: 'Le fait de consommer sur place l\'électricité que l\'on produit (par exemple avec des panneaux solaires), au lieu de la revendre entièrement au réseau.' },
  { terme: 'Pompe à chaleur (PAC)', definition: 'Un système de chauffage qui capte la chaleur de l\'air ou du sol pour chauffer le logement ou l\'eau. Très efficace, surtout dans une maison bien isolée.' },
  { terme: 'RGE', definition: 'Reconnu Garant de l\'Environnement : un label qui certifie qu\'une entreprise de travaux respecte des critères de qualité. Souvent exigé pour bénéficier des aides.' },
  { terme: 'VMC', definition: 'Ventilation Mécanique Contrôlée : un système qui renouvelle l\'air du logement. La VMC double flux récupère la chaleur de l\'air sortant pour limiter les pertes.' },
  { terme: 'Déperditions', definition: 'Les pertes de chaleur d\'un logement, par la toiture, les murs, les fenêtres, le sol et la ventilation. Les réduire, c\'est chauffer moins pour le même confort.' },
  { terme: 'Sobriété', definition: 'Réduire ses consommations par les usages et les réglages, sans travaux : baisser d\'un degré, programmer le chauffage, décaler certains usages. Gratuit et immédiat.' },
  { terme: 'MaPrimeRénov\'', definition: 'La principale aide publique à la rénovation énergétique en France, réservée aux résidences principales. Deux parcours : par geste (un équipement ou une isolation) ou rénovation d\'ampleur, accompagnée. Le montant dépend des revenus du foyer et des travaux ; il évolue chaque année.' },
  { terme: 'CEE', definition: 'Certificats d\'Économies d\'Énergie : un dispositif qui oblige les fournisseurs d\'énergie à financer une partie de vos travaux d\'économie d\'énergie. La prime se demande AVANT de signer le devis, et se cumule avec MaPrimeRénov\'.' },
  { terme: 'Heures creuses', definition: 'Des plages horaires (souvent la nuit) où l\'électricité est facturée moins cher, si vous avez souscrit l\'option Heures Pleines / Heures Creuses.' },
  { terme: 'Tarif dynamique', definition: 'Une offre d\'électricité dont le prix varie heure par heure selon le marché. Intéressant si l\'on peut décaler ses usages vers les heures peu chères.' },
  { terme: 'PDL', definition: 'Point De Livraison : le numéro à 14 chiffres qui identifie votre compteur électrique. Il figure sur votre facture et permet, avec votre accord, des estimations précises.' },

  // --- Ajouts : termes techniques déjà employés dans les réponses d'Helios ---
  { terme: 'Résistance thermique (R)', definition: 'Indique la capacité d\'un isolant à freiner la chaleur : plus le R est élevé, meilleure est l\'isolation. Exprimé en m².K/W, c\'est le chiffre à comparer entre deux devis d\'isolation.' },
  { terme: 'COP', definition: 'Coefficient de Performance : le rendement d\'une pompe à chaleur. Un COP de 3 signifie 3 kWh de chaleur produits pour 1 kWh d\'électricité consommé. Il baisse quand il fait très froid dehors.' },
  { terme: 'Uw', definition: 'Coefficient de transmission thermique d\'une fenêtre (vitrage + cadre) : plus il est bas, moins la fenêtre laisse fuir la chaleur. À comparer entre deux devis de menuiseries.' },
  { terme: 'Passoire thermique', definition: 'Un logement classé F ou G au DPE, donc très énergivore. Ces logements sont progressivement interdits à la location (calendrier 2025-2034) et leur loyer est gelé.' },
  { terme: 'Rénovation d\'ampleur', definition: 'Un bouquet de travaux qui fait gagner plusieurs classes DPE d\'un coup (au lieu de travaux isolés). Mieux aidée par MaPrimeRénov\', mais plus complexe à monter.' },
  { terme: 'Audit énergétique réglementaire', definition: 'Un diagnostic approfondi, réalisé par un professionnel certifié, obligatoire pour vendre certains logements très énergivores (F, G, et E depuis 2025). Différent et plus poussé qu\'un DPE.' },
  { terme: 'Éco-PTZ', definition: 'Prêt à taux zéro pour financer des travaux de rénovation énergétique, de quelques milliers d\'euros pour un seul geste jusqu\'à 50 000 € pour une rénovation globale. Cumulable avec MaPrimeRénov\' et les CEE. Prolongé jusqu\'à fin 2027.' },
  { terme: 'TVA à taux réduit', definition: 'Un taux de 5,5 % (au lieu de 20 %) appliqué directement sur le devis des travaux de rénovation énergétique, dans un logement achevé depuis plus de 2 ans. Aucune démarche à faire : c\'est l\'entreprise qui le mentionne sur le devis et la facture.' },
  { terme: 'DTG (diagnostic technique global)', definition: 'Un état des lieux technique complet d\'un immeuble en copropriété (structure, équipements, performance énergétique), souvent préalable à un projet de travaux collectifs.' },
  { terme: 'PPT (plan pluriannuel de travaux)', definition: 'Un programme de travaux étalé sur plusieurs années, obligatoire pour certaines copropriétés, qui budgétise et planifie les rénovations à venir — y compris énergétiques.' },
  { terme: 'ABF (Architecte des Bâtiments de France)', definition: 'L\'autorité qui valide les travaux visibles depuis l\'extérieur dans les zones protégées (centres historiques, abords de monuments). Peut imposer des contraintes esthétiques sur l\'isolation ou le solaire.' },
  { terme: 'PLU (plan local d\'urbanisme)', definition: 'Le document qui fixe les règles de construction et d\'aspect extérieur dans une commune. À consulter avant tout projet de panneaux solaires, d\'isolation par l\'extérieur ou d\'extension.' },
  { terme: 'TRV (tarif réglementé de vente)', definition: 'Le tarif de l\'électricité fixé par les pouvoirs publics (le contrat historique EDF). Sert de référence pour comparer les offres de marché, mais n\'est plus toujours la moins chère.' },
  { terme: 'HP/HC (heures pleines / heures creuses)', definition: 'Une option tarifaire où le prix de l\'électricité change selon l\'heure de la journée. Intéressante seulement si une part significative de la consommation peut être décalée vers les heures creuses.' },
  { terme: 'TURPE', definition: 'Tarif d\'Utilisation des Réseaux Publics d\'Électricité : la part du prix de l\'électricité qui finance le réseau (lignes, transformateurs). Elle s\'applique même sur l\'électricité qu\'on récupère d\'un stockage.' },
  { terme: 'Accise sur l\'électricité', definition: 'Une taxe nationale incluse dans le prix du kWh, quel que soit le fournisseur. Elle s\'ajoute au TURPE dans la plupart des frais liés à l\'électricité, y compris certains services de stockage.' },
  { terme: 'Obligation d\'achat', definition: 'Le dispositif qui oblige un fournisseur à racheter le surplus d\'électricité solaire non autoconsommé, à un tarif garanti sur plusieurs années — mais ce tarif de rachat a fortement baissé ces dernières années.' },
  { terme: 'Batterie virtuelle', definition: 'Un service qui « met de côté » le surplus solaire non consommé (sans matériel de stockage physique) pour le restituer plus tard, moyennant un abonnement et parfois des frais de restitution.' },
  { terme: 'V2G / V2H (vehicle-to-grid / vehicle-to-home)', definition: 'Des technologies qui permettent d\'utiliser la batterie d\'un véhicule électrique pour alimenter la maison ou le réseau. Encore peu répandues en France, nécessitent un véhicule et une borne compatibles.' },
  { terme: 'Talon de consommation', definition: 'La consommation électrique qui ne s\'arrête jamais, même la nuit ou en absence (frigo, box internet, veilles). Un talon élevé signale souvent des économies faciles à trouver.' },
  { terme: 'Garantie décennale', definition: 'L\'assurance obligatoire d\'un artisan qui couvre pendant 10 ans les dommages compromettant la solidité d\'un ouvrage. À vérifier systématiquement avant de signer un devis de travaux.' },
  { terme: 'Garantie de parfait achèvement', definition: 'Pendant 1 an après la réception des travaux, l\'entreprise doit réparer tout défaut signalé — même mineur. C\'est la première garantie à activer en cas de problème.' },
  { terme: 'Enedis', definition: 'Le gestionnaire du réseau électrique français (pose et relève les compteurs Linky). Avec votre consentement, Helios pourra un jour récupérer votre vraie courbe de consommation auprès d\'Enedis.' },
  { terme: 'Courbe de charge', definition: 'Le détail de la consommation électrique d\'un logement heure par heure (ou demi-heure), mesuré par le compteur Linky. Bien plus précis qu\'une simple consommation annuelle pour simuler des économies.' },
  { terme: 'Bonus écologique', definition: 'L\'ancienne aide de l\'État à l\'achat d\'une voiture électrique neuve. Depuis le 1er juillet 2025, elle est remplacée par une prime « coup de pouce » financée par les CEE, sous conditions de revenus, de prix et de score environnemental du véhicule.' },
  { terme: 'Prime à la conversion', definition: 'Une aide qui était versée en échange de la mise au rebut d\'un vieux véhicule polluant. Elle est supprimée depuis le 2 décembre 2024 : un vendeur qui l\'annonce encore se trompe.' },
  { terme: 'Volant d\'inertie (VOSS)', definition: 'Un stockage d\'électricité mécanique : un cylindre de béton tourne à grande vitesse sous vide, accéléré par le surplus solaire le jour et freiné la nuit pour restituer l\'énergie. Rendement plus faible qu\'une batterie (~70 %), mais durée de vie exceptionnelle (garantie annoncée 40 ans, plus d\'un million de cycles) et aucun métal critique. [specs à confirmer au lancement]' },
]
