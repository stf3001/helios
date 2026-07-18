import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Download } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

interface Fourchette { bas: number; haut: number; central: number }
interface Priorite {
  rang: number
  label: string
  poste: string
  part_deperdition_pct: number | null
  cout_eur: { bas: number; haut: number }
  aide_estimee_eur: number
  reste_a_charge_eur: number
  economie_annuelle_eur: Fourchette
  temps_retour_ans: number | null
}
interface AuditResult {
  version_helios: string
  completeness_score: number
  niveau: string
  deperditions: { poste: string; part_pct: number }[]
  consommation: {
    besoin_kwh_m2_an: number
    origine_besoin: string
    surface_m2: number
    conso_chauffage_theorique_kwh_an: number
    conso_elec_declaree_kwh_an: number | null
    ecart_pct: number | null
  }
  priorites: Priorite[]
  synthese: {
    nb_actions: number
    investissement_eur: { bas: number; haut: number }
    aides_estimees_eur: number
    economie_annuelle_totale_eur: Fourchette | null
    premiere_action: string | null
  }
  avertissement: string
}
interface AuditRow { id: string; created_at: string; result: AuditResult }

const POSTE_LABEL: Record<string, string> = {
  toiture: 'Toiture / combles', murs: 'Murs', air_ventilation: 'Air / ventilation',
  menuiseries: 'Menuiseries', plancher: 'Plancher bas', ponts_thermiques: 'Ponts thermiques',
}
const eur = (n: number) => n.toLocaleString('fr-FR') + ' €'

