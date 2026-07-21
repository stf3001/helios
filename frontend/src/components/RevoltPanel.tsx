import { useEffect, useState, type FormEvent } from 'react'
import { Zap, Info, History } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const TARIF_LABEL: Record<string, string> = { fixe: 'Tarif fixe', soflex: 'SOBRY SoFlex', socap: 'SOBRY SoCap' }
const BRIQUE_LABEL: Record<string, string> = {
  actuel_sans_pv: 'Situation actuelle (sans PV)',
  pv_seul: 'Ajout de panneaux solaires',
  pv_batterie_physique: 'Panneaux + batterie physique',
  pv_mylight_batterie_virtuelle: 'Panneaux + batterie virtuelle MyLight',
}

interface Ligne {
  brique: string
  tarif: string
  cout_annuel_eur: number
  economie_vs_actuel_eur: number
  economie_vs_actuel_pct: number
  taux_autoconsommation?: number
  taux_couverture_besoins?: number
  frais_activation_unique_eur?: number
  avertissement?: string
}

interface RevoltResult {
  study_id?: string
  power_kwc: number
  production_annuelle_kwh: number
  consommation: { source: string; annuelle_kwh: number; avertissement: string }
  lignes: Ligne[]
}

interface RevoltStudySummary {
  id: string
  params: { power_kwc: number; battery_kwh?: number; mylight?: boolean; tarif_modes: string[] }
  result: RevoltResult
  created_at: string
}

const eur = (n: number) => Math.round(n).toLocaleString('fr-FR') + ' €'

