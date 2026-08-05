import { RefreshCw } from 'lucide-react'
import { useAdminData } from '../../components/admin/AdminLayout'
import { useTitle } from '../../hooks/useTitle'

interface LogEntry {
  agent: string
  action: string
  detail: string | null
  created_at: string
}

export default function AdminAgents() {
  useTitle('Back-office — Agents')
  const { data, error, reload } = useAdminData<LogEntry[]>('/api/admin/agents-log?limit=100')

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-white">Journal des agents</h1>
          <p className="text-sm text-slate-500 mt-1">
            Le <span className="text-slate-400">crawler</span> alimente la base de connaissances ;
            la <span className="text-slate-400">veille</span> repère les fiches périmées.
          </p>
        </div>
        <button
          onClick={reload}
          className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Actualiser
        </button>
      </div>

      {error && <p className="mt-4 text-rose-400">{error}</p>}
      {!data && !error && <p className="mt-4 text-slate-500">Chargement…</p>}

      {data && data.length === 0 && (
        <p className="mt-6 text-sm text-slate-500">
          Aucune exécution enregistrée. Les agents se lancent en ligne de commande :
          <code className="ml-1 rounded bg-slate-900 px-1.5 py-0.5 text-slate-400">agents/run_agents.py crawl</code>
        </p>
      )}

      {data && data.length > 0 && (
        <div className="mt-5 overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">Agent</th>
                <th className="px-4 py-2 font-medium">Action</th>
                <th className="px-4 py-2 font-medium">Détail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/50">
              {data.map((l, i) => (
                <tr key={i} className={l.action === 'error' ? 'text-rose-300' : 'text-slate-300'}>
                  <td className="whitespace-nowrap px-4 py-2 tabular-nums text-slate-500">
                    {new Date(l.created_at).toLocaleString('fr-FR')}
                  </td>
                  <td className="px-4 py-2">
                    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-xs">{l.agent}</span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-2">{l.action}</td>
                  <td className="px-4 py-2 text-slate-400">{l.detail ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
