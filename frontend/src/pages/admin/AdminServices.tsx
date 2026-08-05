import { CircleAlert, CircleCheck, CircleMinus, RefreshCw } from 'lucide-react'
import { useAdminData } from '../../components/admin/AdminLayout'
import { useTitle } from '../../hooks/useTitle'

interface Service {
  nom: string
  etat: 'ok' | 'attention' | 'erreur' | 'inactif'
  detail: string
  latence_ms: number | null
}

const ETAT = {
  ok: { Icon: CircleCheck, couleur: 'text-emerald-400', bord: 'border-slate-800' },
  attention: { Icon: CircleAlert, couleur: 'text-amber-400', bord: 'border-amber-900/60' },
  erreur: { Icon: CircleAlert, couleur: 'text-rose-400', bord: 'border-rose-900/60' },
  inactif: { Icon: CircleMinus, couleur: 'text-slate-500', bord: 'border-slate-800' },
} as const

export default function AdminServices() {
  useTitle('Back-office — Services')
  const { data, error, reload } = useAdminData<{ services: Service[]; en_erreur: number }>('/api/admin/services')

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-white">État des services</h1>
          <p className="text-sm text-slate-500 mt-1">
            « Inactif » signifie non configuré, pas en panne — Helios fonctionne alors en mode dégradé prévu.
          </p>
        </div>
        <button
          onClick={reload}
          className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Retester
        </button>
      </div>

      {error && <p className="mt-4 text-rose-400">{error}</p>}
      {!data && !error && <p className="mt-4 text-slate-500">Test des services en cours…</p>}

      {data && (
        <>
          <div className={'mt-5 rounded-lg border px-3 py-2 text-sm ' + (data.en_erreur > 0 ? 'border-rose-900/60 bg-rose-950/40 text-rose-300' : 'border-emerald-900/60 bg-emerald-950/40 text-emerald-300')}>
            {data.en_erreur > 0
              ? `${data.en_erreur} service(s) en erreur — Helios est probablement dégradé.`
              : 'Aucun service en erreur.'}
          </div>

          <div className="mt-4 space-y-2">
            {data.services.map((s) => {
              const { Icon, couleur, bord } = ETAT[s.etat] ?? ETAT.inactif
              return (
                <div key={s.nom} className={'flex items-center gap-3 rounded-xl border bg-slate-900 p-4 ' + bord}>
                  <Icon className={'w-5 h-5 shrink-0 ' + couleur} />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-white">{s.nom}</div>
                    <div className="text-xs text-slate-500 truncate">{s.detail}</div>
                  </div>
                  {s.latence_ms != null && (
                    <span className="text-xs tabular-nums text-slate-500 shrink-0">{s.latence_ms} ms</span>
                  )}
                </div>
              )
            })}
          </div>

          <p className="mt-6 text-xs text-slate-600">
            L'API Claude n'est pas appelée pour ce test : cela consommerait des crédits pour rien. Seul l'état
            de configuration est rapporté.
          </p>
        </>
      )}
    </>
  )
}
