import { CircleAlert, CircleCheck, CircleMinus, RefreshCw } from 'lucide-react'
import { Attente, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
import { useTitle } from '../../hooks/useTitle'

interface Service {
  nom: string
  etat: 'ok' | 'attention' | 'erreur' | 'inactif'
  detail: string
  latence_ms: number | null
}

const ETAT = {
  ok: { Icon: CircleCheck, couleur: 'text-leaf', bord: 'border-bord' },
  attention: { Icon: CircleAlert, couleur: 'text-terra', bord: 'border-terra/40' },
  erreur: { Icon: CircleAlert, couleur: 'text-primary', bord: 'border-primary/40' },
  inactif: { Icon: CircleMinus, couleur: 'text-dark/35', bord: 'border-bord' },
} as const

export default function AdminServices() {
  useTitle('Back-office — Services')
  const { data, error, reload } = useAdminData<{ services: Service[]; en_erreur: number }>('/api/admin/services')

  return (
    <>
      <TitrePage
        titre="État des services"
        action={
          <button onClick={reload} className={BTN_SECONDAIRE}>
            <RefreshCw className="h-3.5 w-3.5" /> Retester
          </button>
        }
      >
        « Inactif » signifie non configuré, pas en panne — Helios fonctionne alors en mode dégradé prévu.
      </TitrePage>

      {error && <Erreur>{error}</Erreur>}
      {!data && !error && <Attente>Test des services en cours…</Attente>}

      {data && (
        <>
          <div className={'mt-5 rounded-xl border px-3 py-2 text-sm ' + (data.en_erreur > 0 ? 'border-primary/40 bg-primary/5 text-primary' : 'border-leaf/40 bg-leaf/5 text-leaf')}>
            {data.en_erreur > 0
              ? `${data.en_erreur} service(s) en erreur — Helios est probablement dégradé.`
              : 'Aucun service en erreur.'}
          </div>

          <div className="mt-4 space-y-2">
            {data.services.map((s) => {
              const { Icon, couleur, bord } = ETAT[s.etat] ?? ETAT.inactif
              return (
                <div key={s.nom} className={'flex items-center gap-3 rounded-2xl border bg-white p-4 ' + bord}>
                  <Icon className={'h-5 w-5 shrink-0 ' + couleur} />
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-ink">{s.nom}</div>
                    <div className="truncate text-xs text-dark/60">{s.detail}</div>
                  </div>
                  {s.latence_ms != null && (
                    <span className="shrink-0 text-xs tabular-nums text-dark/55">{s.latence_ms} ms</span>
                  )}
                </div>
              )
            })}
          </div>

          <p className="mt-6 text-xs text-dark/55">
            L'API Claude n'est pas appelée pour ce test : cela consommerait des crédits pour rien. Seul l'état
            de configuration est rapporté.
          </p>
        </>
      )}
    </>
  )
}
