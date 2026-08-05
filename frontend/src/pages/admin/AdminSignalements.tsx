import { useState } from 'react'
import { Check, Flag, X } from 'lucide-react'
import { useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Signalement {
  id: string
  motif: string
  commentaire: string | null
  statut: string
  note_admin: string | null
  created_at: string
  signale_par: string | null
  conversation_id: string | null
  reponse: string
  model_used: string | null
  rag_score: number | null
}

const MOTIF_LABEL: Record<string, string> = {
  faux: 'Réponse fausse',
  hors_sujet: 'Hors sujet',
  genant: 'Gênant',
  incomprehensible: 'Incompréhensible',
  autre: 'Autre',
}

export default function AdminSignalements() {
  useTitle('Back-office — Signalements')
  const { authFetch } = useAuth()
  const [filtre, setFiltre] = useState('nouveau')
  const { data, error, reload } = useAdminData<Signalement[]>(
    `/api/admin/signalements${filtre ? `?statut=${filtre}` : ''}`,
  )
  const [busy, setBusy] = useState<string | null>(null)

  async function traiter(s: Signalement, statut: 'traite' | 'ignore') {
    const note = window.prompt(
      statut === 'traite'
        ? "Qu'avez-vous corrigé ? (fiche ajoutée, formulation revue…)"
        : 'Pourquoi ignorer ce signalement ?',
    )
    if (note === null) return
    setBusy(s.id)
    try {
      await authFetch(`/api/admin/signalements/${s.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ statut, note_admin: note || null }),
      })
      reload()
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <h1 className="text-xl font-semibold text-white">Signalements</h1>
      <p className="text-sm text-slate-500 mt-1">
        Réponses signalées par les foyers. C'est ce qui rend la constitution vérifiable plutôt
        que seulement affirmée.
      </p>

      <div className="mt-5 flex gap-2">
        {[
          { v: 'nouveau', l: 'À traiter' },
          { v: 'traite', l: 'Traités' },
          { v: 'ignore', l: 'Ignorés' },
          { v: '', l: 'Tous' },
        ].map((f) => (
          <button
            key={f.v}
            onClick={() => setFiltre(f.v)}
            className={
              'rounded-lg px-3 py-1.5 text-sm ' +
              (filtre === f.v ? 'bg-slate-700 text-white' : 'border border-slate-800 text-slate-400 hover:bg-slate-800')
            }
          >
            {f.l}
          </button>
        ))}
      </div>

      {error && <p className="mt-4 text-rose-400">{error}</p>}
      {!data && !error && <p className="mt-4 text-slate-500">Chargement…</p>}

      {data && data.length === 0 && (
        <p className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-500">
          Aucun signalement dans cette catégorie.
        </p>
      )}

      {data && data.length > 0 && (
        <div className="mt-5 space-y-3">
          {data.map((s) => (
            <div key={s.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="flex items-center gap-1 rounded bg-rose-950 px-2 py-0.5 text-rose-300">
                  <Flag className="w-3 h-3" /> {MOTIF_LABEL[s.motif] ?? s.motif}
                </span>
                {s.model_used && <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-400">{s.model_used}</span>}
                {s.rag_score != null && <span className="text-slate-500">score {s.rag_score}</span>}
                <span className="text-slate-500">{s.signale_par ?? 'visiteur anonyme'}</span>
                <span className="ml-auto text-slate-600">{new Date(s.created_at).toLocaleString('fr-FR')}</span>
              </div>

              {s.commentaire && (
                <p className="mt-2 rounded-lg bg-slate-950 px-3 py-2 text-sm text-slate-300">« {s.commentaire} »</p>
              )}

              <details className="mt-2">
                <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-300">
                  Voir la réponse signalée
                </summary>
                <p className="mt-2 whitespace-pre-line rounded-lg border border-slate-800 p-3 text-sm text-slate-400">
                  {s.reponse}
                </p>
              </details>

              {s.note_admin && (
                <p className="mt-2 text-xs text-emerald-400">Suite donnée : {s.note_admin}</p>
              )}

              {s.statut === 'nouveau' && (
                <div className="mt-3 flex gap-2">
                  <button
                    disabled={busy === s.id}
                    onClick={() => traiter(s, 'traite')}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    <Check className="w-3.5 h-3.5" /> Corrigé
                  </button>
                  <button
                    disabled={busy === s.id}
                    onClick={() => traiter(s, 'ignore')}
                    className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                  >
                    <X className="w-3.5 h-3.5" /> Ignorer
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )
}
