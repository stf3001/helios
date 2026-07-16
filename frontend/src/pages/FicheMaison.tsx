import { useEffect, useState, type FormEvent } from 'react'
import BlockCard from '../components/fiche/BlockCard'
import CompletenessBar from '../components/fiche/CompletenessBar'
import type { Draft, FieldSpec, FieldValue } from '../components/fiche/types'
import { useAuth } from '../context/AuthContext'

const IDENTITE_FIELDS: FieldSpec[] = [
  { key: 'code_postal', label: 'Code postal', type: 'text', help: 'Requis — 5 chiffres' },
  { key: 'type_logement', label: 'Type de logement', type: 'select', options: [
    { value: 'maison', label: 'Maison' }, { value: 'appartement', label: 'Appartement' },
  ] },
  { key: 'statut', label: 'Statut', type: 'select', options: [
    { value: 'proprietaire', label: 'Propriétaire' }, { value: 'locataire', label: 'Locataire' }, { value: 'en_achat', label: 'En cours d\'achat' },
  ] },
  { key: 'annee_construction', label: 'Année de construction', type: 'select', options: [
    { value: 'avant_1948', label: 'Avant 1948' }, { value: '1948_1974', label: '1948 – 1974' },
    { value: '1975_1988', label: '1975 – 1988' }, { value: '1989_2000', label: '1989 – 2000' },
    { value: '2001_2012', label: '2001 – 2012' }, { value: 'apres_2012', label: 'Après 2012' },
  ] },
  { key: 'surface_habitable', label: 'Surface habitable (m²)', type: 'number', min: 1, max: 2000 },
  { key: 'nb_niveaux', label: 'Nombre de niveaux', type: 'number', min: 1, max: 20 },
  { key: 'nb_occupants', label: "Nombre d'occupants", type: 'number', min: 0, max: 50 },
  { key: 'residence_principale', label: 'Résidence principale ?', type: 'boolean' },
]

const NIVEAU_ISOLATION_OPTIONS = [
  { value: 'aucune', label: 'Aucune' }, { value: 'partielle', label: 'Partielle' },
  { value: 'bonne', label: 'Bonne' }, { value: 'inconnue', label: 'Inconnue' },
]

const ENVELOPPE_FIELDS: FieldSpec[] = [
  { key: 'isolation_combles', label: 'Isolation combles', type: 'select', options: NIVEAU_ISOLATION_OPTIONS },
  { key: 'isolation_combles_annee', label: 'Année isolation combles', type: 'number', min: 1900, max: 2100 },
  { key: 'isolation_murs', label: 'Isolation murs', type: 'select', options: NIVEAU_ISOLATION_OPTIONS },
  { key: 'isolation_murs_annee', label: 'Année isolation murs', type: 'number', min: 1900, max: 2100 },
  { key: 'isolation_plancher', label: 'Isolation plancher', type: 'select', options: NIVEAU_ISOLATION_OPTIONS },
  { key: 'isolation_plancher_annee', label: 'Année isolation plancher', type: 'number', min: 1900, max: 2100 },
  { key: 'menuiseries', label: 'Menuiseries', type: 'select', options: [
    { value: 'simple', label: 'Simple vitrage' }, { value: 'double', label: 'Double vitrage' },
    { value: 'double_recent', label: 'Double vitrage récent' }, { value: 'triple', label: 'Triple vitrage' },
  ] },
  { key: 'menuiseries_annee', label: 'Année menuiseries', type: 'number', min: 1900, max: 2100 },
  { key: 'ventilation', label: 'Ventilation', type: 'select', options: [
    { value: 'aucune', label: 'Aucune' }, { value: 'naturelle', label: 'Naturelle' },
    { value: 'VMC_simple', label: 'VMC simple flux' }, { value: 'VMC_double', label: 'VMC double flux' },
    { value: 'inconnue', label: 'Inconnue' },
  ] },
  { key: 'dpe_lettre', label: 'DPE', type: 'select', options: ['A', 'B', 'C', 'D', 'E', 'F', 'G'].map((l) => ({ value: l, label: l })) },
  { key: 'dpe_annee', label: 'Année du DPE', type: 'number', min: 1900, max: 2100 },
]

const CHAUFFAGE_OPTIONS = [
  { value: 'elec_direct', label: 'Électrique direct' }, { value: 'PAC_air_eau', label: 'PAC air-eau' },
  { value: 'PAC_air_air', label: 'PAC air-air' }, { value: 'gaz', label: 'Gaz' }, { value: 'fioul', label: 'Fioul' },
  { value: 'bois', label: 'Bois' }, { value: 'reseau', label: 'Réseau de chaleur' }, { value: 'autre', label: 'Autre' },
]

