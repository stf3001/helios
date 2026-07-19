// Glossaire — définitions courtes et vulgarisées. Les définitions générales sont fournies ;
// celles qui dépendent de montants/règles annuelles portent la mention [à vérifier].

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
  { terme: 'MaPrimeRénov\'', definition: 'La principale aide publique à la rénovation énergétique en France. Les montants et conditions évoluent chaque année. [à vérifier pour l\'année en cours]' },
  { terme: 'CEE', definition: 'Certificats d\'Économies d\'Énergie : un dispositif qui oblige les fournisseurs d\'énergie à financer une partie de vos travaux d\'économie d\'énergie. [montants à vérifier]' },
  { terme: 'Heures creuses', definition: 'Des plages horaires (souvent la nuit) où l\'électricité est facturée moins cher, si vous avez souscrit l\'option Heures Pleines / Heures Creuses.' },
  { terme: 'Tarif dynamique', definition: 'Une offre d\'électricité dont le prix varie heure par heure selon le marché. Intéressant si l\'on peut décaler ses usages vers les heures peu chères.' },
  { terme: 'PDL', definition: 'Point De Livraison : le numéro à 14 chiffres qui identifie votre compteur électrique. Il figure sur votre facture et permet, avec votre accord, des estimations précises.' },
]
