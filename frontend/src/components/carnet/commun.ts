/**
 * Outils partagés par le bloc « À faire », le calendrier et le journal (carnet, lot 4).
 *
 * Ces trois vues vivent à des endroits différents de l'espace (en tête, et dans « Ma
 * maison ») : quand l'une écrit (« C'est fait », un équipement ajouté), les autres doivent
 * se recharger. Un événement de fenêtre suffit, sans état global ni dépendance.
 */
import { useEffect } from 'react'
import { libelleType } from './libelles'

const EVENEMENT = 'carnet:maj'

export function signalerMaj() {
  window.dispatchEvent(new Event(EVENEMENT))
}

/** Ouvre le formulaire du journal pré-rempli (phase 2 : « Noter une fissure » depuis les risques). */
const OUVRIR_JOURNAL = 'carnet:ouvrir-journal'
export function ouvrirJournal(brouillon: Record<string, string>) {
  window.dispatchEvent(new CustomEvent(OUVRIR_JOURNAL, { detail: brouillon }))
  document.getElementById('journal-maison')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
export function useOuvrirJournal(ouvrir: (brouillon: Record<string, string>) => void) {
  useEffect(() => {
    const ecouter = (e: Event) => ouvrir((e as CustomEvent).detail)
    window.addEventListener(OUVRIR_JOURNAL, ecouter)
    return () => window.removeEventListener(OUVRIR_JOURNAL, ecouter)
  }, [ouvrir])
}

export function useMaj(recharger: () => void) {
  useEffect(() => {
    window.addEventListener(EVENEMENT, recharger)
    return () => window.removeEventListener(EVENEMENT, recharger)
  }, [recharger])
}

export type Echeance = {
  tache_id: string; equipement_id: string | null; libelle: string; qui: string; nature: string
  source: { type: string; titre: string; url: string | null } | null; fiche_kb: string | null; note: string | null
  regle: string; date_reference: string | null; provenance: string; reference_supposee: boolean
  echeance: string | null; statut: 'en_retard' | 'ce_mois' | 'bientot' | 'a_planifier' | 'plus_tard'
  periode_conseillee: number[] | null; mention_puissance: string | null
  // Lot 8 : à qui revient la tâche. `pour_moi: false` → affichée en lecture, avec `mention`.
  responsable: 'occupant' | 'proprietaire'; pour_moi: boolean; mention: string | null
}

/** Ce que l'espace montre selon le statut du foyer (`services/parcours.py`). */
export type Parcours = {
  profil: 'proprietaire' | 'locataire' | 'acheteur'; voit_travaux: boolean; voit_projets_lourds: boolean
  avant_d_acheter: boolean; note_proprietaire: boolean
}

export type EquipementNom = { id: string; categorie: string; type: string; marque: string | null; en_service: boolean }

export const QUI: Record<string, string> = { soi: 'Vous-même', pro: 'Un professionnel', soi_ou_pro: 'Vous ou un pro' }

export const nomEquipement = (e: EquipementNom | undefined) =>
  e ? [libelleType(e.categorie, e.type), e.marque].filter(Boolean).join(' · ') : 'La maison'

// Date LOCALE (le format suédois donne AAAA-MM-JJ) : toISOString passerait en UTC, donc à la veille la nuit.
export const aujourdhui = () => new Date().toLocaleDateString('sv-SE')

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

const jourJ = (iso: string) => new Date(`${iso}T00:00:00`)

/** « 12 novembre », avec l'année seulement si ce n'est pas l'année en cours. */
export function dateLongue(iso: string): string {
  const d = jourJ(iso)
  const annee = d.getFullYear() !== new Date().getFullYear() ? ` ${d.getFullYear()}` : ''
  return `${d.getDate() === 1 ? '1er' : d.getDate()} ${MOIS[d.getMonth()]}${annee}`
}

/** « depuis 3 semaines » pour une échéance passée, « avant le 12 novembre » sinon. */
export function echeanceRelative(iso: string | null): string {
  if (!iso) return 'date à préciser'
  const jours = Math.round((Date.now() - jourJ(iso).getTime()) / 86400000)
  if (jours <= 0) return `avant le ${dateLongue(iso)}`
  if (jours < 14) return `depuis ${jours} jour${jours > 1 ? 's' : ''}`
  if (jours < 60) return `depuis ${Math.round(jours / 7)} semaines`
  if (jours < 730) return `depuis ${Math.round(jours / 30.4)} mois`
  return `depuis ${Math.floor(jours / 365.25)} ans`
}