const SYSTEMES_FIELDS: FieldSpec[] = [
  { key: 'chauffage_principal', label: 'Chauffage principal', type: 'select', options: CHAUFFAGE_OPTIONS },
  { key: 'chauffage_principal_annee', label: "Année d'installation", type: 'number', min: 1900, max: 2100 },
  { key: 'chauffage_appoint', label: "Chauffage d'appoint", type: 'select', options: CHAUFFAGE_OPTIONS },
  { key: 'chauffage_appoint_annee', label: "Année d'installation (appoint)", type: 'number', min: 1900, max: 2100 },
  { key: 'ecs', label: "Eau chaude sanitaire", type: 'select', options: [
    { value: 'ballon_elec', label: 'Ballon électrique' }, { value: 'thermodynamique', label: 'Thermodynamique' },
    { value: 'gaz', label: 'Gaz' }, { value: 'solaire', label: 'Solaire' }, { value: 'instantane', label: 'Instantané' },
  ] },
  { key: 'ecs_annee', label: 'Année ECS', type: 'number', min: 1900, max: 2100 },
  { key: 'clim', label: 'Climatisation ?', type: 'boolean' },
  { key: 'clim_type', label: 'Type de climatisation', type: 'text' },
  { key: 'regulation', label: 'Régulation du chauffage', type: 'select', options: [
    { value: 'aucune', label: 'Aucune' }, { value: 'thermostat', label: 'Thermostat' },
    { value: 'programmable', label: 'Programmable' }, { value: 'connecte', label: 'Connectée' },
  ] },
]

const ENERGIE_FIELDS: FieldSpec[] = [
  { key: 'conso_elec_kwh_an', label: 'Consommation électrique (kWh/an)', type: 'number', min: 0 },
  { key: 'conso_autre_energie_type', label: 'Autre énergie (type)', type: 'text' },
  { key: 'conso_autre_energie_qte', label: 'Autre énergie (quantité/an)', type: 'number', min: 0 },
  { key: 'puissance_souscrite', label: 'Puissance souscrite (kVA)', type: 'select', options: ['3', '6', '9', '12', '15', '18', '24', '30', '36'].map((v) => ({ value: v, label: `${v} kVA` })) },
  { key: 'option_tarifaire', label: 'Option tarifaire', type: 'select', options: [
    { value: 'base', label: 'Base' }, { value: 'HPHC', label: 'Heures pleines / creuses' }, { value: 'tempo', label: 'Tempo' },
  ] },
]

const PROJET_FIELDS: FieldSpec[] = [
  { key: 'objectifs', label: 'Vos objectifs', type: 'multiselect', options: [
    { value: 'reduire_facture', label: 'Réduire la facture' }, { value: 'confort_hiver', label: 'Confort hiver' },
    { value: 'confort_ete', label: 'Confort été' }, { value: 'autonomie', label: 'Autonomie' },
    { value: 'ecologie', label: 'Écologie' }, { value: 'valoriser_bien', label: 'Valoriser le bien' },
    { value: 'vendre_louer', label: 'Vendre / louer' },
  ] },
  { key: 'budget_envisage', label: 'Budget envisagé', type: 'select', options: [
    { value: '<5k', label: 'Moins de 5 000 €' }, { value: '5-15k', label: '5 000 – 15 000 €' },
    { value: '15-30k', label: '15 000 – 30 000 €' }, { value: '30k+', label: 'Plus de 30 000 €' },
    { value: 'ne_sait_pas', label: 'Ne sait pas encore' },
  ] },
  { key: 'horizon', label: 'Horizon des travaux', type: 'select', options: [
    { value: '<6mois', label: 'Moins de 6 mois' }, { value: '6-24mois', label: '6 à 24 mois' }, { value: 'reflexion', label: 'En réflexion' },
  ] },
  { key: 'travaux_deja_faits', label: 'Travaux déjà réalisés', type: 'textarea' },
  { key: 'contraintes', label: 'Contraintes (copropriété, site classé…)', type: 'textarea' },
]

const TOITURE_FIELDS: FieldSpec[] = [
  { key: 'orientation_toiture', label: 'Orientation de la toiture', type: 'text', help: 'ex. sud, sud-ouest…' },
  { key: 'surface_toit_exploitable', label: 'Surface de toit exploitable (m²)', type: 'number', min: 0 },
  { key: 'ombrage', label: 'Ombrage', type: 'select', options: [
    { value: 'aucun', label: 'Aucun' }, { value: 'partiel', label: 'Partiel' }, { value: 'important', label: 'Important' },
  ] },
  { key: 'pente', label: 'Pente (degrés)', type: 'number', min: 0, max: 90 },
]

