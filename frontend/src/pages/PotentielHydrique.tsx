import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Droplets } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'

const MODELES = ['20L', '50L', '100L', '250L', '500L', '1000L']
const MOIS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']

interface MoisData { mois: number; litres_jour: number; litres_mois: number }
interface WaterResult {
  ville: string
  modele: string
  source: string
  production_annuelle_litres: number
  moyenne_litres_jour: number
  personnes_couvertes: number
  mensuel: MoisData[]
  avertissement: string
}

export default function PotentielHydrique() {
  useTitle('Mon potentiel hydrique')
  const { user, authFetch } = useAuth()
  const [cities, setCities] = useState<string[]>([])
  const [ville, setVille] = useState('')
  const [modele, setModele] = useState('20L')
  const [result, setResult] = useState<WaterResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/water/cities').then((r) => (r.ok ? r.json() : [])).then((c) => { setCities(c); if (c[0]) setVille(c[0]) })
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    const doFetch = user ? authFetch : fetch
    try {
      const res = await doFetch('/api/water/simulate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ville, modele }),
      })
      if (!res.ok) { const b = await res.json().catch(() => null); throw new Error(b?.detail || 'Estimation impossible.') }
      const data = await res.json()
      setResult(data.result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally { setLoading(false) }
  }

  const maxMois = result ? Math.max(...result.mensuel.map((m) => m.litres_mois)) : 1

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <Droplets className="w-7 h-7 text-sky" />
        <h1 className="text-2xl font-bold">Mon potentiel hydrique</h1>
      </div>
      <p className="text-gray-600 mb-8">
        Estimez la quantité d'eau qu'un générateur atmosphérique (Hydrolia) pourrait produire chez vous,
        selon le climat de votre ville. De l'eau pure, extraite de l'air — une brique de la maison de demain.{' '}
        <Link to="/eau" className="text-sky underline">Comprendre l'eau atmosphérique →</Link>
      </p>

      <form onSubmit={onSubmit} className="bg-gray-50 rounded-2xl p-6 grid gap-4 sm:grid-cols-2 mb-8">
        <div>
          <label className="block text-sm font-medium mb-1">Votre ville (climat de référence)</label>
          <select value={ville} onChange={(e) => setVille(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {cities.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Modèle</label>
          <select value={modele} onChange={(e) => setModele(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
            {MODELES.map((m) => <option key={m} value={m}>{m} / jour (nominal)</option>)}
          </select>
        </div>
        <div className="sm:col-span-2">
          <button type="submit" disabled={loading || !ville}
            className="rounded-xl bg-sky text-white font-semibold px-6 py-2.5 hover:opacity-90 disabled:opacity-50">
            {loading ? 'Calcul…' : 'Estimer ma production d\'eau'}
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-red-600 mb-6">{error}</p>}

      {result && (
        <div className="space-y-8">
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { v: result.production_annuelle_litres.toLocaleString('fr-FR') + ' L', l: 'produits par an' },
              { v: result.moyenne_litres_jour + ' L', l: 'en moyenne par jour' },
              { v: result.personnes_couvertes.toString(), l: 'personnes couvertes (~4 L/j)' },
            ].map((c) => (
              <div key={c.l} className="bg-white border border-gray-200 rounded-2xl p-5 text-center">
                <div className="text-3xl font-bold text-sky my-1">{c.v}</div>
                <div className="text-xs text-gray-500">{c.l}</div>
              </div>
            ))}
          </div>

          <div>
            <h2 className="font-semibold text-lg mb-3">Production mois par mois (litres)</h2>
            <div className="flex items-end gap-1.5 h-40 border-b border-gray-200">
              {result.mensuel.map((m) => (
                <div key={m.mois} className="flex-1 flex flex-col items-center justify-end h-full">
                  <div className="w-full bg-sky/70 rounded-t" style={{ height: `${(m.litres_mois / maxMois) * 100}%` }}
                    title={`${MOIS[m.mois - 1]} : ${m.litres_mois} L`} />
                </div>
              ))}
            </div>
            <div className="flex justify-between text-[10px] text-gray-400 mt-1">
              {MOIS.map((m) => <span key={m} className="flex-1 text-center">{m[0]}</span>)}
            </div>
          </div>

          <p className="text-xs text-gray-400">{result.avertissement}</p>
        </div>
      )}
    </section>
  )
}