export default function EspaceAudits() {
  const { authFetch } = useAuth()
  const [score, setScore] = useState<number | null>(null)
  const [audits, setAudits] = useState<AuditRow[]>([])
  const [selected, setSelected] = useState<AuditRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      authFetch('/api/houses/me').then((r) => (r.ok ? r.json() : null)),
      authFetch('/api/audits').then((r) => (r.ok ? r.json() : [])),
    ]).then(([house, list]) => {
      setScore(house?.completeness_score ?? null)
      setAudits(list)
      if (list.length > 0) setSelected(list[0])
    }).finally(() => setLoading(false))
  }, [authFetch])

  async function generate() {
    setError(null)
    setGenerating(true)
    try {
      const res = await authFetch('/api/audits', { method: 'POST' })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail || 'Génération impossible.')
      }
      const created = await res.json()
      const row: AuditRow = { id: created.id, created_at: created.created_at, result: created.result }
      setAudits((prev) => [row, ...prev])
      setSelected(row)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur inconnue')
    } finally {
      setGenerating(false)
    }
  }

  async function downloadPdf(id: string) {
    const res = await authFetch(`/api/audits/${id}/pdf`)
    if (!res.ok) { setError('PDF indisponible.'); return }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `preaudit-helios-${id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const canGenerate = score !== null && score >= 70
  const r = selected?.result

  return (
    <section className="max-w-[1000px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Mes pré-audits</h1>
      </div>
      <p className="text-gray-600 mb-6">
        Un pré-diagnostic énergétique chiffré, calculé à partir de votre fiche maison. Ordres de grandeur indicatifs.
      </p>

      {loading ? (
        <p className="text-gray-400">Chargement…</p>
      ) : (
        <>
          {/* Bandeau complétude / génération */}
          <div className="bg-gray-50 rounded-2xl p-5 mb-8 flex flex-wrap items-center justify-between gap-4">
            <div className="text-sm">
              Complétude de votre fiche : <strong>{score ?? 0}%</strong>
              {!canGenerate && (
                <span className="text-gray-500">
                  {' '}— il faut au moins <strong>70%</strong> pour générer un pré-audit chiffré.{' '}
                  <Link to="/mon-espace" className="text-primary underline">Compléter ma fiche</Link>
                </span>
              )}
            </div>
            <button
              onClick={generate}
              disabled={!canGenerate || generating}
              className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-40"
            >
              {generating ? 'Calcul en cours…' : 'Générer un pré-audit'}
            </button>
          </div>

          {error && <p className="text-sm text-red-600 mb-6">{error}</p>}

          {audits.length === 0 && !error && (
            <p className="text-gray-400">Aucun pré-audit pour l'instant.</p>
          )}

          {audits.length > 0 && (
            <div className="grid md:grid-cols-[200px_1fr] gap-6">
              {/* Historique */}
              <div className="space-y-1">
                <div className="text-xs font-semibold text-gray-400 mb-1">Historique</div>
                {audits.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => setSelected(a)}
                    className={
                      'block w-full text-left text-xs rounded-lg px-3 py-2 ' +
                      (a.id === selected?.id ? 'bg-primary/10 text-primary font-semibold' : 'hover:bg-gray-100 text-gray-600')
                    }
                  >
                    {new Date(a.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                  </button>
                ))}
              </div>

              {/* Résultat */}
              {r && (
                <div className="space-y-8">
                  <div className="flex justify-end">
                    <button
                      onClick={() => downloadPdf(selected!.id)}
                      className="inline-flex items-center gap-1.5 text-sm rounded-lg border border-primary text-primary px-4 py-2 hover:bg-primary/5"
                    >
                      <Download className="w-4 h-4" /> Télécharger le PDF
                    </button>
                  </div>

                  {/* Déperditions */}
                  <div>
                    <h2 className="font-semibold text-lg mb-3">Où votre logement perd de la chaleur</h2>
                    <div className="space-y-2">
                      {r.deperditions.map((d) => (
                        <div key={d.poste} className="flex items-center gap-3 text-sm">
                          <div className="w-36 shrink-0">{POSTE_LABEL[d.poste] ?? d.poste}</div>
                          <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                            <div className="bg-primary h-full rounded-full" style={{ width: `${d.part_pct}%` }} />
                          </div>
                          <div className="w-12 text-right text-gray-600">{d.part_pct}%</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Consommation */}
                  <div>
                    <h2 className="font-semibold text-lg mb-2">Consommation</h2>
                    <p className="text-sm text-gray-600">
                      Besoin de chauffage estimé : <strong>{r.consommation.besoin_kwh_m2_an} kWh/m²/an</strong>{' '}
                      × {r.consommation.surface_m2} m² = <strong>{r.consommation.conso_chauffage_theorique_kwh_an.toLocaleString('fr-FR')} kWh/an</strong>.
                      {r.consommation.conso_elec_declaree_kwh_an && (
                        <> Conso déclarée : {r.consommation.conso_elec_declaree_kwh_an.toLocaleString('fr-FR')} kWh/an.</>
                      )}
                    </p>
                  </div>

                  {/* Priorités */}
                  <div>
                    <h2 className="font-semibold text-lg mb-3">Vos priorités de travaux</h2>
                    <div className="space-y-3">
                      {r.priorites.map((p) => (
                        <div key={p.rang} className="border border-gray-200 rounded-xl p-4">
                          <div className="flex items-baseline justify-between gap-2 mb-2">
                            <div className="font-medium">#{p.rang} {p.label}</div>
                            {p.temps_retour_ans !== null && (
                              <div className="text-xs text-gray-500 shrink-0">retour ~{p.temps_retour_ans} ans</div>
                            )}
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-gray-600">
                            <div>Coût : {eur(p.cout_eur.bas)}–{eur(p.cout_eur.haut)}</div>
                            <div>Aide : ~{eur(p.aide_estimee_eur)}</div>
                            <div>Reste : ~{eur(p.reste_a_charge_eur)}</div>
                            <div>Éco/an : {eur(p.economie_annuelle_eur.bas)}–{eur(p.economie_annuelle_eur.haut)}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Synthèse */}
                  <div className="bg-primary/5 border border-primary/20 rounded-2xl p-5">
                    <h2 className="font-semibold text-lg mb-2">Synthèse</h2>
                    <p className="text-sm text-gray-700">
                      <strong>{r.synthese.nb_actions} actions</strong> recommandées. Investissement estimé :{' '}
                      {eur(r.synthese.investissement_eur.bas)}–{eur(r.synthese.investissement_eur.haut)}, aides ~{eur(r.synthese.aides_estimees_eur)}.
                      {r.synthese.economie_annuelle_totale_eur && (
                        <> Économie annuelle potentielle : <strong>{eur(r.synthese.economie_annuelle_totale_eur.bas)}–{eur(r.synthese.economie_annuelle_totale_eur.haut)}</strong>.</>
                      )}
                    </p>
                    {r.synthese.premiere_action && (
                      <p className="text-sm text-gray-700 mt-2">
                        Première étape conseillée : <strong>{r.synthese.premiere_action}</strong> — l'esprit colibri, on commence petit.
                      </p>
                    )}
                  </div>

                  <p className="text-xs text-gray-400">{r.avertissement}</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  )
}