export default function FicheMaison() {
  const { user, authFetch } = useAuth()
  const [house, setHouse] = useState<Record<string, unknown> | null>(null)
  const [draft, setDraft] = useState<Draft>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newCodePostal, setNewCodePostal] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    authFetch('/api/houses/me')
      .then(async (res) => {
        if (res.status === 404) {
          setHouse(null)
          return
        }
        if (!res.ok) throw new Error('Impossible de charger votre fiche maison')
        const data = await res.json()
        setHouse(data)
        setDraft(data)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Erreur inconnue'))
      .finally(() => setLoading(false))
  }, [authFetch])

  async function createHouse(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const res = await authFetch('/api/houses/me', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code_postal: newCodePostal }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Création impossible')
      }
      const data = await res.json()
      setHouse(data)
      setDraft(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setCreating(false)
    }
  }

  async function saveBlock(keys: string[]) {
    const patch = Object.fromEntries(keys.map((k) => [k, draft[k] ?? null]))
    const res = await authFetch('/api/houses/me', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new Error(body?.detail || 'Enregistrement impossible')
    }
    const data = await res.json()
    setHouse(data)
    setDraft((d) => ({ ...d, ...data }))
  }

  function onChange(key: string, value: FieldValue) {
    setDraft((d) => ({ ...d, [key]: value }))
  }

  if (loading) {
    return <div className="max-w-[900px] mx-auto px-4 py-16 text-center text-gray-500">Chargement…</div>
  }

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-2">Ma fiche maison</h1>
      <p className="text-gray-600 mb-8">
        Bonjour {user?.prenom || ''} — renseignez votre logement bloc par bloc, à votre rythme. Rien n'est obligatoire
        à part le code postal.
      </p>

      {user && !user.email_verified && (
        <div className="border-l-4 border-sun bg-sun/10 rounded-r-2xl p-4 text-sm text-gray-700 mb-8">
          Pensez à vérifier votre email pour sécuriser votre compte — un lien vous a été envoyé.
        </div>
      )}

      {error && <p className="text-sm text-red-600 mb-6">{error}</p>}

      {!house ? (
        <form onSubmit={createHouse} className="bg-gray-50 rounded-2xl p-6 max-w-sm">
          <label className="block text-sm font-medium mb-1" htmlFor="code_postal">Code postal</label>
          <input
            id="code_postal" type="text" required pattern="\d{5}" maxLength={5} value={newCodePostal}
            onChange={(e) => setNewCodePostal(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm mb-4"
            placeholder="75001"
          />
          <button
            type="submit" disabled={creating}
            className="rounded-xl bg-primary text-white text-sm font-semibold px-4 py-2 hover:opacity-90 disabled:opacity-50"
          >
            {creating ? 'Création…' : 'Créer ma fiche maison'}
          </button>
        </form>
      ) : (
        <>
          <CompletenessBar score={house.completeness_score as number} niveau={house.niveau as string} />
          <div className="space-y-6">
            <BlockCard title="Identité du logement" weightLabel="20 % du score" pct={(house.block_scores as Record<string, number>)?.identite} fields={IDENTITE_FIELDS} draft={draft} onChange={onChange} onSave={saveBlock} />
            <BlockCard title="Enveloppe" weightLabel="25 % du score" pct={(house.block_scores as Record<string, number>)?.enveloppe} fields={ENVELOPPE_FIELDS} draft={draft} onChange={onChange} onSave={saveBlock} />
            <BlockCard title="Systèmes" weightLabel="25 % du score" pct={(house.block_scores as Record<string, number>)?.systemes} fields={SYSTEMES_FIELDS} draft={draft} onChange={onChange} onSave={saveBlock} />
            <BlockCard title="Énergie & factures" weightLabel="15 % du score" pct={(house.block_scores as Record<string, number>)?.energie} fields={ENERGIE_FIELDS} draft={draft} onChange={onChange} onSave={saveBlock} />
            <BlockCard title="Projet & désidératas" weightLabel="15 % du score" pct={(house.block_scores as Record<string, number>)?.projet} fields={PROJET_FIELDS} draft={draft} onChange={onChange} onSave={saveBlock} />
            <BlockCard title="Toiture / potentiel solaire" weightLabel="bonus — utilisé au simulateur" fields={TOITURE_FIELDS} draft={draft} onChange={onChange} onSave={saveBlock} />
          </div>
        </>
      )}
    </section>
  )
}