export default function RevoltPanel({ defaultPowerKwc }: { defaultPowerKwc: number }) {
  const { authFetch } = useAuth()
  const [powerKwc, setPowerKwc] = useState(String(defaultPowerKwc))
  const [avecBatterie, setAvecBatterie] = useState(false)
  const [batteryKwh, setBatteryKwh] = useState('5')
  const [batteryKw, setBatteryKw] = useState('3')
  const [mylight, setMylight] = useState(false)
  const [tarifModes, setTarifModes] = useState<string[]>(['fixe', 'soflex', 'socap'])
  const [result, setResult] = useState<RevoltResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [historique, setHistorique] = useState<RevoltStudySummary[]>([])

  function chargerHistorique() {
    authFetch('/api/revolt/studies').then((r) => (r.ok ? r.json() : [])).then(setHistorique).catch(() => {})
  }
  useEffect(chargerHistorique, [authFetch])

  function toggleTarif(mode: string) {
    setTarifModes((m) => (m.includes(mode) ? m.filter((x) => x !== mode) : [...m, mode]))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await authFetch('/api/revolt/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          power_kwc: Number(powerKwc),
          battery_kwh: avecBatterie ? Number(batteryKwh) : undefined,
          battery_power_kw: avecBatterie ? Number(batteryKw) : undefined,
          mylight,
          tarif_modes: tarifModes.length ? tarifModes : ['fixe'],
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Simulation impossible, réessayez.')
      }
      setResult(await res.json())
      chargerHistorique() // conservée gratuitement dans l'espace client — on rafraîchit la liste
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setLoading(false)
    }
  }

  // Regroupe les lignes par brique (une carte par brique, une colonne par tarif)
  const briques = result ? Array.from(new Set(result.lignes.map((l) => l.brique))) : []

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 mt-4">
      <div className="flex items-center gap-2 mb-1">
        <Zap className="w-5 h-5 text-primary" />
        <h3 className="font-semibold text-lg">Scénarios avancés (bêta)</h3>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Comparez, à consommation réelle égale : panneaux seuls, avec batterie physique, avec batterie
        virtuelle MyLight, et différents tarifs SOBRY.
      </p>

      <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2 bg-gray-50 rounded-xl p-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">Puissance simulée (kWc)</label>
          <input type="number" min={1} max={36} step={0.5} value={powerKwc} onChange={(e) => setPowerKwc(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Tarifs à comparer</label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(TARIF_LABEL).map(([mode, label]) => (
              <button type="button" key={mode} onClick={() => toggleTarif(mode)}
                className={'text-xs px-3 py-1.5 rounded-full border ' +
                  (tarifModes.includes(mode) ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-600')}>
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="sm:col-span-2 flex flex-wrap gap-6">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={avecBatterie} onChange={(e) => setAvecBatterie(e.target.checked)} />
            Ajouter une batterie physique
          </label>
          {avecBatterie && (
            <div className="flex gap-3">
              <input type="number" min={1} value={batteryKwh} onChange={(e) => setBatteryKwh(e.target.value)}
                placeholder="Capacité (kWh)" className="w-32 rounded-lg border border-gray-300 px-3 py-1.5 text-sm" />
              <input type="number" min={1} value={batteryKw} onChange={(e) => setBatteryKw(e.target.value)}
                placeholder="Puissance (kW)" className="w-32 rounded-lg border border-gray-300 px-3 py-1.5 text-sm" />
            </div>
          )}
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={mylight} onChange={(e) => setMylight(e.target.checked)} />
            Simuler la batterie virtuelle MyLight
          </label>
        </div>

        <div className="sm:col-span-2">
          <button type="submit" disabled={loading}
            className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-50">
            {loading ? 'Calcul en cours (peut prendre 30-60s)…' : 'Comparer les scénarios'}
          </button>
        </div>
      </form>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {result && (
        <div className="space-y-4">
          <div className="text-xs text-gray-500 flex items-start gap-1.5 bg-amber-50 border border-amber-200 rounded-lg p-3">
            <Info className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
            <span>{result.consommation.avertissement}</span>
          </div>

          {briques.map((brique) => {
            const lignesBrique = result.lignes.filter((l) => l.brique === brique)
            return (
              <div key={brique} className="rounded-xl border border-gray-200 p-4">
                <div className="font-medium text-ink mb-2">{BRIQUE_LABEL[brique] ?? brique}</div>
                <div className="grid sm:grid-cols-3 gap-3 text-sm">
                  {lignesBrique.map((l) => (
                    <div key={l.tarif} className="rounded-lg bg-gray-50 p-3">
                      <div className="text-xs text-gray-500 mb-1">{TARIF_LABEL[l.tarif] ?? l.tarif}</div>
                      <div className="font-semibold text-ink">{eur(l.cout_annuel_eur)}/an</div>
                      {brique !== 'actuel_sans_pv' && (
                        <div className={l.economie_vs_actuel_eur >= 0 ? 'text-leaf' : 'text-red-600'}>
                          {l.economie_vs_actuel_eur >= 0 ? '−' : '+'}{eur(Math.abs(l.economie_vs_actuel_eur))}/an
                          {' '}({l.economie_vs_actuel_pct >= 0 ? '' : '+'}{Math.abs(l.economie_vs_actuel_pct)}%)
                        </div>
                      )}
                      {l.taux_autoconsommation != null && (
                        <div className="text-xs text-gray-500 mt-1">
                          Autoconso {Math.round(l.taux_autoconsommation * 100)} %
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {lignesBrique[0]?.avertissement && (
                  <p className="text-xs text-gray-500 mt-2">{lignesBrique[0].avertissement}</p>
                )}
                {lignesBrique[0]?.frais_activation_unique_eur != null && (
                  <p className="text-xs text-gray-500 mt-1">
                    + frais d'activation unique : {eur(lignesBrique[0].frais_activation_unique_eur)}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {historique.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
            <History className="w-4 h-4" /> Mes simulations précédentes
          </div>
          <p className="text-xs text-gray-500 mb-3">
            Conservées gratuitement dans votre espace — Helios s'appuie dessus dans vos conversations.
          </p>
          <ul className="space-y-1.5">
            {historique.map((h) => {
              const meilleure = h.result.lignes
                .filter((l) => l.brique !== 'actuel_sans_pv')
                .sort((a, b) => b.economie_vs_actuel_eur - a.economie_vs_actuel_eur)[0]
              return (
                <li key={h.id} className="text-xs text-gray-600 flex flex-wrap items-center gap-x-2">
                  <span className="text-gray-400">{new Date(h.created_at).toLocaleDateString('fr-FR')}</span>
                  <span>{h.params.power_kwc} kWc</span>
                  {h.params.battery_kwh && <span>+ batterie {h.params.battery_kwh} kWh</span>}
                  {h.params.mylight && <span>+ MyLight</span>}
                  {meilleure && (
                    <span className="text-leaf font-medium">
                      meilleure option : {BRIQUE_LABEL[meilleure.brique] ?? meilleure.brique} ({TARIF_LABEL[meilleure.tarif]}) —
                      {' '}{eur(meilleure.economie_vs_actuel_eur)}/an
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
