import { useState } from 'react'
import { BadgeCheck, Copy, Pause, Play } from 'lucide-react'
import { useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Partner {
  id: string
  raison_sociale: string
  siret: string | null
  email: string | null
  rge: boolean
  zones: string[] | null
  metiers: string[] | null
  statut: string
  note_moyenne: number | null
  charte_signee_at: string | null
  created_at: string
}

const STATUT_STYLE: Record<string, string> = {
  candidat: 'bg-amber-950/60 text-amber-300 border-amber-900/60',
  actif: 'bg-emerald-950/60 text-emerald-300 border-emerald-900/60',
  suspendu: 'bg-rose-950/60 text-rose-300 border-rose-900/60',
}

export default function AdminPartenaires() {
  useTitle('Back-office — Partenaires')
  const { authFetch } = useAuth()
  const { data, error, reload } = useAdminData<Partner[]>('/api/admin/partners')
  const [busy, setBusy] = useState<string | null>(null)
  // Le mot de passe initial n'est renvoyé qu'UNE fois par l'API : on le garde à l'écran
  // jusqu'à ce que l'admin l'ait transmis au partenaire.
  const [motDePasse, setMotDePasse] = useState<{ email: string; mdp: string } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function agir(p: Partner, action: 'activate' | 'suspend') {
    if (action === 'suspend' && !confirm(`Suspendre ${p.raison_sociale} ? Il n'apparaîtra plus dans l'annuaire public.`)) return
    setBusy(p.id)
    setActionError(null)
    try {
      const r = await authFetch(`/api/admin/partners/${p.id}/${action}`, { method: 'POST' })
      if (!r.ok) throw new Error(`Erreur ${r.status}`)
      const body = await r.json()
      if (action === 'activate' && body.mot_de_passe_initial) {
        setMotDePasse({ email: body.email, mdp: body.mot_de_passe_initial })
      }
      reload()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Action impossible')
    } finally {
      setBusy(null)
    }
  }

  if (error) return <p className="text-rose-400">{error}</p>
  if (!data) return <p className="text-slate-500">Chargement…</p>

  const candidats = data.filter((p) => p.statut === 'candidat')
  const autres = data.filter((p) => p.statut !== 'candidat')

  return (
    <>
      <h1 className="text-xl font-semibold text-white">Partenaires</h1>
      <p className="text-sm text-slate-500 mt-1">
        Activer une candidature signe la charte et génère l'accès à l'espace partenaire.
      </p>

      {actionError && <p className="mt-4 text-sm text-rose-400">{actionError}</p>}

      {motDePasse && (
        <div className="mt-4 rounded-xl border border-emerald-900/60 bg-emerald-950/40 p-4">
          <div className="text-sm text-emerald-300 font-medium">Accès créé — à transmettre maintenant</div>
          <p className="text-xs text-emerald-400/80 mt-1">
            Ce mot de passe n'est affiché qu'une seule fois : il n'est pas stocké en clair.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-sm">
            <span className="rounded bg-slate-900 px-2 py-1 text-slate-300">{motDePasse.email}</span>
            <span className="rounded bg-slate-900 px-2 py-1 text-white">{motDePasse.mdp}</span>
            <button
              onClick={() => navigator.clipboard?.writeText(motDePasse.mdp)}
              className="flex items-center gap-1.5 rounded border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
            >
              <Copy className="w-3.5 h-3.5" /> Copier
            </button>
            <button onClick={() => setMotDePasse(null)} className="text-xs text-slate-500 hover:text-slate-300">
              J'ai transmis
            </button>
          </div>
        </div>
      )}

      {candidats.length > 0 && (
        <section className="mt-8">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-amber-400 mb-3">
            Candidatures à examiner ({candidats.length})
          </h2>
          <div className="space-y-2">
            {candidats.map((p) => (
              <Ligne key={p.id} p={p} busy={busy === p.id} onAgir={agir} />
            ))}
          </div>
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-3">
          Annuaire ({autres.length})
        </h2>
        {autres.length === 0 ? (
          <p className="text-sm text-slate-500">Aucun partenaire activé.</p>
        ) : (
          <div className="space-y-2">
            {autres.map((p) => (
              <Ligne key={p.id} p={p} busy={busy === p.id} onAgir={agir} />
            ))}
          </div>
        )}
      </section>
    </>
  )
}

function Ligne({
  p, busy, onAgir,
}: { p: Partner; busy: boolean; onAgir: (p: Partner, a: 'activate' | 'suspend') => void }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 flex flex-wrap items-center gap-x-4 gap-y-2">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-white">{p.raison_sociale}</span>
          <span className={'rounded-full border px-2 py-0.5 text-xs ' + (STATUT_STYLE[p.statut] ?? 'border-slate-700 text-slate-400')}>
            {p.statut}
          </span>
          {p.rge && (
            <span className="flex items-center gap-1 text-xs text-sky-400" title="Reconnu Garant de l'Environnement">
              <BadgeCheck className="w-3.5 h-3.5" /> RGE
            </span>
          )}
          {p.note_moyenne != null && (
            <span className={'text-xs ' + (p.note_moyenne < 3 ? 'text-rose-400' : 'text-slate-400')}>
              {p.note_moyenne.toFixed(1)}/5
            </span>
          )}
        </div>
        <div className="text-xs text-slate-500 mt-1 truncate">
          {p.email ?? 'sans email'}
          {p.siret && <> · SIRET {p.siret}</>}
          {p.metiers?.length ? <> · {p.metiers.join(', ')}</> : null}
          {p.zones?.length ? <> · zones {p.zones.join(', ')}</> : null}
        </div>
      </div>

      <div className="flex items-center gap-2">
        {p.statut !== 'actif' && (
          <button
            disabled={busy}
            onClick={() => onAgir(p, 'activate')}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" /> {p.statut === 'candidat' ? 'Valider' : 'Réactiver'}
          </button>
        )}
        {p.statut === 'actif' && (
          <button
            disabled={busy}
            onClick={() => onAgir(p, 'suspend')}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <Pause className="w-3.5 h-3.5" /> Suspendre
          </button>
        )}
      </div>
    </div>
  )
}
