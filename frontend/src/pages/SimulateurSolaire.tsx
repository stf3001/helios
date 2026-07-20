import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Sun } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'

const ORIENTATIONS = [
  { value: 'sud', label: 'Sud' },
  { value: 'sud_est', label: 'Sud-Est' },
  { value: 'sud_ouest', label: 'Sud-Ouest' },
  { value: 'est', label: 'Est' },
  { value: 'ouest', label: 'Ouest' },
  { value: 'nord_est', label: 'Nord-Est' },
  { value: 'nord_ouest', label: 'Nord-Ouest' },
  { value: 'nord', label: 'Nord' },
]

const OMBRAGES = [
  { value: 'aucun', label: 'Aucun' },
  { value: 'partiel', label: 'Partiel' },
  { value: 'important', label: 'Important' },
]

interface Fourchette {
  bas: number
  haut: number
  central: number
}

interface Profil {
  taux_autoconso_pct: number
  economie_annuelle_eur: Fourchette
  temps_retour_ans: number | null
}

interface ScenarioPuissance {
  puissance_kwc: number
  production_annuelle_kwh: number
  cout_installation_eur: Fourchette
  profils_autoconso: { sans_pilotage: Profil; avec_pilotage: Profil }
  stockage_options: StockageOption[]
}

interface StockageOption {
  tech: string
  label: string
  capacite_kwh: number
  taux_autoconso_pct: number
  economie_annuelle_eur: Fourchette
  cout_total_eur: Fourchette
  temps_retour_ans: number | null
  garantie_ans: number
  note: string
}

interface SimResult {
  partiel: boolean
  params: { gps: { label: string | null }; orientation: string | null; pente: number; ombrage: string }
  production?: Record<string, { annual_kwh: number; monthly_kwh: number[] }>
  message?: string
  scenarios?: {
    conso_reference_kwh: number
    conso_estimee: boolean
    par_puissance: Record<string, ScenarioPuissance>
    avertissement: string
  }
}

const eur = (n: number) => n.toLocaleString('fr-FR') + ' €'

