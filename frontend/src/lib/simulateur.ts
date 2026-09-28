/**
 * Couche de données du simulateur « maison + équipements ».
 *
 * Aucun chiffre n'est calculé ici : tout vient du moteur déterministe côté serveur.
 * Ce fichier ne fait que transporter la configuration, appeler l'API et ranger la
 * réponse. Un seul appel en vol à la fois — le précédent est annulé.
 */

export type Presence = 'absents' | 'partielle' | 'toute_la_journee'
export type Orientation = 'sud' | 'sud_est' | 'sud_ouest' | 'est' | 'ouest' | 'est_ouest'
export type Ombrage = 'aucun' | 'partiel' | 'important'
export type Raccordement = 'monophase' | 'triphase' | 'inconnu'
export type Saison = 'printemps' | 'ete' | 'automne' | 'hiver'

export interface Config {
  adresse?: string | null
  lat?: number | null
  lon?: number | null
  maison: {
    surface_m2: number
    nb_occupants: number
    presence_journee: Presence
    residence_secondaire: boolean
    mois_occupation: number[]
    chauffage: string
    ecs: string
    clim: { present: boolean; deja_installe: boolean; nb_pieces: number; plage: string }
    piscine: { present: boolean; deja_installe: boolean; volume_m3: number; pompe_kw: number | null }
    voiture: {
      present: boolean; deja_installe: boolean; km_an: number
      recharge: string; presente_en_journee: boolean
    }
    conso_connue_kwh_an: number | null
    puissance_souscrite_kva: number
    raccordement: Raccordement
    besoin_secours: boolean
  }
  panneaux: {
    nb_panneaux: number
    orientation: Orientation
    inclinaison: number
    ombrage: Ombrage
    nb_panneaux_carport: number
    surface_toit_m2: number | null
  }
  stockage: {
    nb_packs: number
    batterie_virtuelle: string | null
    palier_virtuel_kwh: number | null
    pilotage: boolean
  }
  hausse_prix_pct_an?: number | null
}

export interface Indicateurs {
  autonomie_pct: number
  autonomie_part_virtuelle_pct: number
  production_valorisee_pct: number
  facture_mois_eur: number
  facture_mois_reference_eur: number
  economie_1re_annee_eur: number
  gain_net_25_ans_eur: number
  temps_retour_ans: number | null
  rendement_annuel_pct: number | null
  puissance_kwc: number
  nb_usages_pilotes: number
  conso_estimee: boolean
}

export interface PointJournee {
  production: number; consommation: number; direct: number
  charge: number; decharge: number; injecte: number; ecrete: number
  stocke_virtuel: number; restitue_virtuel: number; achat: number
}

export interface Resultat {
  lieu: { commune: string | null; lat: number; lon: number; precision_deg: number }
  production: {
    annuel_kwh: number; par_kwc_kwh: number
    kwc_toit: number; kwc_carport: number; pertes_pct: number
  }
  panneaux_max_toit: number | null
  version_moteur: string
  indicateurs: Indicateurs
  bilan_annuel: Record<string, number>
  bilan_mensuel: (Record<string, number> & { mois: number })[]
  journees: Record<Saison, PointJournee[]>
  stockage: {
    batterie_physique: { nb_packs: number; capacite_kwh: number; charge_kwh: number; restitue_kwh: number }
    batterie_virtuelle: null | {
      code: string; label: string; stocke_kwh: number; restitue_kwh: number
      abonnement_annuel_eur: number; cout_restitution_annuel_eur: number
      palier_kwh: number | null; credit_maxi_kwh: number; grille_complete: boolean
      fournisseur_impose: string | null; note: string
      conseil: string; recommandee: boolean
    }
    pilotage: { actif: boolean; nb_usages: number }
  }
  investissement: {
    panneaux_eur: number; carport_eur: number; batterie_eur: number
    activation_virtuelle_eur: number; materiel_virtuel_eur: number; total_eur: number
    tva_pct: number; tva_raison: string
  }
  economie: {
    facture_mois_eur: number; facture_mois_reference_eur: number
    abonnement_elec_mois_eur: number; abonnement_virtuel_mois_eur: number
    economie_1re_annee_eur: number; gain_net_25_ans_eur: number
    temps_retour_ans: number | null; rendement_annuel_pct: number | null
    tresorerie: { annee: number; flux_eur: number; cumul_eur: number }[]
    prix_kwh_eur: number; hausse_prix_pct_an: number
  }
  consommation: {
    annuel_kwh: number; estimee: boolean
    detail_kwh: Record<string, number>; equipements_ajoutes: string[]
  }
  alertes: { niveau: string; texte: string }[]
  hypotheses: { libelle: string; valeur: string; statut: string }[]
}

