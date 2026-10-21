/**
 * Libellés des pièces et émetteurs (carnet, lot 2). Les CODES viennent de
 * `api/app/models/piece.py` : les deux listes se tiennent à jour ENSEMBLE.
 */
import type { FieldOption } from '../fiche/types'

export const TYPES_PIECE: FieldOption[] = [
  { value: 'sejour', label: 'Séjour' }, { value: 'cuisine', label: 'Cuisine' },
  { value: 'chambre', label: 'Chambre' }, { value: 'salle_de_bain', label: 'Salle de bain' },
  { value: 'wc', label: 'WC' }, { value: 'bureau', label: 'Bureau' }, { value: 'entree', label: 'Entrée' },
  { value: 'buanderie', label: 'Buanderie' }, { value: 'garage', label: 'Garage' },
  { value: 'veranda', label: 'Véranda' }, { value: 'combles_amenages', label: 'Combles aménagés' },
  { value: 'autre', label: 'Autre' },
]

export const ORIENTATIONS: FieldOption[] = [
  ['N', 'Nord'], ['NE', 'Nord-est'], ['E', 'Est'], ['SE', 'Sud-est'],
  ['S', 'Sud'], ['SO', 'Sud-ouest'], ['O', 'Ouest'], ['NO', 'Nord-ouest'],
].map(([value, label]) => ({ value, label }))

export const NIVEAUX: FieldOption[] = [
  { value: '-1', label: 'Sous-sol' }, { value: '0', label: 'Rez-de-chaussée' },
  { value: '1', label: '1er étage' }, { value: '2', label: '2e étage' }, { value: '3', label: '3e étage' },
]

export const libelleNiveau = (n: number) =>
  NIVEAUX.find((o) => o.value === String(n))?.label ?? `${n}e étage`

/** [singulier, pluriel] — « 2 radiateurs à eau ». */
const EMETTEURS: Record<string, [string, string]> = {
  radiateur_eau: ['radiateur à eau', 'radiateurs à eau'],
  convecteur: ['convecteur', 'convecteurs'],
  panneau_rayonnant: ['panneau rayonnant', 'panneaux rayonnants'],
  radiateur_inertie: ['radiateur à inertie', 'radiateurs à inertie'],
  seche_serviettes: ['sèche-serviettes', 'sèche-serviettes'],
  plancher_chauffant_eau: ['plancher chauffant à eau', 'planchers chauffants à eau'],
  plancher_chauffant_elec: ['plancher chauffant électrique', 'planchers chauffants électriques'],
  unite_interieure_clim: ['unité de climatisation', 'unités de climatisation'],
  poele_bois: ['poêle à bois', 'poêles à bois'],
  poele_granules: ['poêle à granulés', 'poêles à granulés'],
  cheminee: ['cheminée', 'cheminées'],
  autre: ['autre émetteur', 'autres émetteurs'],
}

export const TYPES_EMETTEUR: FieldOption[] = Object.entries(EMETTEURS).map(([value, [s]]) => ({
  value, label: s.charAt(0).toUpperCase() + s.slice(1),
}))

export const libelleEmetteur = (type: string, nombre: number) =>
  (EMETTEURS[type] ?? [type, type])[nombre > 1 ? 1 : 0]

export type Emetteur = {
  id: string; piece_id: string; type: string; nombre: number; puissance_w: number | null
  robinet_thermostatique: boolean | null; programmable: boolean | null; equipement_id: string | null; note: string | null
}

/** « 2 radiateurs à eau, robinets thermostatiques · 1 sèche-serviettes » */
export function phraseEmetteurs(emetteurs: Emetteur[]): string {
  return emetteurs.map((e) => {
    let s = `${e.nombre} ${libelleEmetteur(e.type, e.nombre)}`
    if (e.robinet_thermostatique) s += e.nombre > 1 ? ', robinets thermostatiques' : ', robinet thermostatique'
    if (e.programmable) s += ', programmable' + (e.nombre > 1 ? 's' : '')
    return s
  }).join(' · ')
}
