import { useState } from 'react'
import { EyeOff, Flame, Play, TriangleAlert } from 'lucide-react'
import { Section, useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Fiche {
  titre: string
  source: string
  n?: number
  date_maj?: string
}

interface Kb {
  par_source: Record<string, number>
  plus_remontees: Fiche[]
  jamais_remontees: Fiche[]
  obsoletes: Fiche[]
  volume?: {
    reponses_avec_sources: number
    tirages_max: number
    total_fiches: number
    echantillon_suffisant: boolean
  }
}

interface Question {
  question: string
  score: number
  created_at: string
  conversation_id: string
}

export default function AdminConnaissances() {
  useTitle('Back-office — Connaissances')
  const { authFetch } = useAuth()
  const { data, error, reload } = useAdminData<Kb>('/api/admin/kb')
  const { data: questions } = useAdminData<Question[]>('/api/admin/questions-sans-reponse?limit=50')
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [filtreSource, setFiltreSource] = useState<string>('')

  async function lancer(agent: 'crawl' | 'veille') {
    setBusy(true)
    setMessage(null)
    try {
      const r = await authFetch(`/api/admin/agents/run?agent=${agent}`, { method: 'POST' })
      const body = await r.json()
      if (!r.ok) throw new Error(body.detail ?? `Erreur ${r.status}`)
      setMessage(body.message)
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Lancement impossible')
    } finally {
      setBusy(false)
    }
  }

  if (error) return <p className="text-rose-400">{error}</p>
  if (!data) return <p className="text-slate-500">Chargement…</p>

  const sources = Object.keys(data.par_source)
  const jamais = filtreSource ? data.jamais_remontees.filter((f) => f.source === filtreSource) : data.jamais_remontees

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-white">Base de connaissances</h1>
          <p className="text-sm text-slate-500 mt-1">
            Ce qu'Helios sait, ce qu'il ne sait pas, et ce qui ne lui sert jamais.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            disabled={busy}
            onClick={() => lancer('crawl')}
            className="flex items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-1.5 text-sm text-white hover:bg-slate-600 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" /> Lancer le crawler
          </button>
          <button
            disabled={busy}
            onClick={() => lancer('veille')}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" /> Lancer la veille
          </button>
        </div>
      </div>

      {message && (
        <p className="mt-4 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-300">{message}</p>
      )}

      <Section title={`Questions restées sans réponse (${questions?.length ?? 0})`}>
        <p className="text-xs text-slate-500 mb-3">
          Aucune source n'a atteint le seuil de pertinence : ce sont les fiches à écrire en priorité,
          dictées par les usages réels.
        </p>
        {!questions || questions.length === 0 ? (
          <p className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-500">
            Aucune pour l'instant. Ce relevé démarre avec la mise en service du back-office : seuls
            les échanges postérieurs sont mesurés.
          </p>
        ) : (
          <div className="space-y-2">
            {questions.map((q, i) => (
              <div key={i} className="rounded-xl border border-amber-900/40 bg-slate-900 p-3">
                <div className="flex items-start gap-3">
                  <TriangleAlert className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
                  <p className="flex-1 text-sm text-slate-200">{q.question}</p>
                  <span className="shrink-0 text-xs tabular-nums text-amber-400">score {q.score}</span>
                </div>
                <div className="mt-1 pl-7 text-xs text-slate-600">
                  {new Date(q.created_at).toLocaleString('fr-FR')}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Fiches les plus mobilisées">
        <p className="text-xs text-slate-500 mb-3">
          Nombre de fois où la fiche est remontée dans la recherche — ce qui répond réellement aux besoins.
        </p>
        <div className="rounded-xl border border-slate-800 bg-slate-900 divide-y divide-slate-800">
          {data.plus_remontees.map((f, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2.5 text-sm">
              <Flame className="w-4 h-4 shrink-0 text-orange-400" />
              <span className="flex-1 truncate text-slate-200">{f.titre}</span>
              <span className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-400">{f.source}</span>
              <span className="w-10 shrink-0 text-right tabular-nums text-slate-400">{f.n}×</span>
            </div>
          ))}
          {data.plus_remontees.length === 0 && (
            <p className="px-4 py-3 text-sm text-slate-500">Aucune donnée d'usage encore.</p>
          )}
        </div>
      </Section>

      <Section
        title={`Fiches jamais remontées (${data.jamais_remontees.length})`}
        action={
          <select
            value={filtreSource}
            onChange={(e) => setFiltreSource(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-300"
          >
            <option value="">Toutes les sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        }
      >
        {data.volume && !data.volume.echantillon_suffisant ? (
          // Garde-fou anti-surinterprétation : sans assez d'usage, l'absence ne prouve rien.
          <p className="mb-3 rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-xs text-amber-300/90">
            Échantillon encore trop faible pour conclure : {data.volume.reponses_avec_sources} réponse(s)
            n'ont pu mobiliser que {data.volume.tirages_max} fiches au maximum, sur {data.volume.total_fiches}.
            Une fiche absente de cette liste n'est pas nécessairement mal écrite — elle n'a simplement
            pas encore eu l'occasion de servir.
          </p>
        ) : (
          <p className="text-xs text-slate-500 mb-3">
            Jamais retenues par la recherche : soit le sujet n'est jamais demandé, soit la formulation
            ne correspond pas aux mots des utilisateurs. À relire avant d'en écrire de nouvelles.
          </p>
        )}
        <div className="rounded-xl border border-slate-800 bg-slate-900 divide-y divide-slate-800 max-h-[420px] overflow-y-auto">
          {jamais.map((f, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2 text-sm">
              <EyeOff className="w-3.5 h-3.5 shrink-0 text-slate-600" />
              <span className="flex-1 truncate text-slate-400">{f.titre}</span>
              <span className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-500">{f.source}</span>
            </div>
          ))}
          {jamais.length === 0 && <p className="px-4 py-3 text-sm text-slate-500">Aucune.</p>}
        </div>
      </Section>

      <Section title="Répartition par source">
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(data.par_source).map(([s, n]) => (
            <span key={s} className="rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-300">
              {s} <span className="text-slate-500 tabular-nums">{n}</span>
            </span>
          ))}
        </div>
        <button onClick={reload} className="mt-3 text-xs text-slate-500 hover:text-slate-300">
          Recharger les compteurs
        </button>
      </Section>
    </>
  )
}
