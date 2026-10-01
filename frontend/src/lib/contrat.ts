/**
 * Ce que le foyer déclare de son CONTRAT : option tarifaire, heures creuses, fournisseur,
 * tarif bloqué.
 *
 * POURQUOI CE FICHIER EXISTE, ET POURQUOI CES CHAMPS NE SONT PAS DANS `Config` —
 * `api/app/schemas/simulateur.py` est en `extra="forbid"`. Un champ que le moteur ne
 * connaît pas fait échouer CHAQUE calcul en 422, et l'écran se remplit de tirets sans dire
 * pourquoi (c'est exactement la panne du 29/09/2026, racontée dans `SimulateurSolaire.tsx`).
 * Ces données vivent donc À CÔTÉ de la configuration, comme le jardin le fait déjà, et
 * n'entrent ni dans l'appel au moteur ni dans l'URL de partage.
 *
 * Elles ne changent AUCUN chiffre du panneau de droite : c'est de la collecte, pas du
 * calcul. Elles rejoignent la fiche Maison d'un visiteur connecté (`PATCH /api/houses/me`)
 * et servent plus tard, dans l'espace client, à juger une offre de courtage.
 */

/* Les memes jetons que la fiche Maison (`OptionTarifaire` dans
 * `api/app/schemas/house.py`) : « HPHC » s'ecrit en capitales la-bas, donc ici aussi.
 * Deux orthographes pour la meme chose, c'est une valeur perdue au premier aller-retour. */
export type OptionTarifaire = 'base' | 'HPHC' | 'tempo'

export const OPTIONS_TARIFAIRES: { value: OptionTarifaire; label: string }[] = [
  { value: 'base', label: 'Base' },
  { value: 'HPHC', label: 'Heures pleines – Heures creuses' },
  { value: 'tempo', label: 'Tempo' },
]

/** Les puissances réellement proposées au compteur résidentiel, en kVA. */
export const PUISSANCES_KVA = [3, 6, 9, 12, 15, 18, 24, 30, 36] as const

/** Une plage d'heures creuses. Chaîne vide = non renseigné (et non « minuit »). */
export interface Plage {
  debut: string
  fin: string
}

export type TarifBloque = 'oui' | 'non' | 'inconnu'

export interface Contrat {
  option_tarifaire: OptionTarifaire
  /** Toujours deux plages : le visiteur peut n'en remplir qu'une et laisser l'autre vide. */
  heures_creuses: [Plage, Plage]
  fournisseur: string | null
  /** Saisi à la main quand `fournisseur === 'autre'`. */
  fournisseur_autre: string
  tarif_bloque: TarifBloque | null
  tarif_bloque_mois: number | null
}

export const PLAGE_VIDE: Plage = { debut: '', fin: '' }

/**
 * Les défauts : l'option et les plages les plus répandues chez Enedis (une plage de deux
 * heures l'après-midi, une de six heures la nuit). Ils sont présents dès le premier
 * chargement — un écran vide ne dit pas ce qu'on attend.
 */
export const CONTRAT_INITIAL: Contrat = {
  option_tarifaire: 'HPHC',
  heures_creuses: [{ debut: '13:00', fin: '15:00' }, { debut: '01:00', fin: '07:00' }],
  fournisseur: null,
  fournisseur_autre: '',
  tarif_bloque: null,
  tarif_bloque_mois: null,
}

const HEURE = /^([01]\d|2[0-3]):([0-5]\d)$/

function minutes(h: string): number | null {
  const m = HEURE.exec(h)
  return m ? Number(m[1]) * 60 + Number(m[2]) : null
}

/** Une plage dure de son début à sa fin, en passant minuit si la fin précède le début. */
export function dureeMinutes(plage: Plage): number | null {
  const debut = minutes(plage.debut)
  const fin = minutes(plage.fin)
  if (debut === null || fin === null) return null
  return fin === debut ? 0 : (fin - debut + 1440) % 1440
}

export interface VerdictHeuresCreuses {
  /** Ce qui empêche d'enregistrer : affiché en rouge sous le bloc. */
  erreur: string | null
  /** Ce qui étonne sans empêcher : affiché en gris, jamais bloquant. */
  rappel: string | null
  /** Le total des deux plages, en minutes, ou `null` si rien n'est complet. */
  total: number | null
}

/**
 * La validation des heures creuses.
 *
 * Trois règles, et une seule bloque : il faut au moins une plage complète, une plage à
 * moitié remplie est une erreur de saisie, et un total différent de huit heures est
 * seulement SIGNALÉ — les contrats hors normes existent, et refuser la saisie de quelqu'un
 * qui a sous les yeux sa propre facture serait lui donner tort contre un document.
 */
export function verifierHeuresCreuses(plages: [Plage, Plage]): VerdictHeuresCreuses {
  const moities = plages.filter((p) => (p.debut === '') !== (p.fin === ''))
  if (moities.length > 0) {
    return {
      erreur: 'Une plage demande une heure de début ET une heure de fin. Complétez-la, ou effacez-la.',
      rappel: null,
      total: null,
    }
  }

  const durees = plages.map(dureeMinutes).filter((d): d is number => d !== null)
  if (durees.length === 0) {
    return { erreur: 'Renseignez au moins une plage d’heures creuses.', rappel: null, total: null }
  }

  const total = durees.reduce((a, b) => a + b, 0)
  const heures = Math.floor(total / 60)
  const reste = total % 60
  const ecrit = reste === 0 ? `${heures} h` : `${heures} h ${String(reste).padStart(2, '0')}`
  return {
    erreur: null,
    rappel: total === 480 ? null : `Vous déclarez ${ecrit} d’heures creuses — c’est habituellement 8 h au total. Vérifiez sur votre facture si ce n’est pas voulu.`,
    total,
  }
}

/**
 * Ce qui part dans la fiche Maison. Les clés sont celles des colonnes de `houses`, pas
 * celles de cet écran : la fiche est le magasin, cet objet n'est que son reflet.
 */
export function versFicheMaison(contrat: Contrat, fournisseurLibelle: string | null) {
  const plage = (p: Plage) => (p.debut && p.fin ? { debut: p.debut, fin: p.fin } : null)
  return {
    option_tarifaire: contrat.option_tarifaire,
    heures_creuses: contrat.option_tarifaire === 'HPHC'
      ? contrat.heures_creuses.map(plage).filter((p) => p !== null)
      : null,
    fournisseur_actuel: fournisseurLibelle,
    tarif_bloque: contrat.tarif_bloque,
    tarif_bloque_mois_restants: contrat.tarif_bloque === 'oui' ? contrat.tarif_bloque_mois : null,
  }
}