export interface Option {
  code: string; label: string; nb_panneaux: number; puissance_kwc: number
  investissement_eur: number; tva_pct: number; autonomie_pct: number
  facture_mois_eur: number; economie_1re_annee_eur: number
  gain_net_25_ans_eur: number; temps_retour_ans: number | null
  rendement_annuel_pct: number | null
  configuration: {
    nb_panneaux: number; nb_panneaux_carport: number; nb_packs: number
    batterie_virtuelle: string | null; pilotage: boolean
  }
  secours_possible: boolean
  note_secours: string | null
}

export interface ProchaineEtape {
  libelle: string
  gain_annuel_eur: number
  investissement_eur: number
  appliquer: Partial<{
    nb_panneaux: number; pilotage: boolean
    batterie_virtuelle: string; nb_packs: number
  }>
}

export interface Objectif {
  code: string; libelle: string; atteint: boolean; valeur: string
}

export interface Options {
  options: Option[]
  recommandee: string | null
  prochaine_etape: ProchaineEtape | null
  objectifs: Objectif[]
}

export const CONFIG_INITIALE: Config = {
  adresse: null,
  lat: null,
  lon: null,
  maison: {
    surface_m2: 100,
    nb_occupants: 3,
    presence_journee: 'absents',
    residence_secondaire: false,
    mois_occupation: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    chauffage: 'elec_direct',
    ecs: 'ballon_elec',
    clim: { present: false, deja_installe: true, nb_pieces: 1, plage: 'apres_midi' },
    piscine: { present: false, deja_installe: true, volume_m3: 40, pompe_kw: null },
    voiture: { present: false, deja_installe: true, km_an: 12000, recharge: 'nuit', presente_en_journee: false },
    conso_connue_kwh_an: null,
    puissance_souscrite_kva: 9,
    raccordement: 'inconnu',
    besoin_secours: false,
  },
  panneaux: {
    nb_panneaux: 0,
    orientation: 'sud',
    inclinaison: 30,
    ombrage: 'aucun',
    nb_panneaux_carport: 0,
    surface_toit_m2: null,
  },
  stockage: { nb_packs: 0, batterie_virtuelle: null, palier_virtuel_kwh: null, pilotage: false },
  hausse_prix_pct_an: null,
}

export const ORIENTATIONS: { value: Orientation; label: string }[] = [
  { value: 'sud', label: 'Sud' },
  { value: 'sud_est', label: 'Sud-Est' },
  { value: 'sud_ouest', label: 'Sud-Ouest' },
  { value: 'est', label: 'Est' },
  { value: 'ouest', label: 'Ouest' },
  { value: 'est_ouest', label: 'Est-Ouest (deux pans)' },
]

export const OMBRAGES: { value: Ombrage; label: string }[] = [
  { value: 'aucun', label: 'Aucun' },
  { value: 'partiel', label: 'Partiel' },
  { value: 'important', label: 'Important' },
]

export const CHAUFFAGES = [
  { value: 'elec_direct', label: 'Radiateurs électriques' },
  { value: 'PAC_air_eau', label: 'Pompe à chaleur air/eau' },
  { value: 'PAC_air_air', label: 'Pompe à chaleur air/air' },
  { value: 'gaz', label: 'Gaz' },
  { value: 'fioul', label: 'Fioul' },
  { value: 'bois', label: 'Bois' },
  { value: 'reseau', label: 'Réseau de chaleur' },
  { value: 'autre', label: 'Autre' },
]

export const ECS_OPTIONS = [
  { value: 'ballon_elec', label: 'Ballon électrique' },
  { value: 'thermodynamique', label: 'Ballon thermodynamique' },
  { value: 'gaz', label: 'Gaz' },
  { value: 'solaire', label: 'Chauffe-eau solaire' },
  { value: 'instantane', label: 'Production instantanée' },
]

