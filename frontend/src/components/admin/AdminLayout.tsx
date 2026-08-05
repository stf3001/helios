import { type ReactNode, useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Activity, BookOpen, Flag, Gauge, HeartPulse, LogOut, MessagesSquare, ShieldCheck, Users2, ExternalLink } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

/** Coquille du back-office — identité visuelle DISTINCTE du site public :
 * fond sombre, typographie système compacte, densité d'information élevée.
 * L'objectif est qu'on sache au premier coup d'œil qu'on n'est plus côté client. */

const NAV = [
  { to: '/admin', label: 'Tableau de bord', Icon: Gauge, end: true },
  { to: '/admin/conversations', label: 'Conversations', Icon: MessagesSquare },
  { to: '/admin/connaissances', label: 'Connaissances', Icon: BookOpen },
  { to: '/admin/signalements', label: 'Signalements', Icon: Flag },
  { to: '/admin/foyers', label: 'Foyers & RGPD', Icon: ShieldCheck },
  { to: '/admin/partenaires', label: 'Partenaires', Icon: Users2 },
  { to: '/admin/services', label: 'Services', Icon: HeartPulse },
  { to: '/admin/agents', label: 'Agents', Icon: Activity },
]

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function doLogout() {
    await logout()
    navigate('/')
  }

  return (
    // `font-sans` du site est remplacé par la pile système : le back-office n'est pas un
    // support de marque, il doit être lisible et dense.
    <div className="min-h-screen bg-slate-950 text-slate-200 [font-family:ui-sans-serif,system-ui,sans-serif]">
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-900/95 backdrop-blur">
        <div className="max-w-[1400px] mx-auto px-4 h-14 flex items-center gap-6">
          <Link to="/admin" className="flex items-center gap-2 shrink-0">
            <img src="/brand/logo-mark.png" alt="" className="h-6 w-auto opacity-90" />
            <span className="font-semibold tracking-tight text-white">
              HELIOS <span className="text-slate-500 font-normal">back-office</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1 text-sm">
            {NAV.map(({ to, label, Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg transition ' +
                  (isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50')
                }
              >
                <Icon className="w-4 h-4" /> {label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-3 text-sm">
            <Link
              to="/"
              className="hidden sm:flex items-center gap-1.5 text-slate-400 hover:text-slate-100"
              title="Ouvrir le site public"
            >
              <ExternalLink className="w-4 h-4" /> Site
            </Link>
            <span className="hidden sm:inline text-slate-500">{user?.email}</span>
            <button onClick={doLogout} className="flex items-center gap-1.5 text-slate-400 hover:text-white" title="Se déconnecter">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Navigation mobile : la barre principale devient trop dense sous 768px */}
        <nav className="md:hidden flex overflow-x-auto scrollbar-hide gap-1 px-3 pb-2 text-sm">
          {NAV.map(({ to, label, Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap ' +
                (isActive ? 'bg-slate-800 text-white' : 'text-slate-400')
              }
            >
              <Icon className="w-4 h-4" /> {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="max-w-[1400px] mx-auto px-4 py-6">{children}</main>
    </div>
  )
}

/** Carte de statistique — unité de base du tableau de bord. */
export function StatCard({
  label, value, hint, accent,
}: { label: string; value: ReactNode; hint?: ReactNode; accent?: 'ok' | 'warn' | 'bad' }) {
  const accentClass =
    accent === 'bad' ? 'text-rose-400' : accent === 'warn' ? 'text-amber-400' : accent === 'ok' ? 'text-emerald-400' : 'text-white'
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={'text-2xl font-semibold mt-1 tabular-nums ' + accentClass}>{value}</div>
      {hint != null && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  )
}

export function Section({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="mt-8">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

/** Appel API admin + états de chargement/erreur, factorisés pour toutes les pages du back-office. */
export function useAdminData<T>(path: string): { data: T | null; error: string | null; reload: () => void } {
  const { authFetch } = useAuth()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let annule = false
    setError(null)
    authFetch(path)
      .then(async (r) => {
        if (r.status === 403) throw new Error("Accès réservé aux administrateurs.")
        if (!r.ok) throw new Error(`Erreur ${r.status}`)
        return r.json()
      })
      .then((d) => { if (!annule) setData(d) })
      .catch((e) => { if (!annule) setError(e.message) })
    return () => { annule = true }
    // `authFetch` est recréé à chaque rendu du provider : l'exclure évite une boucle de requêtes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick])

  return { data, error, reload: () => setTick((t) => t + 1) }
}
