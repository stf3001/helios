import { useEffect, useState } from 'react'
import { AlertTriangle, ArrowLeft, MessageSquare, User2 } from 'lucide-react'
import { useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Ligne {
  id: string
  mode: string
  started_at: string
  dernier_message: string | null
  email: string | null
  prenom: string | null
  nb_messages: number
  sans_reponse: boolean
}

interface MessageDetail {
  role: string
  content: string
  created_at: string
  model_used: string | null
  rag_score: number | null
  citations: { titre: string; cat: string | null; score: number }[] | null
  tokens: number | null
  cout_eur: number | null
  constitution_version: string | null
}

interface Detail {
  id: string
  mode: string
  started_at: string
  foyer: { email: string; prenom: string | null } | null
  messages: MessageDetail[]
  seuil_pertinence: number
}

const VOIE: Record<string, { label: string; classe: string }> = {
  kb: { label: 'instantané', classe: 'bg-emerald-950 text-emerald-300' },
  local: { label: 'local', classe: 'bg-sky-950 text-sky-300' },
  api: { label: 'API', classe: 'bg-amber-950 text-amber-300' },
}

export default function AdminConversations() {
  useTitle('Back-office — Conversations')
  const [mode, setMode] = useState<string>('')
  const [ouverte, setOuverte] = useState<string | null>(null)
  const { data, error } = useAdminData<{ total: number; conversations: Ligne[] }>(
    `/api/admin/conversations?limit=60${mode ? `&mode=${mode}` : ''}`,
  )

  if (ouverte) return <DetailConversation id={ouverte} onRetour={() => setOuverte(null)} />

  return (
    <>
      <h1 className="text-xl font-semibold text-white">Conversations</h1>
      <p className="text-sm text-slate-500 mt-1">
        Échanges réels avec Helios. L'identité du foyer est affichée — accès complet assumé.
      </p>

      <div className="mt-5 flex gap-2">
        {[
          { v: '', l: 'Toutes' },
          { v: 'public', l: 'Public' },
          { v: 'connecte', l: 'Connecté' },
        ].map((f) => (
          <button
            key={f.v}
            onClick={() => setMode(f.v)}
            className={
              'rounded-lg px-3 py-1.5 text-sm ' +
              (mode === f.v ? 'bg-slate-700 text-white' : 'border border-slate-800 text-slate-400 hover:bg-slate-800')
            }
          >
            {f.l}
          </button>
        ))}
      </div>

      {error && <p className="mt-4 text-rose-400">{error}</p>}
      {!data && !error && <p className="mt-4 text-slate-500">Chargement…</p>}

      {data && (
        <>
          <p className="mt-4 text-xs text-slate-500">{data.total} conversation(s) au total</p>
          <div className="mt-3 space-y-2">
            {data.conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => setOuverte(c.id)}
                className="w-full text-left rounded-xl border border-slate-800 bg-slate-900 p-4 hover:border-slate-700"
              >
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className={'rounded px-1.5 py-0.5 text-xs ' + (c.mode === 'connecte' ? 'bg-slate-800 text-slate-200' : 'bg-slate-800/60 text-slate-400')}>
                    {c.mode}
                  </span>
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <User2 className="w-3.5 h-3.5 text-slate-500" />
                    {c.email ?? <span className="text-slate-500">visiteur anonyme</span>}
                  </span>
                  <span className="flex items-center gap-1 text-slate-500 text-xs">
                    <MessageSquare className="w-3.5 h-3.5" /> {c.nb_messages}
                  </span>
                  {c.sans_reponse && (
                    <span className="flex items-center gap-1 rounded bg-amber-950 px-1.5 py-0.5 text-xs text-amber-300">
                      <AlertTriangle className="w-3 h-3" /> sans réponse pertinente
                    </span>
                  )}
                  <span className="ml-auto text-xs tabular-nums text-slate-600">
                    {new Date(c.dernier_message ?? c.started_at).toLocaleString('fr-FR')}
                  </span>
                </div>
              </button>
            ))}
            {data.conversations.length === 0 && <p className="text-sm text-slate-500">Aucune conversation.</p>}
          </div>
        </>
      )}
    </>
  )
}

function DetailConversation({ id, onRetour }: { id: string; onRetour: () => void }) {
  const { authFetch } = useAuth()
  const [detail, setDetail] = useState<Detail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let annule = false
    authFetch(`/api/admin/conversations/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Erreur ${r.status}`))))
      .then((d) => { if (!annule) setDetail(d) })
      .catch((e) => { if (!annule) setError(e.message) })
    return () => { annule = true }
    // `authFetch` est recréé à chaque rendu du provider : l'exclure évite une boucle de requêtes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  return (
    <>
      <button onClick={onRetour} className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white">
        <ArrowLeft className="w-4 h-4" /> Toutes les conversations
      </button>

      {error && <p className="mt-4 text-rose-400">{error}</p>}
      {!detail && !error && <p className="mt-4 text-slate-500">Chargement…</p>}

      {detail && (
        <>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <h1 className="text-lg font-semibold text-white">
              {detail.foyer ? `${detail.foyer.prenom ?? ''} ${detail.foyer.email}`.trim() : 'Visiteur anonyme'}
            </h1>
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">{detail.mode}</span>
            <span className="text-xs text-slate-500">{new Date(detail.started_at).toLocaleString('fr-FR')}</span>
          </div>

          <div className="mt-5 space-y-3">
            {detail.messages.map((m, i) => {
              const estHelios = m.role === 'helios'
              const voie = m.model_used ? VOIE[m.model_used] : null
              const scoreFaible = m.rag_score != null && m.rag_score < detail.seuil_pertinence
              return (
                <div
                  key={i}
                  className={
                    'rounded-xl border p-4 ' +
                    (estHelios ? 'border-slate-800 bg-slate-900' : 'border-slate-800/60 bg-slate-900/40')
                  }
                >
                  <div className="flex flex-wrap items-center gap-2 mb-2 text-xs">
                    <span className={estHelios ? 'font-medium text-primary' : 'font-medium text-slate-400'}>
                      {estHelios ? 'Helios' : 'Foyer'}
                    </span>
                    {voie && <span className={'rounded px-1.5 py-0.5 ' + voie.classe}>{voie.label}</span>}
                    {m.rag_score != null && (
                      <span className={scoreFaible ? 'text-amber-400' : 'text-slate-500'}>
                        score {m.rag_score}
                        {scoreFaible && ' · sous le seuil'}
                      </span>
                    )}
                    {m.cout_eur != null && <span className="text-slate-500">{m.cout_eur.toFixed(4)} €</span>}
                    {m.constitution_version && <span className="text-slate-600">constitution {m.constitution_version}</span>}
                    <span className="ml-auto text-slate-600">{new Date(m.created_at).toLocaleTimeString('fr-FR')}</span>
                  </div>

                  <p className="whitespace-pre-line text-sm text-slate-200">{m.content}</p>

                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 border-t border-slate-800 pt-2">
                      <div className="text-xs text-slate-500 mb-1">Sources mobilisées</div>
                      <div className="flex flex-wrap gap-1.5">
                        {m.citations.map((c, j) => (
                          <span key={j} className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                            {c.titre.slice(0, 60)} <span className="text-slate-600">{c.score}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </>
  )
}
