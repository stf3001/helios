import { useEffect, useState, type FormEvent } from 'react'
import { Zap, TrendingUp } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

interface Reco { sujet: string; constat: string; conseil: string }
interface Advice {
  recommandations: Reco[]
  tarif_dynamique: { compatibilite: string; explication: string; usages_pilotables: string[] }
  avertissement: string
}
interface SpotPoint { h: number; prix: number }
interface SpotPrices { source: string; unite: string; pas: string; points: SpotPoint[]; note?: string }
interface Estimation {
  gain_estime_pct: number
  gain_estime_eur_an: number
  facture_reference_eur_an: number
  offres?: string[]
  meilleures_offres?: string[]
}
interface StudyResult {
  id: string
  status: string
  estimation: Estimation
  helios_opinion: string
  favorable: boolean
  comparateur_public: string
  partner_link: string | null
  partenaire?: string | null
}

const COMPAT_STYLE: Record<string, string> = {
  favorable: 'bg-green-100 text-green-800',
  neutre: 'bg-gray-100 text-gray-700',
  prudence: 'bg-amber-100 text-amber-800',
}

export default function EspaceEnergie() {
  const { authFetch } = useAuth()
  const [advice, setAdvice] = useState<Advice | null>(null)
  const [spot, setSpot] = useState<SpotPrices | null>(null)
  const [loading, setLoading] = useState(true)

  // Parcours SOBRY
  const [pdl, setPdl] = useState('')
  const [consent, setConsent] = useState(false)
  const [study, setStudy] = useState<StudyResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [decided, setDecided] = useState<string | null>(null)

  // Parcours courtage
  const [courtageConsent, setCourtageConsent] = useState(false)
  const [offreActuelle, setOffreActuelle] = useState('')
  const [courtage, setCourtage] = useState<StudyResult | null>(null)
  const [courtageBusy, setCourtageBusy] = useState(false)
  const [courtageDecided, setCourtageDecided] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      authFetch('/api/energy/advice').then((r) => (r.ok ? r.json() : null)),
      authFetch('/api/energy/spot-prices').then((r) => (r.ok ? r.json() : null)),
    ]).then(([a, s]) => { setAdvice(a); setSpot(s) }).finally(() => setLoading(false))
  }, [authFetch])

  async function launchStudy(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const res = await authFetch('/api/energy/study', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pdl, consent }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Étude impossible.')
      }
      setStudy(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setSubmitting(false)
    }
  }

  async function decide(decision: 'souscrite' | 'declinee') {
    if (!study) return
    const res = await authFetch(`/api/energy/study/${study.id}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision }),
    })
    if (res.ok) setDecided(decision)
  }

  async function launchCourtage(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setCourtageBusy(true)
    try {
      const res = await authFetch('/api/energy/courtage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consent: courtageConsent, offre_actuelle: offreActuelle || null }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Étude impossible.')
      }
      setCourtage(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setCourtageBusy(false)
    }
  }

  async function decideCourtage(decision: 'souscrite' | 'declinee') {
    if (!courtage) return
    const res = await authFetch(`/api/energy/study/${courtage.id}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision }),
    })
    if (res.ok) setCourtageDecided(decision)
  }

  const maxPrix = spot ? Math.max(...spot.points.map((p) => p.prix)) : 1

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <Zap className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Mon contrat d'énergie</h1>
      </div>
      <p className="text-gray-600 mb-8">
        Helios vérifie aussi que vous achetez bien votre énergie — conseil gratuit et indépendant, sans commission.
      </p>

      {loading ? (
        <p className="text-gray-400">Chargement…</p>
      ) : (
        <div className="space-y-10">
          {/* Niveau 1 : conseil Helios */}
          <div>
            <h2 className="font-semibold text-lg mb-3">Le conseil d'Helios (gratuit, sans tiers)</h2>
            {advice && (
              <div className="space-y-3">
                {advice.recommandations.map((r) => (
                  <div key={r.sujet} className="border border-gray-200 rounded-xl p-4">
                    <div className="font-medium text-sm mb-1">{r.sujet}</div>
                    <div className="text-sm text-gray-600">{r.constat}</div>
                    <div className="text-sm text-gray-800 mt-1">→ {r.conseil}</div>
                  </div>
                ))}
                <div className="rounded-xl p-4 bg-gray-50">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm">Tarif dynamique</span>
                    <span className={'text-xs px-2 py-0.5 rounded-full ' + (COMPAT_STYLE[advice.tarif_dynamique.compatibilite] ?? '')}>
                      {advice.tarif_dynamique.compatibilite}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{advice.tarif_dynamique.explication}</p>
                </div>
                <p className="text-xs text-gray-400">{advice.avertissement}</p>
              </div>
            )}
          </div>

          {/* Prix spot */}
          {spot && (
            <div>
              <h2 className="font-semibold text-lg mb-1">Prix de l'électricité aujourd'hui (heure par heure)</h2>
              {spot.note && <p className="text-xs text-amber-700 mb-3">{spot.note}</p>}
              <div className="flex items-end gap-[3px] h-32 border-b border-gray-200">
                {spot.points.map((p) => (
                  <div key={p.h} className="flex-1 bg-primary/70 rounded-t" style={{ height: `${(p.prix / maxPrix) * 100}%` }}
                    title={`${p.h}h : ${p.prix} €/kWh`} />
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                <span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>23h</span>
              </div>
            </div>
          )}

          {/* Niveau 2 : étude SOBRY */}
          <div className="border-t border-gray-200 pt-8">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-lg">Aller plus loin : étude tarif dynamique (SOBRY)</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              SOBRY est un fournisseur partenaire à tarification dynamique. Avec votre accord, nous transmettons votre
              point de livraison (PDL) pour une estimation précise. <strong>Helios vous donnera son avis indépendant
              sur le résultat — y compris négatif</strong> — avant toute décision.
            </p>

            {!study ? (
              <form onSubmit={launchStudy} className="bg-gray-50 rounded-2xl p-5 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Votre PDL (14 chiffres, sur votre facture)</label>
                  <input value={pdl} onChange={(e) => setPdl(e.target.value.replace(/\D/g, '').slice(0, 14))}
                    placeholder="12345678901234"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono" />
                </div>
                <label className="flex items-start gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
                  <span>J'autorise HELIOS à transmettre mon PDL et mon profil de consommation à SOBRY pour une estimation
                    tarifaire. Je peux retirer ce consentement à tout moment avant souscription.</span>
                </label>
                <button type="submit" disabled={!consent || pdl.length !== 14 || submitting}
                  className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-40">
                  {submitting ? 'Étude en cours…' : 'Lancer l\'étude'}
                </button>
                {error && <p className="text-sm text-red-600">{error}</p>}
              </form>
            ) : (
              <div className="space-y-4">
                {/* L'avis d'Helios est présenté AVANT toute incitation */}
                <div className={'rounded-2xl p-5 border ' + (study.favorable ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200')}>
                  <div className="font-semibold mb-1">L'avis d'Helios</div>
                  <p className="text-sm text-gray-700">{study.helios_opinion}</p>
                </div>

                <div className="text-sm text-gray-600">
                  Estimation : gain <strong>~{study.estimation.gain_estime_pct}%</strong> soit
                  ~{study.estimation.gain_estime_eur_an} €/an (base facture {study.estimation.facture_reference_eur_an} €).
                  Offres : {(study.estimation.offres ?? []).join(', ')}.
                </div>

                {decided ? (
                  <p className="text-sm font-medium text-gray-800">
                    {decided === 'souscrite' ? 'Vous avez choisi de souscrire — bonne transition !' : 'Vous avez décliné. Votre choix est enregistré.'}
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-3">
                    {study.favorable && study.partner_link && (
                      <a href={study.partner_link} target="_blank" rel="noopener noreferrer"
                        onClick={() => decide('souscrite')}
                        className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90">
                        Souscrire chez SOBRY
                      </a>
                    )}
                    <button onClick={() => decide('declinee')}
                      className="rounded-xl border border-gray-300 text-gray-700 px-5 py-2.5 hover:bg-gray-50">
                      Ne pas donner suite
                    </button>
                  </div>
                )}

                <p className="text-xs text-gray-400">
                  Comparez librement les offres du marché sur le comparateur public indépendant{' '}
                  <a href={study.comparateur_public} target="_blank" rel="noopener noreferrer" className="underline">
                    energie-info.fr
                  </a>.
                </p>
              </div>
            )}
          </div>

          {/* Niveau 2 bis : courtage d'énergie */}
          <div className="border-t border-gray-200 pt-8">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h2 className="font-semibold text-lg">Faire jouer la concurrence : étude de courtage</h2>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Un partenaire courtier compare pour vous les offres du marché selon votre profil.
              <strong> Helios vous donnera son avis indépendant sur le résultat</strong> — y compris « restez sur votre offre ».
            </p>

            {!courtage ? (
              <form onSubmit={launchCourtage} className="bg-gray-50 rounded-2xl p-5 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Votre offre actuelle (facultatif)</label>
                  <input value={offreActuelle} onChange={(e) => setOffreActuelle(e.target.value)}
                    placeholder="ex. EDF Tarif Bleu"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
                </div>
                <label className="flex items-start gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={courtageConsent} onChange={(e) => setCourtageConsent(e.target.checked)} className="mt-1" />
                  <span>J'autorise HELIOS à transmettre mon profil de consommation à un partenaire courtier pour comparer les offres.</span>
                </label>
                <button type="submit" disabled={!courtageConsent || courtageBusy}
                  className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-40">
                  {courtageBusy ? 'Étude en cours…' : 'Lancer l\'étude de courtage'}
                </button>
                {error && <p className="text-sm text-red-600">{error}</p>}
              </form>
            ) : (
              <div className="space-y-4">
                <div className={'rounded-2xl p-5 border ' + (courtage.favorable ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200')}>
                  <div className="font-semibold mb-1">L'avis d'Helios{courtage.partenaire ? ` (courtier : ${courtage.partenaire})` : ''}</div>
                  <p className="text-sm text-gray-700">{courtage.helios_opinion}</p>
                </div>
                <div className="text-sm text-gray-600">
                  Gain estimé <strong>~{courtage.estimation.gain_estime_pct}%</strong> soit
                  ~{courtage.estimation.gain_estime_eur_an} €/an.
                  {courtage.estimation.meilleures_offres && <> Pistes : {courtage.estimation.meilleures_offres.join(', ')}.</>}
                </div>
                {courtageDecided ? (
                  <p className="text-sm font-medium text-gray-800">
                    {courtageDecided === 'souscrite' ? 'Vous avez choisi de changer d\'offre — bonne économie !' : 'Vous avez décliné. Votre choix est enregistré.'}
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-3">
                    {courtage.favorable && courtage.partner_link && (
                      <a href={courtage.partner_link} target="_blank" rel="noopener noreferrer"
                        onClick={() => decideCourtage('souscrite')}
                        className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90">
                        Voir l'offre du courtier
                      </a>
                    )}
                    <button onClick={() => decideCourtage('declinee')}
                      className="rounded-xl border border-gray-300 text-gray-700 px-5 py-2.5 hover:bg-gray-50">
                      Ne pas donner suite
                    </button>
                  </div>
                )}
                <p className="text-xs text-gray-400">
                  Comparez aussi librement sur le comparateur public indépendant{' '}
                  <a href={courtage.comparateur_public} target="_blank" rel="noopener noreferrer" className="underline">energie-info.fr</a>.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
