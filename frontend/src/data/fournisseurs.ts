/**
 * Les fournisseurs d'électricité proposés dans « Énergie ».
 *
 * Liste tenue ici et nulle part ailleurs : elle bouge au gré du marché, et un fournisseur
 * qui disparaît ne doit pas obliger à ouvrir un composant. L'ordre est celui des parts de
 * marché résidentielles, les plus courants d'abord.
 *
 * CE N'EST PAS UNE RECOMMANDATION. Aucun de ces noms n'est partenaire d'Helios, aucun n'est
 * mis en avant — la charte interdit de pousser qui que ce soit. On demande seulement chez
 * qui le foyer est aujourd'hui, pour savoir d'où l'on part.
 */

export interface Fournisseur {
  value: string
  label: string
}

export const FOURNISSEURS: Fournisseur[] = [
  { value: 'edf', label: 'EDF' },
  { value: 'engie', label: 'Engie' },
  { value: 'totalenergies', label: 'TotalEnergies' },
  { value: 'ekwateur', label: 'Ekwateur' },
  { value: 'octopus', label: 'Octopus Energy' },
  { value: 'mint', label: 'Mint Énergie' },
  { value: 'vattenfall', label: 'Vattenfall' },
  { value: 'ilek', label: 'ilek' },
  { value: 'enercoop', label: 'Enercoop' },
  { value: 'autre', label: 'Autre' },
  { value: 'inconnu', label: 'Je ne sais pas' },
]

export function libelleFournisseur(code: string | null, autre: string): string | null {
  if (!code) return null
  if (code === 'autre') return autre.trim() || 'Autre fournisseur'
  return FOURNISSEURS.find((f) => f.value === code)?.label ?? null
}

/**
 * Le chemin du retour : la fiche Maison ne garde que le LIBELLÉ, parce que c'est lui qui
 * se lit dans l'espace client et qui sert à une étude de courtage. On le retrouve ici dans
 * la liste ; ce qui n'y est pas retombe sur « Autre » avec le texte d'origine, jamais sur
 * rien — une réponse déjà donnée ne doit pas se perdre parce que la liste a bougé.
 */
export function fournisseurDepuisLibelle(
  libelle: string | null | undefined,
): { code: string; autre: string } | null {
  const texte = libelle?.trim()
  if (!texte) return null
  const connu = FOURNISSEURS.find(
    (f) => f.value !== 'autre' && f.label.toLowerCase() === texte.toLowerCase())
  return connu ? { code: connu.value, autre: '' } : { code: 'autre', autre: texte }
}
