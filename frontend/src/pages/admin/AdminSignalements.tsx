import { useState } from 'react'
import { Check, ChevronDown, Flag, X } from 'lucide-react'
import {
  Attente, BTN_PRIMAIRE, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData,
} from '../../components/admin/AdminLayout'
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
      <TitrePage titre="Signalements">
        Réponses signalées par les foyers. C'est ce qui rend la constitution vérifiable plutôt
        que seulement affirmée.
      </TitrePage>

      <div className="mt-5 flex flex-wrap gap-2">
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
              'rounded-xl px-3 py-1.5 text-sm transition '
              + (filtre === f.v
                ? 'bg-primary font-semibold text-white'
                : 'border border-bord bg-white text-dark hover:bg-cream')
            }
          >
            {f.l}
          </button>
        ))}
      </div>

      {error && <Erreur>{error}</Erreur>}
      {!data && !error && <Attente />}

      {data && data.length === 0 && (
        <p className="mt-6 rounded-2xl border border-bord bg-white p-4 text-sm text-dark/70">
          Aucun signalement dans cette catégorie.
        </p>
      )}

      {data && data.length > 0 && (
        <div className="mt-5 space-y-3">
          {data.map((s) => (
            <div key={s.id} className="rounded-2xl border border-bord bg-white p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="flex items-center gap-1 rounded-full border border-primary/40 bg-primary/10 px-2 py-0.5 text-primary">
                  <Flag className="h-3 w-3" /> {MOTIF_LABEL[s.motif] ?? s.motif}
                </span>
                {s.model_used && (
                  <span className="rounded-full border border-bord bg-cream px-2 py-0.5 text-dark/70">{s.model_used}</span>
                )}
                {s.rag_score != null && <span className="text-dark/55">score {s.rag_score}</span>}
                <span className="text-dark/55">{s.signale_par ?? 'visiteur anonyme'}</span>
                <span className="ml-auto text-dark/45">{new Date(s.created_at).toLocaleString('fr-FR')}</span>
              </div>

              {s.commentaire && (
                <p className="mt-2 rounded-xl bg-cream px-3 py-2 text-sm text-dark">« {s.commentaire} »</p>
              )}

              <details className="group mt-2">
                <summary className="flex cursor-pointer list-none items-center gap-1.5 text-sm text-primary hover:text-terra">
                  <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
                  Voir la réponse signalée
                </summary>
                <p className="mt-2 whitespace-pre-line rounded-xl border border-bord bg-cream/50 p-3 text-sm text-dark/80">
                  {s.reponse}
                </p>
              </details>

              {s.note_admin && <p className="mt-2 text-xs text-leaf">Suite donnée : {s.note_admin}</p>}

              {s.statut === 'nouveau' && (
                <div className="mt-3 flex gap-2">
                  <button disabled={busy === s.id} onClick={() => traiter(s, 'traite')} className={BTN_PRIMAIRE}>
                    <Check className="h-3.5 w-3.5" /> Corrigé
                  </button>
                  <button disabled={busy === s.id} onClick={() => traiter(s, 'ignore')} className={BTN_SECONDAIRE}>
                    <X className="h-3.5 w-3.5" /> Ignorer
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
