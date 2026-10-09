import { useState } from 'react'
import { EyeOff, Flame, Layers, Play, TriangleAlert } from 'lucide-react'
import Depliant from '../../components/Depliant'
import {
  Attente, BTN_PRIMAIRE, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData,
} from '../../components/admin/AdminLayout'
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

  if (error) return <Erreur>{error}</Erreur>
  if (!data) return <Attente />

  const sources = Object.keys(data.par_source)
  const jamais = filtreSource ? data.jamais_remontees.filter((f) => f.source === filtreSource) : data.jamais_remontees
  const totalFiches = Object.values(data.par_source).reduce((s, n) => s + n, 0)

  return (
    <>
      <TitrePage
        titre="Base de connaissances"
        action={
          <>
            <button disabled={busy} onClick={() => lancer('crawl')} className={BTN_PRIMAIRE}>
              <Play className="h-3.5 w-3.5" /> Lancer le crawler
            </button>
            <button disabled={busy} onClick={() => lancer('veille')} className={BTN_SECONDAIRE}>
              <Play className="h-3.5 w-3.5" /> Lancer la veille
            </button>
          </>
        }
      >
        Ce qu'Helios sait, ce qu'il ne sait pas, et ce qui ne lui sert jamais.
      </TitrePage>

      {message && (
        <p className="mt-4 rounded-xl border border-bord bg-white px-3 py-2 text-sm text-dark">{message}</p>
      )}

      <div className="mt-6 space-y-3">
        <Depliant
          titre="Questions restées sans réponse"
          aide="Aucune source n'a atteint le seuil de pertinence : ce sont les fiches à écrire en priorité, dictées par les usages réels."
          icone={<TriangleAlert className="h-5 w-5 shrink-0 text-terra" />}
          /* Ouvert d'office quand il y a quelque chose à traiter : c'est la seule section
             de la page qui appelle une action d'écriture. */
          ouvert={(questions?.length ?? 0) > 0}
          resume={<span className="tabular-nums">{questions?.length ?? 0}</span>}
        >
          {!questions || questions.length === 0 ? (
            <p className="text-sm text-dark/70">
              Aucune pour l'instant. Ce relevé démarre avec la mise en service du back-office : seuls
              les échanges postérieurs sont mesurés.
            </p>
          ) : (
            <div className="space-y-2">
              {questions.map((q, i) => (
                <div key={i} className="rounded-xl border border-terra/30 bg-terra/5 p-3">
                  <div className="flex items-start gap-3">
                    <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-terra" />
                    <p className="flex-1 text-sm text-dark">{q.question}</p>
                    <span className="shrink-0 text-xs tabular-nums text-terra">score {q.score}</span>
                  </div>
                  <div className="mt-1 pl-7 text-xs text-dark/50">
                    {new Date(q.created_at).toLocaleString('fr-FR')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Depliant>

        <Depliant
          titre="Fiches les plus mobilisées"
          aide="Nombre de fois où la fiche est remontée dans la recherche — ce qui répond réellement aux besoins."
          icone={<Flame className="h-5 w-5 shrink-0 text-primary" />}
          resume={<span className="tabular-nums">{data.plus_remontees.length}</span>}
        >
          <div className="divide-y divide-bord rounded-xl border border-bord bg-white">
            {data.plus_remontees.map((f, i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-2.5 text-sm">
                <Flame className="h-4 w-4 shrink-0 text-primary" />
                <span className="flex-1 truncate text-dark">{f.titre}</span>
                <span className="shrink-0 rounded-full bg-cream px-2 py-0.5 text-xs text-dark/70">{f.source}</span>
                <span className="w-10 shrink-0 text-right tabular-nums text-dark/70">{f.n}×</span>
              </div>
            ))}
            {data.plus_remontees.length === 0 && (
              <p className="px-3 py-3 text-sm text-dark/60">Aucune donnée d'usage encore.</p>
            )}
          </div>
        </Depliant>

        <Depliant
          titre="Fiches jamais remontées"
          icone={<EyeOff className="h-5 w-5 shrink-0 text-dark/40" />}
          resume={<span className="tabular-nums">{data.jamais_remontees.length}</span>}
        >
          {data.volume && !data.volume.echantillon_suffisant ? (
            // Garde-fou anti-surinterprétation : sans assez d'usage, l'absence ne prouve rien.
            <p className="rounded-xl border border-terra/30 bg-terra/5 px-3 py-2 text-xs text-terra">
              Échantillon encore trop faible pour conclure : {data.volume.reponses_avec_sources} réponse(s)
              n'ont pu mobiliser que {data.volume.tirages_max} fiches au maximum, sur {data.volume.total_fiches}.
              Une fiche absente de cette liste n'est pas nécessairement mal écrite — elle n'a simplement
              pas encore eu l'occasion de servir.
            </p>
          ) : (
            <p className="text-sm text-dark/70">
              Jamais retenues par la recherche : soit le sujet n'est jamais demandé, soit la formulation
              ne correspond pas aux mots des utilisateurs. À relire avant d'en écrire de nouvelles.
            </p>
          )}

          <select
            value={filtreSource}
            onChange={(e) => setFiltreSource(e.target.value)}
            className="rounded-xl border border-bord bg-white px-2 py-1.5 text-dark"
          >
            <option value="">Toutes les sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <div className="max-h-[420px] divide-y divide-bord overflow-y-auto rounded-xl border border-bord bg-white">
            {jamais.map((f, i) => (
              <div key={i} className="flex items-center gap-3 px-3 py-2 text-sm">
                <EyeOff className="h-3.5 w-3.5 shrink-0 text-dark/40" />
                <span className="flex-1 truncate text-dark/80">{f.titre}</span>
                <span className="shrink-0 rounded-full bg-cream px-2 py-0.5 text-xs text-dark/60">{f.source}</span>
              </div>
            ))}
            {jamais.length === 0 && <p className="px-3 py-3 text-sm text-dark/60">Aucune.</p>}
          </div>
        </Depliant>

        <Depliant
          titre="Répartition par source"
          icone={<Layers className="h-5 w-5 shrink-0 text-sky" />}
          resume={<span className="tabular-nums">{totalFiches} fiches · {sources.length} sources</span>}
        >
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(data.par_source).map(([s, n]) => (
              <span key={s} className="rounded-full border border-bord bg-cream px-2.5 py-1 text-xs text-dark">
                {s} <span className="tabular-nums text-dark/55">{n}</span>
              </span>
            ))}
          </div>
          <button onClick={reload} className="text-sm text-primary underline hover:text-terra">
            Recharger les compteurs
          </button>
        </Depliant>
      </div>
    </>
  )
}
