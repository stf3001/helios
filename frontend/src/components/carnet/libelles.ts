/**
 * Libellés du carnet de maison (lot 1). Les CODES viennent de
 * `api/app/models/equipement.py` (`TYPES_PAR_CATEGORIE`) : les deux listes se tiennent à
 * jour ENSEMBLE — un code absent ici s'afficherait brut, un code absent là-bas serait
 * refusé par l'API.
 */
import type { FieldOption } from '../fiche/types'

export const CATEGORIES: FieldOption[] = [
  { value: 'chauffage', label: 'Chauffage' },
  { value: 'ecs', label: 'Eau chaude' },
  { value: 'clim', label: 'Climatisation' },
  { value: 'ventilation', label: 'Ventilation' },
  { value: 'production_electricite', label: "Production d'électricité" },
  { value: 'stockage', label: 'Stockage' },
  { value: 'recharge', label: 'Recharge du véhicule' },
  { value: 'eau', label: 'Eau et assainissement' },
  { value: 'autre', label: 'Autre' },
]

export const TYPES: Record<string, FieldOption[]> = {
  chauffage: [
    { value: 'PAC_air_eau', label: 'PAC air/eau' },
    { value: 'PAC_air_air', label: 'PAC air/air' },
    { value: 'chaudiere_gaz', label: 'Chaudière gaz' },
    { value: 'chaudiere_fioul', label: 'Chaudière fioul' },
    { value: 'chaudiere_bois', label: 'Chaudière bois' },
    { value: 'poele_bois', label: 'Poêle à bois' },
    { value: 'poele_granules', label: 'Poêle à granulés' },
    { value: 'insert', label: 'Insert ou foyer fermé' },
    { value: 'convecteurs', label: 'Convecteurs électriques' },
    { value: 'radiateurs_inertie', label: 'Radiateurs à inertie' },
    { value: 'autre', label: 'Autre' },
  ],
  ecs: [
    { value: 'ballon_elec', label: 'Ballon électrique' },
    { value: 'thermodynamique', label: 'Ballon thermodynamique' },
    { value: 'gaz', label: 'Chauffe-eau gaz' },
    { value: 'solaire', label: 'Chauffe-eau solaire' },
    { value: 'instantane', label: 'Chauffe-eau instantané' },
    { value: 'autre', label: 'Autre' },
  ],
  clim: [
    { value: 'split', label: 'Split' },
    { value: 'multisplit', label: 'Multisplit' },
    { value: 'gainable', label: 'Gainable' },
    { value: 'PAC_air_air', label: 'PAC air/air réversible' },
    { value: 'autre', label: 'Autre' },
  ],
  ventilation: [
    { value: 'VMC_simple', label: 'VMC simple flux' },
    { value: 'VMC_double', label: 'VMC double flux' },
    { value: 'autre', label: 'Autre' },
  ],
  production_electricite: [
    { value: 'panneaux_pv', label: 'Panneaux photovoltaïques' },
    { value: 'onduleur', label: 'Onduleur' },
    { value: 'eolienne', label: 'Éolienne' },
    { value: 'autre', label: 'Autre' },
  ],
  stockage: [
    { value: 'batterie', label: 'Batterie' },
    { value: 'autre', label: 'Autre' },
  ],
  recharge: [
    { value: 'borne_recharge', label: 'Borne de recharge' },
    { value: 'autre', label: 'Autre' },
  ],
  eau: [
    { value: 'adoucisseur', label: 'Adoucisseur' },
    { value: 'fosse_septique', label: 'Fosse septique' },
    { value: 'micro_station', label: "Micro-station d'épuration" },
    { value: 'pompe_piscine', label: 'Pompe de piscine' },
    { value: 'generateur_eau_atmospherique', label: "Générateur d'eau atmosphérique" },
    { value: 'autre', label: 'Autre' },
  ],
  autre: [{ value: 'autre', label: 'Autre' }],
}