export const PRESENCES: { value: Presence; label: string }[] = [
  { value: 'absents', label: 'Absents en journée' },
  { value: 'partielle', label: 'Présents une partie de la journée' },
  { value: 'toute_la_journee', label: 'Présents toute la journée' },
]

export const SAISONS: { value: Saison; label: string }[] = [
  { value: 'printemps', label: 'Printemps' },
  { value: 'ete', label: 'Été' },
  { value: 'automne', label: 'Automne' },
  { value: 'hiver', label: 'Hiver' },
]

export const MOIS_COURTS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

export class ErreurSimulateur extends Error {
  readonly statut: number
  constructor(message: string, statut: number) {
    super(message)
    this.statut = statut
  }
}

async function poster<T>(chemin: string, config: Config, signal?: AbortSignal): Promise<T> {
  const reponse = await fetch(`/api${chemin}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
    signal,
  })
  if (!reponse.ok) {
    let detail = 'Le calcul n’a pas abouti.'
    try {
      const corps = await reponse.json()
      if (typeof corps.detail === 'string') detail = corps.detail
    } catch {
      /* réponse non JSON : on garde le message générique */
    }
    throw new ErreurSimulateur(detail, reponse.status)
  }
  return reponse.json() as Promise<T>
}

export const calculer = (config: Config, signal?: AbortSignal) =>
  poster<Resultat>('/simulateur/calcul', config, signal)

export const chercherOptions = (config: Config, signal?: AbortSignal) =>
  poster<Options>('/simulateur/options', config, signal)

export interface SuggestionAdresse {
  label: string
  commune: string
  lat: number
  lon: number
}

/** Autocomplétion d'adresse — API Adresse (data.gouv.fr), publique et sans clé. */
export async function chercherAdresses(
  texte: string,
  signal?: AbortSignal,
): Promise<SuggestionAdresse[]> {
  if (texte.trim().length < 3) return []
  const url = `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(texte)}&limit=5`
  const reponse = await fetch(url, { signal })
  if (!reponse.ok) return []
  const corps = await reponse.json()
  return (corps.features ?? []).map((f: any) => ({
    label: f.properties.label as string,
    commune: f.properties.city as string,
    lat: f.geometry.coordinates[1] as number,
    lon: f.geometry.coordinates[0] as number,
  }))
}

/**
 * Partage par URL : seulement la commune et des coordonnées arrondies, JAMAIS l'adresse
 * complète. Une URL se recopie, s'envoie et se retrouve dans des journaux de serveur.
 */
export function versUrl(config: Config, commune: string | null): string {
  const arrondi = (v: number | null | undefined) =>
    v === null || v === undefined ? null : Math.round(v * 20) / 20
  const compact = {
    ...config,
    adresse: commune,
    lat: arrondi(config.lat),
    lon: arrondi(config.lon),
  }
  return btoa(encodeURIComponent(JSON.stringify(compact)))
}

export function depuisUrl(code: string): Config | null {
  try {
    const brut = JSON.parse(decodeURIComponent(atob(code)))
    // On refusionne sur la configuration initiale : une URL ancienne à qui il manque un
    // champ doit continuer de marcher, avec le défaut pour ce champ.
    return {
      ...CONFIG_INITIALE,
      ...brut,
      maison: { ...CONFIG_INITIALE.maison, ...(brut.maison ?? {}) },
      panneaux: { ...CONFIG_INITIALE.panneaux, ...(brut.panneaux ?? {}) },
      stockage: { ...CONFIG_INITIALE.stockage, ...(brut.stockage ?? {}) },
    }
  } catch {
    return null
  }
}

export const euros = (v: number | null | undefined) =>
  v === null || v === undefined ? '—' : `${Math.round(v).toLocaleString('fr-FR')} €`

export const kwh = (v: number | null | undefined) =>
  v === null || v === undefined ? '—' : `${Math.round(v).toLocaleString('fr-FR')} kWh`

export const ans = (v: number | null | undefined) =>
  v === null || v === undefined ? 'jamais sur 25 ans' : `${v} ans`
