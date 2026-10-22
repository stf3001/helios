/** Libellés des mises en relation, lot 3 — recopiés de l'API : `services/conformite.py`
 *  (justificatifs) et `services/contestations.py` (motifs). Les deux côtés se tiennent à jour ENSEMBLE. */

export const JUSTIFICATIFS: [string, string][] = [
  ['kbis', 'Extrait Kbis'], ['decennale', "Attestation d'assurance décennale"], ['rge', 'Qualification RGE'],
]
export const LIBELLE_JUSTIFICATIF: Record<string, string> = Object.fromEntries(JUSTIFICATIFS)

export const ETAT_JUSTIFICATIF: Record<string, { label: string; style: string }> = {
  valide: { label: 'valide', style: 'border-leaf/40 bg-leaf/10 text-leaf' },
  bientot: { label: 'échéance proche', style: 'border-sun/50 bg-sun/10 text-dark/80' },
  expire: { label: 'expiré', style: 'border-primary/40 bg-primary/10 text-primary' },
  manquant: { label: 'manquant', style: 'border-terra/40 bg-terra/10 text-terra' },
}

export const MOTIFS_CONTESTATION: [string, string][] = [
  ['coordonnees_fausses', 'Coordonnées fausses'],
  ['hors_zone_ou_metier', 'Hors de ma zone ou de mes métiers'],
  ['doublon', 'Doublon : même foyer, même métier, déjà reçu dans les 12 mois (par Hélios ou en direct)'],
  ['injoignable', 'Foyer injoignable après trois essais dans ses créneaux'],
]

export const STATUT_CONTESTATION: Record<string, string> = {
  en_attente: 'en attente', acceptee: 'acceptée', refusee: 'refusée',
}

export function dateCourte(iso: string | null | undefined): string {
  return iso ? new Date(iso.length === 10 ? `${iso}T12:00:00` : iso).toLocaleDateString('fr-FR') : '—'
}