/** Carnet d'information du logement (lot 11). Codes : `MODES_EVACUATION`, `ETIQUETTES_ENERGIE`
 *  (`models/equipement.py`) et `CATEGORIES_CIL` (`models/travaux.py`) — à tenir ENSEMBLE. */
export const MODES_EVACUATION: FieldOption[] = [
  { value: 'ventouse', label: 'Ventouse' }, { value: 'conduit', label: 'Conduit de fumée' },
  { value: 'sans_objet', label: 'Sans objet (pas de combustion)' }, { value: 'inconnu', label: 'Je ne sais pas' },
]
export const ETIQUETTES_ENERGIE: FieldOption[] = [
  ...['A+++', 'A++', 'A+', 'A', 'B', 'C', 'D', 'E', 'F', 'G'].map((c) => ({ value: c, label: c })),
  { value: 'inconnue', label: 'Je ne sais pas' },
]
export const CATEGORIES_CIL: FieldOption[] = [
  { value: 'isolation_toiture', label: 'Isolation de la toiture (combles, rampants, toit-terrasse)' },
  { value: 'isolation_murs', label: "Isolation des murs donnant sur l'extérieur" },
  { value: 'parois_vitrees_portes', label: "Fenêtres et portes donnant sur l'extérieur" },
  { value: 'planchers_bas', label: 'Isolation des planchers bas' },
  { value: 'chauffage_froid_ecs', label: 'Chauffage, climatisation, eau chaude' },
  { value: 'autre', label: "Autres travaux (hors carnet d'information du logement)" },
]

export const UNITES: FieldOption[] = ['kW', 'kWc', 'kWh', 'L'].map((u) => ({ value: u, label: u }))

/** Les valeurs de la fiche Maison, avec leur article : « Votre fiche indique une PAC air/eau de 2016 ».
 *  Deux tables, parce que `gaz` ne se dit pas pareil pour le chauffage et l'eau chaude. */
const CHAUFFAGE_FICHE: Record<string, string> = {
  elec_direct: 'un chauffage électrique direct', PAC_air_eau: 'une PAC air/eau', PAC_air_air: 'une PAC air/air',
  gaz: 'un chauffage au gaz', fioul: 'un chauffage au fioul', bois: 'un chauffage au bois',
  reseau: 'un réseau de chaleur', autre: 'un autre chauffage',
}
const AUTRES_FICHE: Record<string, Record<string, string>> = {
  ecs: {
    ballon_elec: 'un ballon électrique', thermodynamique: 'un ballon thermodynamique', gaz: 'un chauffe-eau gaz',
    solaire: 'un chauffe-eau solaire', instantane: 'un chauffe-eau instantané',
  },
  ventilation: { VMC_simple: 'une VMC simple flux', VMC_double: 'une VMC double flux' },
}

/** La phrase du bandeau de suggestion, à partir de ce que renvoie l'API. */
export function phraseSuggestion(origine: string, valeur: string | null, annee: number | null): string {
  let objet: string
  if (origine === 'chauffage_principal' || origine === 'chauffage_appoint') {
    objet = CHAUFFAGE_FICHE[valeur ?? ''] ?? 'un chauffage'
    if (origine === 'chauffage_appoint') objet += ' en appoint'
  } else if (origine === 'clim') {
    objet = valeur ? `une climatisation (${valeur})` : 'une climatisation'
  } else {
    objet = AUTRES_FICHE[origine]?.[valeur ?? ''] ?? (valeur ?? origine)
  }
  return `Votre fiche indique ${objet}${annee ? ` de ${annee}` : ''}.`
}

export const libelleType = (c: string, t: string) => TYPES[c]?.find((o) => o.value === t)?.label ?? t

/** La question de la fiche `kb/garanties_travaux.md` vers laquelle renvoie « En savoir plus ». */
export const FICHE_GARANTIES = 'Après des travaux, quelles garanties me protègent et que couvre chacune ?'

export function dateFr(iso: string | null | undefined): string {
  if (!iso) return ''
  const [a, m, j] = iso.split('-')
  return `${j}/${m}/${a}`
}
