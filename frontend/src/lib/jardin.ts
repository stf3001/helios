/**
 * Le jardin nourricier, côté écran : les types et l'appel.
 *
 * Ce fichier ne calcule RIEN. Comme pour le simulateur solaire, tous les chiffres
 * viennent du moteur (`/api/jardin/calcul`, `services/jardin.py`) : un calcul recopié
 * ici finirait tôt ou tard par ne plus dire la même chose que celui du serveur.
 *
 * `heures_jour` est une contrainte d'ENTRÉE, pas un résultat — voir le commentaire en
 * tête de `services/jardin.py`, qui explique pourquoi le calcul est retourné.
 */

export type Conduite = 'debutant' | 'rodee'

export interface JardinConfig {
  personnes: number
  heures_jour: number
  conduite: Conduite
  code_postal: string | null
}

export interface JardinMois {
  mois: number
  nom: string
  heures: number
  heures_jour: number
}

export interface JardinResultat {
  personnes: number
  conduite: Conduite
  zone: 'nord' | 'sud' | null
  besoin_kg_an: number
  budget_heures_jour: number
  surface_cultivee_m2: number
  surface_totale_m2: number
  recolte_kg_an: number
  couverture_pct: number
  heures_an: number
  mensuel: JardinMois[]
  pointe: { mois: string; heures_jour: number }
  autonomie: {
    surface_cultivee_m2: number
    surface_totale_m2: number
    heures_jour: number
    atteinte: boolean
  }
  hypotheses: { cle: string; valeur: string; statut: string; detail: string }[]
  avertissement: string
}

export const JARDIN_INITIAL: JardinConfig = {
  personnes: 2,
  // Une heure par jour : c'est le budget de départ, celui qui ne fait peur à personne.
  heures_jour: 1,
  conduite: 'debutant',
  code_postal: null,
}

export async function calculerJardin(
  config: JardinConfig,
  signal?: AbortSignal,
): Promise<JardinResultat> {
  const reponse = await fetch('/api/jardin/calcul', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
    signal,
  })
  if (!reponse.ok) throw new Error('Le calcul du jardin n’a pas abouti.')
  return reponse.json() as Promise<JardinResultat>
}
