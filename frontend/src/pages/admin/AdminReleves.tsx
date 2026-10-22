import { useState } from 'react'
import { Download, FileText, Lock, Receipt } from 'lucide-react'
import Depliant from '../../components/Depliant'
import {
  Attente, BTN_PRIMAIRE, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData,
} from '../../components/admin/AdminLayout'
import { dateCourte } from '../../components/mer/libelles'
import Releve, { MENTION_RELEVE, StatutReleve, euros, nomDuMois, type ReleveMois } from '../../components/mer/Releve'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

/** Relevés mensuels (mises en relation, lot 4) : tableau du mois, clôture, export. Pas des factures. */
interface TableauMois {
  mois: string; statut: string; cloture_le: string | null; cloture_par: string | null; cloture_possible_le: string
  en_attente: number; total_ht: number; releves: ReleveMois[]
}

const moisCourant = () => new Date().toLocaleDateString('sv-SE').slice(0, 7)

export default function AdminReleves() {
  useTitle('Back-office — Relevés')
  const { authFetch } = useAuth()
  const [mois, setMois] = useState(moisCourant())
  const { data, error, reload } = useAdminData<TableauMois>(`/api/admin/releves?mois=${mois}`)
  const [message, setMessage] = useState<{ ok: boolean; texte: string } | null>(null)
  const [busy, setBusy] = useState(false)

  async function telecharger(chemin: string, nom: string) {
    const r = await authFetch(chemin)
    if (!r.ok) { setMessage({ ok: false, texte: `Erreur ${r.status}` }); return }
    const url = URL.createObjectURL(await r.blob())
    const a = document.createElement('a')
    a.href = url; a.download = nom; a.click()
    URL.revokeObjectURL(url)
  }

  async function cloturer() {
    if (!confirm(`Clore ${nomDuMois(mois)} ? Les relevés de ce mois seront figés et ne bougeront plus.`)) return
    setBusy(true); setMessage(null)
    const r = await authFetch(`/api/admin/releves/${mois}/cloturer`, { method: 'POST' })
    const b = await r.json().catch(() => null)
    setBusy(false)
    if (r.ok) { setMessage({ ok: true, texte: `${nomDuMois(mois)} est clos : ${b.nb_releves} relevé(s) figé(s).` }); reload() }
    else setMessage({ ok: false, texte: typeof b?.detail === 'string' ? b.detail : `Erreur ${r.status}` })
  }

  return (
    <>
      <TitrePage titre="Relevés">
        {MENTION_RELEVE} Un relevé par partenaire et par mois de transmission (heure de Paris), provisoire jusqu'à sa
        clôture : au plus tôt le 8 du mois suivant, une fois toutes les contestations du mois tranchées.
      </TitrePage>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-dark/70">Mois
          <input type="month" value={mois} onChange={(e) => { setMois(e.target.value); setMessage(null) }}
            className="rounded-lg border border-bord bg-white px-3 py-1.5 text-ink" />
        </label>
        {data && <StatutReleve statut={data.statut} />}
        {data?.statut === 'clos' && data.cloture_le && (
          <span className="text-sm text-dark/60">clos le {dateCourte(data.cloture_le)}{data.cloture_par && ` par ${data.cloture_par}`}</span>
        )}
        <div className="ml-auto flex flex-wrap gap-2">
          <button onClick={() => telecharger(`/api/admin/releves/${mois}/csv`, `releves-${mois}.csv`)} className={BTN_SECONDAIRE}>
            <Download className="h-3.5 w-3.5" /> Export CSV
          </button>
          {data?.statut === 'provisoire' && (
            <button onClick={cloturer} disabled={busy} className={BTN_PRIMAIRE}
              title={`Possible à partir du ${dateCourte(data.cloture_possible_le)}`}>
              <Lock className="h-3.5 w-3.5" /> Clore {nomDuMois(mois)}
            </button>
          )}
        </div>
      </div>

      {message && (
        <p className={'mt-4 rounded-xl border px-3 py-2 text-sm ' + (message.ok
          ? 'border-leaf/40 bg-leaf/5 text-leaf' : 'border-primary/40 bg-primary/5 text-primary')}>{message.texte}</p>
      )}
      {error && <Erreur>{error}</Erreur>}
      {!data && !error && <Attente />}

      {data && (
        <section className="mt-6">
          {data.statut === 'provisoire' && (
            <p className="mb-3 text-sm text-dark/70">
              Clôture possible à partir du <strong className="text-ink">{dateCourte(data.cloture_possible_le)}</strong>
              {data.en_attente > 0 && <span className="text-terra"> · {data.en_attente} contestation(s) encore en attente</span>}.
            </p>
          )}
          {data.releves.length === 0 ? (
            <p className="text-sm text-dark/60">Aucune mise en relation transmise en {nomDuMois(mois)}.</p>
          ) : (
            <>
              <div className="overflow-x-auto rounded-xl border border-bord bg-white">
                <table className="w-full min-w-[560px] text-left text-sm">
                  <thead className="bg-sable text-xs text-dark/60">
                    <tr>
                      <th className="px-3 py-2 font-normal">Partenaire</th><th className="px-3 font-normal">Mises en relation</th>
                      <th className="px-3 font-normal">Contestées</th><th className="px-3 text-right font-normal">Total HT</th>
                      <th className="px-3" />
                    </tr>
                  </thead>
                  <tbody>
                    {data.releves.map((r) => (
                      <tr key={r.partenaire.id} className="border-t border-bord">
                        <td className="px-3 py-2 text-ink">{r.partenaire.raison_sociale}
                          {r.partenaire.demo && <span className="ml-1 text-xs text-dark/55">(Démo)</span>}</td>
                        <td className="px-3">{r.nb_lignes}</td>
                        <td className="px-3">{r.nb_contestees}{r.en_attente.length > 0 && <span className="text-terra"> dont {r.en_attente.length} en cours</span>}</td>
                        <td className="px-3 text-right font-semibold text-ink">{euros(r.total_ht)}</td>
                        <td className="px-3 text-right">
                          <button onClick={() => telecharger(`/api/admin/releves/${mois}/${r.partenaire.id}/pdf`, `releve-${mois}.pdf`)}
                            className="inline-flex items-center gap-1 text-xs text-dark/70 underline hover:text-ink">
                            <FileText className="h-3.5 w-3.5" /> PDF
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-bord bg-sable/60">
                      <td className="px-3 py-2 text-dark/70" colSpan={3}>Total HT hors partenaires de démonstration</td>
                      <td className="px-3 text-right font-semibold text-ink">{euros(data.total_ht)}</td><td />
                    </tr>
                  </tfoot>
                </table>
              </div>
              <div className="mt-4 space-y-3">
                {data.releves.map((r) => (
                  <Depliant key={r.partenaire.id} titre={r.partenaire.raison_sociale}
                    icone={<Receipt className="h-5 w-5 shrink-0 text-dark/50" />}
                    resume={<span className="text-dark/60">{r.nb_lignes} ligne(s) · {euros(r.total_ht)} HT</span>}>
                    <Releve r={r} />
                  </Depliant>
                ))}
              </div>
            </>
          )}
        </section>
      )}
    </>
  )
}
