import { Activity, RefreshCw, TriangleAlert } from 'lucide-react'
import Depliant from '../../components/Depliant'
import { Attente, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
import { useTitle } from '../../hooks/useTitle'

interface LogEntry {
  agent: string
  action: string
  detail: string | null
  created_at: string
}

/** Les noms sont ceux écrits en base par `agents_engine._log` — « crawler », pas « crawl »
 *  (qui est le nom de la commande). Un agent absent de cette table garde son nom brut. */
const AGENTS: Record<string, { titre: string; aide: string }> = {
  crawler: {
    titre: 'Crawler',
    aide: "Relit les fichiers de kb/, recalcule les embeddings et met la base à jour. Une fiche retirée du fichier est retirée de la base.",
  },
  veille: {
    titre: 'Veille',
    aide: 'Repère les fiches dont la date de mise à jour est dépassée — celles à relire avant qu’Helios ne les cite encore.',
  },
}

export default function AdminAgents() {
  useTitle('Back-office — Agents')
  const { data, error, reload } = useAdminData<LogEntry[]>('/api/admin/agents-log?limit=100')

  // Un journal de cent lignes mélangeant deux agents ne se lit pas : on le replie par agent,
  // et le résumé du bloc dit l'essentiel sans l'ouvrir (dernière exécution, erreurs).
  const parAgent = new Map<string, LogEntry[]>()
  for (const l of data ?? []) {
    const lignes = parAgent.get(l.agent)
    if (lignes) lignes.push(l)
    else parAgent.set(l.agent, [l])
  }

  return (
    <>
      <TitrePage
        titre="Journal des agents"
        action={
          <button onClick={reload} className={BTN_SECONDAIRE}>
            <RefreshCw className="h-3.5 w-3.5" /> Actualiser
          </button>
        }
      >
        Le <strong className="font-semibold text-ink">crawler</strong> alimente la base de connaissances ;
        la <strong className="font-semibold text-ink">veille</strong> repère les fiches périmées. Les deux se
        lancent aussi depuis la page Connaissances.
      </TitrePage>

      {error && <Erreur>{error}</Erreur>}
      {!data && !error && <Attente />}

      {data && data.length === 0 && (
        <p className="mt-6 rounded-2xl border border-bord bg-white p-4 text-sm text-dark/70">
          Aucune exécution enregistrée. Les agents se lancent depuis la page Connaissances, ou en ligne
          de commande&nbsp;:
          <code className="ml-1 rounded bg-cream px-1.5 py-0.5 text-ink">agents/run_agents.py crawl</code>
        </p>
      )}

      {data && data.length > 0 && (
        <div className="mt-6 space-y-3">
          {[...parAgent.entries()].map(([agent, lignes], i) => {
            const erreurs = lignes.filter((l) => l.action === 'error').length
            return (
              <Depliant
                key={agent}
                titre={AGENTS[agent]?.titre ?? agent}
                aide={AGENTS[agent]?.aide}
                icone={<Activity className="h-5 w-5 shrink-0 text-primary" />}
                /* Le premier bloc ouvert : c'est l'agent qui a tourné le plus récemment,
                   l'API renvoyant le journal du plus récent au plus ancien. */
                ouvert={i === 0}
                resume={
                  <span className="flex items-center gap-2">
                    {erreurs > 0 && (
                      <span className="flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-primary">
                        <TriangleAlert className="h-3 w-3" /> {erreurs}
                      </span>
                    )}
                    <span className="tabular-nums">{lignes.length} ligne(s)</span>
                    <span className="hidden sm:inline">
                      · {new Date(lignes[0].created_at).toLocaleString('fr-FR')}
                    </span>
                  </span>
                }
              >
                <div className="-mx-1 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-left text-xs uppercase tracking-wide text-dark/55">
                      <tr>
                        <th className="px-2 py-2 font-semibold">Date</th>
                        <th className="px-2 py-2 font-semibold">Action</th>
                        <th className="px-2 py-2 font-semibold">Détail</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-bord">
                      {lignes.map((l, j) => (
                        <tr key={j} className={l.action === 'error' ? 'text-primary' : 'text-dark'}>
                          <td className="whitespace-nowrap px-2 py-2 tabular-nums text-dark/55">
                            {new Date(l.created_at).toLocaleString('fr-FR')}
                          </td>
                          <td className="whitespace-nowrap px-2 py-2">{l.action}</td>
                          <td className="px-2 py-2 text-dark/70">{l.detail ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Depliant>
            )
          })}
        </div>
      )}
    </>
  )
}