export default function SimulateurSolaire() {
  useTitle('Simulateur solaire')
  const { user, authFetch } = useAuth()
  const [adresse, setAdresse] = useState('')
  const [orientation, setOrientation] = useState('sud')
  const [pente, setPente] = useState('30')
  const [ombrage, setOmbrage] = useState('aucun')
  const [conso, setConso] = useState('')
  const [result, setResult] = useState<SimResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    const doFetch = user ? authFetch : fetch
    try {
      const res = await doFetch('/api/solar/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          adresse,
          orientation,
          pente: Number(pente),
          ombrage,
          conso_kwh_an: conso ? Number(conso) : undefined,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Simulation impossible, réessayez.')
      }
      setResult(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <Sun className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Simulateur de potentiel solaire</h1>
      </div>
      <p className="text-gray-600 mb-8">
        Estimez la production photovoltaïque de votre toiture — gratuitement, sans engagement.
        Données de production issues de PVGIS (Commission européenne).
      </p>

      <form onSubmit={onSubmit} className="bg-gray-50 rounded-2xl p-6 grid gap-4 sm:grid-cols-2 mb-8">
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium mb-1">Adresse de la maison</label>
          <input
            required value={adresse} onChange={(e) => setAdresse(e.target.value)}
            placeholder="12 rue de la République, Lyon"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Orientation de la toiture</label>
          <select value={orientation} onChange={(e) => setOrientation(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {ORIENTATIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Inclinaison (degrés)</label>
          <input type="number" min={0} max={90} value={pente} onChange={(e) => setPente(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Ombrage</label>
          <select value={ombrage} onChange={(e) => setOmbrage(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {OMBRAGES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Conso élec. annuelle (kWh, optionnel)</label>
          <input type="number" min={0} value={conso} onChange={(e) => setConso(e.target.value)}
            placeholder="ex. 4500"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div className="sm:col-span-2">
          <button type="submit" disabled={loading}
            className="rounded-xl bg-primary text-white font-semibold px-6 py-2.5 hover:opacity-90 disabled:opacity-50">
            {loading ? 'Calcul en cours…' : 'Estimer ma production'}
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-red-600 mb-6">{error}</p>}

      {result && (
        <div className="space-y-6">
          {result.params.gps.label && (
            <p className="text-sm text-gray-500">📍 {result.params.gps.label}</p>
          )}

          {/* Production (toujours affichée) */}
          <div className="grid gap-4 sm:grid-cols-3">
            {result.production &&
              Object.entries(result.production).map(([kwc, prod]) => (
                <div key={kwc} className="bg-white border border-gray-200 rounded-2xl p-5 text-center">
                  <div className="text-sm text-gray-500">Installation {kwc} kWc</div>
                  <div className="text-3xl font-bold text-primary my-1">
                    {prod.annual_kwh.toLocaleString('fr-FR')}
                  </div>
                  <div className="text-xs text-gray-500">kWh produits par an</div>
                </div>
              ))}
            {result.scenarios &&
              Object.entries(result.scenarios.par_puissance).map(([kwc, s]) => (
                <div key={kwc} className="bg-white border border-gray-200 rounded-2xl p-5 text-center">
                  <div className="text-sm text-gray-500">Installation {kwc} kWc</div>
                  <div className="text-3xl font-bold text-primary my-1">
                    {s.production_annuelle_kwh.toLocaleString('fr-FR')}
                  </div>
                  <div className="text-xs text-gray-500">kWh produits par an</div>
                </div>
              ))}
          </div>

          {/* Mode public : CTA inscription */}
          {result.partiel && (
            <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6 text-center">
              <p className="text-gray-700 mb-4">{result.message}</p>
              <Link to="/inscription"
                className="inline-block rounded-xl bg-primary text-white font-semibold px-6 py-2.5 hover:opacity-90">
                Créer mon compte gratuit
              </Link>
            </div>
          )}

          {/* Mode connecté : scénarios économiques complets */}
          {result.scenarios && (
            <div className="space-y-4">
              {result.scenarios.conso_estimee && (
                <p className="text-xs text-gray-500">
                  Conso de référence estimée à {result.scenarios.conso_reference_kwh.toLocaleString('fr-FR')} kWh/an —
                  renseignez votre conso réelle dans votre fiche maison pour affiner.
                </p>
              )}
              {Object.entries(result.scenarios.par_puissance).map(([kwc, s]) => (
                <div key={kwc} className="bg-white border border-gray-200 rounded-2xl p-6">
                  <h3 className="font-semibold text-lg mb-3">Installation {kwc} kWc — coût estimé {eur(s.cout_installation_eur.bas)} à {eur(s.cout_installation_eur.haut)}</h3>
                  <div className="grid sm:grid-cols-2 gap-4 text-sm mb-4">
                    <div className="rounded-xl bg-gray-50 p-4">
                      <div className="font-medium mb-1">Sans pilotage</div>
                      <div className="text-gray-600">Autoconso {s.profils_autoconso.sans_pilotage.taux_autoconso_pct} %</div>
                      <div className="text-gray-600">
                        Éco. {eur(s.profils_autoconso.sans_pilotage.economie_annuelle_eur.bas)}–{eur(s.profils_autoconso.sans_pilotage.economie_annuelle_eur.haut)}/an
                      </div>
                      <div className="text-gray-600">Retour ~{s.profils_autoconso.sans_pilotage.temps_retour_ans} ans</div>
                    </div>
                    <div className="rounded-xl bg-primary/5 p-4">
                      <div className="font-medium mb-1">Avec pilotage</div>
                      <div className="text-gray-600">Autoconso {s.profils_autoconso.avec_pilotage.taux_autoconso_pct} %</div>
                      <div className="text-gray-600">
                        Éco. {eur(s.profils_autoconso.avec_pilotage.economie_annuelle_eur.bas)}–{eur(s.profils_autoconso.avec_pilotage.economie_annuelle_eur.haut)}/an
                      </div>
                      <div className="text-gray-600">Retour ~{s.profils_autoconso.avec_pilotage.temps_retour_ans} ans</div>
                    </div>
                  </div>

                  {/* Comparaison des technologies de stockage */}
                  <div className="text-sm font-medium text-ink mb-2">Ajouter un stockage ({s.stockage_options[0]?.capacite_kwh} kWh) — autoconso {s.stockage_options[0]?.taux_autoconso_pct} %</div>
                  <div className="grid sm:grid-cols-3 gap-3 text-sm">
                    {s.stockage_options.map((o) => (
                      <div key={o.tech} className="rounded-xl border border-gray-200 p-4">
                        <div className="font-medium text-ink mb-1">{o.label}</div>
                        <div className="text-gray-600">Coût total ~{eur(o.cout_total_eur.central)}</div>
                        <div className="text-gray-600">Retour ~{o.temps_retour_ans} ans</div>
                        <div className="text-leaf font-medium">Garantie {o.garantie_ans} ans</div>
                        <div className="text-xs text-gray-400 mt-1">{o.note}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <p className="text-xs text-gray-400">{result.scenarios.avertissement}</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
