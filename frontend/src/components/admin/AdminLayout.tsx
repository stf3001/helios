import { type ReactNode, useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, BookOpen, ExternalLink, Flag, HeartPulse, LogOut, MessagesSquare, ShieldCheck, Users2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import MarqueHelios from '../MarqueHelios'

/** Coquille du back-office.
 *
 * ELLE A CHANGÉ DE PARTI PRIS LE 08/10/2026 (demande de Stéphane : « j'aimerais du
 * clair »). Jusque-là elle était volontairement sombre et en police système, pour qu'on
 * sache au premier coup d'œil qu'on n'était plus côté client. Dans les faits ce contraste
 * se payait ailleurs : deux chartes à tenir, des tableaux gris sur gris, et un écran qu'on
 * lit moins bien que le site qu'il supervise. Elle reprend donc l'ivoire, les bordures et
 * les typographies de la marque — ce sont les MÊMES jetons Tailwind que le site public
 * (`sable`, `bord`, `ink`, `primary`), jamais une couleur écrite en dur.
 *
 * Ce qui distingue encore le back-office : une densité plus forte, un bandeau d'en-tête
 * encre, et l'absence totale de l'en-tête et du pied de page publics.
 */

/** La marque EST l'entrée « Tableau de bord » (fusionnées le 08/10/2026) : deux boutons
 *  voisins menant tous les deux à /admin se faisaient concurrence pour rien. */
const NAV = [
  { to: '/admin/conversations', label: 'Conversations', Icon: MessagesSquare },
  { to: '/admin/connaissances', label: 'Connaissances', Icon: BookOpen },
  { to: '/admin/signalements', label: 'Signalements', Icon: Flag },
  { to: '/admin/foyers', label: 'Foyers & RGPD', Icon: ShieldCheck },
  { to: '/admin/partenaires', label: 'Partenaires', Icon: Users2 },
  { to: '/admin/services', label: 'Services', Icon: HeartPulse },
  { to: '/admin/agents', label: 'Agents', Icon: Activity },
]

const LIEN = 'flex items-center gap-2 rounded-xl px-3 py-1.5 transition whitespace-nowrap '
const LIEN_ACTIF = 'bg-white/15 text-white'
const LIEN_INACTIF = 'text-white/65 hover:bg-white/10 hover:text-white'

export default function AdminLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function doLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-sable font-sans text-dark antialiased">
      <header className="sticky top-0 z-40 bg-ink text-white">
        <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-4 px-4">
          {/* Marque et tableau de bord confondus : le soleil ramène à la vue d'ensemble. */}
          <NavLink
            to="/admin"
            end
            title="Tableau de bord"
            className={({ isActive }) =>
              'flex shrink-0 items-center gap-2 rounded-xl px-2 py-1.5 transition '
              + (isActive ? 'bg-white/15' : 'hover:bg-white/10')
            }
          >
            <MarqueHelios taille={22} className="text-sun" />
            <span className="font-display text-lg leading-none">
              HELIOS <span className="text-white/55">back-office</span>
            </span>
          </NavLink>

          <nav className="hidden min-w-0 flex-1 items-center gap-0.5 overflow-x-auto scrollbar-hide text-sm xl:flex">
            {NAV.map(({ to, label, Icon }) => (
              <NavLink key={to} to={to} className={({ isActive }) => LIEN + (isActive ? LIEN_ACTIF : LIEN_INACTIF)}>
                <Icon className="h-4 w-4" /> {label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex shrink-0 items-center gap-3 text-sm">
            <a href="/" className="hidden items-center gap-1.5 text-white/65 hover:text-white sm:flex" title="Ouvrir le site public">
              <ExternalLink className="h-4 w-4" /> Site
            </a>
            <span className="hidden max-w-[16ch] truncate text-white/50 2xl:inline">{user?.email}</span>
            <button onClick={doLogout} className="text-white/65 hover:text-white" title="Se déconnecter">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Sous `xl`, les sept entrées ne tiennent plus sur la ligne de la marque : elles
            passent sur une seconde ligne, qui défile. */}
        <nav className="flex gap-0.5 overflow-x-auto scrollbar-hide px-3 pb-2 text-sm xl:hidden">
          {NAV.map(({ to, label, Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => LIEN + (isActive ? LIEN_ACTIF : LIEN_INACTIF)}>
              <Icon className="h-4 w-4" /> {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-[1400px] px-4 py-6">{children}</main>
    </div>
  )
}

/** Le titre d'une page du back-office : sa phrase d'explication, et ses actions à droite. */
export function TitrePage({
  titre, children, action,
}: { titre: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="max-w-2xl">
        <h1 className="font-display text-3xl text-ink">{titre}</h1>
        {children && <p className="mt-1 text-sm text-dark/70">{children}</p>}
      </div>
      {action && <div className="flex shrink-0 flex-wrap gap-2">{action}</div>}
    </div>
  )
}

/** Carte de statistique — unité de base du tableau de bord. */
export function StatCard({
  label, value, hint, accent,
}: { label: string; value: ReactNode; hint?: ReactNode; accent?: 'ok' | 'warn' | 'bad' }) {
  const accentClass =
    accent === 'bad' ? 'text-primary' : accent === 'warn' ? 'text-terra' : accent === 'ok' ? 'text-leaf' : 'text-ink'
  return (
    <div className="rounded-2xl border border-bord bg-white p-4">
      <div className="text-xs uppercase tracking-wide text-dark/55">{label}</div>
      <div className={'mt-1 font-display text-3xl tabular-nums ' + accentClass}>{value}</div>
      {hint != null && <div className="mt-1 text-xs text-dark/55">{hint}</div>}
    </div>
  )
}

export function Section({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="mt-8">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-dark/55">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

/** Les trois boutons du back-office, écrits une fois pour qu'ils ne divergent pas d'une
 *  page à l'autre. Une ACTION porte le terracotta, comme partout sur le site. */
export const BTN_PRIMAIRE =
  'flex items-center gap-1.5 rounded-xl bg-primary px-3 py-1.5 text-sm font-semibold text-white '
  + 'transition hover:bg-terra disabled:opacity-50'
export const BTN_SECONDAIRE =
  'flex items-center gap-1.5 rounded-xl border border-bord bg-white px-3 py-1.5 text-sm text-ink '
  + 'transition hover:bg-cream disabled:opacity-50'
export const BTN_DANGER =
  'flex items-center gap-1.5 rounded-xl border border-primary/40 bg-white px-3 py-1.5 text-sm text-primary '
  + 'transition hover:bg-primary/10 disabled:opacity-30'

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

/** Les deux états d'attente, écrits une fois : ils se répétaient sur chacune des huit pages. */
export function Attente({ children = 'Chargement…' }: { children?: ReactNode }) {
  return <p className="mt-4 text-sm text-dark/55">{children}</p>
}

export function Erreur({ children }: { children: ReactNode }) {
  return <p className="mt-4 rounded-xl border border-primary/40 bg-primary/5 px-3 py-2 text-sm text-primary">{children}</p>
}
