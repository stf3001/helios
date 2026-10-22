import { useState } from 'react'
import { Check, Scale, X } from 'lucide-react'
import Depliant from '../../components/Depliant'
import { Attente, BTN_DANGER, BTN_PRIMAIRE, Erreur, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
import { Creneaux } from '../../components/mer/Dossier'
import { STATUT_CONTESTATION, dateCourte } from '../../components/mer/libelles'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

/** File des contestations (mises en relation, lot 3). Acceptée → la demande n'est plus
 *  facturable (`prix_ht` gardé) ; refusée → rien ne change. Le motif est obligatoire. */
interface Contestation {
  id: string; motif: string; libelle: string; commentaire: string; essais: string[] | null; statut: string
  decision_motif: string | null; decidee_le: string | null; created_at: string
  lead: {
    id: string; metier: string | null; transmis_le: string; code_postal: string | null
    creneaux: { jour: string; plage: string }[]; a_un_telephone: boolean; facturable: boolean; prix_ht: number | null
  }
  partenaire: { id: string; raison_sociale: string; demo: boolean }
  doublons_helios_12_mois: number
}

export default function AdminContestations() {
  useTitle('Back-office — Contestations')
  const attente = useAdminData<Contestation[]>('/api/admin/contestations?statut=en_attente')
  const acceptees = useAdminData<Contestation[]>('/api/admin/contestations?statut=acceptee')
  const refusees = useAdminData<Contestation[]>('/api/admin/contestations?statut=refusee')

  if (attente.error) return <Erreur>{attente.error}</Erreur>
  if (!attente.data) return <Attente />
  const recharger = () => { attente.reload(); acceptees.reload(); refusees.reload() }

  return (
    <>
      <TitrePage titre="Contestations">
        Un partenaire conteste une mise en relation dans les 7 jours qui suivent sa transmission. Acceptée, elle
        n'est plus facturable ; refusée, rien ne change. Le motif de votre décision est conservé.
      </TitrePage>

      <section className="mt-8">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-terra">
          À trancher ({attente.data.length})
        </h2>
        {attente.data.length === 0
          ? <p className="text-sm text-dark/60">Aucune contestation en attente.</p>
          : <div className="space-y-3">{attente.data.map((c) => <Carte key={c.id} c={c} onDecide={recharger} />)}</div>}
      </section>

      {[['Acceptées', acceptees.data], ['Refusées', refusees.data]].map(([titre, liste]) => (
        <section key={titre as string} className="mt-6">
          <Depliant titre={titre as string} icone={<Scale className="h-5 w-5 shrink-0 text-dark/50" />}
            resume={<span className="text-dark/55">{(liste as Contestation[] | null)?.length ?? '…'}</span>}>
            <div className="space-y-3">
              {((liste as Contestation[] | null) ?? []).map((c) => <Carte key={c.id} c={c} />)}
            </div>
          </Depliant>
        </section>
      ))}
    </>
  )
}

function Carte({ c, onDecide }: { c: Contestation; onDecide?: () => void }) {
  const { authFetch } = useAuth()
  const [motif, setMotif] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function decider(acceptee: boolean) {
    setBusy(true); setErreur(null)
    const r = await authFetch(`/api/admin/contestations/${c.id}/decision`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ acceptee, motif }),
    })
    setBusy(false)
    if (r.ok) { onDecide?.(); return }
    const b = await r.json().catch(() => null)
    setErreur(typeof b?.detail === 'string' ? b.detail : 'Indiquez un motif (3 caractères au moins).')
  }

  return (
    <div className="rounded-xl border border-bord bg-cream/50 p-4 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold text-ink">{c.partenaire.raison_sociale}</span>
        {c.partenaire.demo && <span className="text-xs text-dark/55">(Démo)</span>}
        <span className="text-dark/60">· {c.lead.metier} · {c.lead.code_postal} · transmise le {dateCourte(c.lead.transmis_le)}</span>
        <span className="text-dark/60">· contestée le {dateCourte(c.created_at)}</span>
        {c.statut !== 'en_attente' && (
          <span className={'rounded-full border px-2 py-0.5 text-xs ' + (c.statut === 'acceptee'
            ? 'border-leaf/40 bg-leaf/10 text-leaf' : 'border-bord bg-sable text-dark/60')}>
            {STATUT_CONTESTATION[c.statut]}
          </span>
        )}
      </div>
      <p className="mt-2"><span className="font-semibold text-ink">{c.libelle}</span></p>
      <p className="mt-1 whitespace-pre-line text-dark/80">« {c.commentaire} »</p>
      {c.essais && <p className="mt-1 text-dark/70">Essais d'appel : {c.essais.map(dateCourte).join(', ')}</p>}
      {c.motif === 'injoignable' && (
        <div className="mt-2">
          <Creneaux creneaux={c.lead.creneaux} />
          {!c.lead.a_un_telephone && <p className="mt-1 text-terra">Le foyer n'a pas donné de téléphone : il fallait lui écrire.</p>}
        </div>
      )}
      {c.motif === 'doublon' && (
        <p className="mt-1 text-dark/70">
          Chez Hélios : {c.doublons_helios_12_mois} demande(s) du même foyer pour ce métier à ce partenaire dans les 12 mois
          précédents. Un doublon venu en direct ne se voit pas ici.
        </p>
      )}
      <p className="mt-1 text-dark/60">
        {c.lead.prix_ht != null && `${c.lead.prix_ht} € HT · `}{c.lead.facturable ? 'facturable' : 'non facturable'}
      </p>
      {c.statut === 'en_attente' ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input value={motif} onChange={(e) => setMotif(e.target.value)} placeholder="Motif de votre décision"
            aria-label="Motif de la décision" className="min-w-0 flex-1 rounded-lg border border-bord bg-white px-3 py-1.5" />
          <button disabled={busy || motif.trim().length < 3} onClick={() => decider(true)} className={BTN_PRIMAIRE}>
            <Check className="h-3.5 w-3.5" /> Accepter
          </button>
          <button disabled={busy || motif.trim().length < 3} onClick={() => decider(false)} className={BTN_DANGER}>
            <X className="h-3.5 w-3.5" /> Refuser
          </button>
        </div>
      ) : (
        <p className="mt-2 text-dark/70">Décision du {dateCourte(c.decidee_le)} : {c.decision_motif}</p>
      )}
      {erreur && <p className="mt-1 text-primary">{erreur}</p>}
    </div>
  )
}
