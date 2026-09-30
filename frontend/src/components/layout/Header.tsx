import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import MarqueHelios from '../MarqueHelios'

const links = [
  { to: '/helios', label: 'Qui est Helios' },
  { to: '/simulateur-solaire', label: 'La maison de demain' },
  { to: '/le-vent', label: 'Le vent' },
  { to: '/eau', label: 'L’eau' },
  { to: '/la-terre', label: 'La terre' },
  { to: '/achat-energie', label: 'L’achat d’énergie' },
  { to: '/faq', label: 'FAQ' },
]

function Logo({ onClick }: { onClick?: () => void }) {
  return (
    <Link to="/" onClick={onClick} className="flex items-center gap-2.5 shrink-0" aria-label="Helios, accueil">
      <MarqueHelios taille={26} className="text-primary" />
      <span className="font-display text-2xl text-ink leading-none">Helios</span>
    </Link>
  )
}

/** Le bouton plein de l'en-tete : encre, pas terracotta. Le terracotta est
 *  l'accent du contenu (la question posee a Helios) ; si l'en-tete le portait
 *  aussi, les deux se disputeraient l'oeil sur l'accueil. */
const boutonPlein =
  'inline-flex items-center justify-center rounded-xl bg-ink text-sable text-sm font-semibold px-4 py-2 hover:bg-ink/90 transition-colors'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)

  function close() { setOpen(false) }
  async function doLogout() { await logout(); close(); navigate('/') }

  // Le panneau mobile se referme au changement de page : sans cela il restait
  // ouvert par-dessus la page qu'on venait de demander.
  useEffect(() => { setOpen(false) }, [pathname])

  return (
    <header className="sticky top-0 z-50 bg-sable/90 backdrop-blur border-b border-bord">
      <div className="max-w-[1200px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Logo />

        {/* Desktop */}
        <nav aria-label="Navigation principale" className="hidden lg:flex items-center gap-4 text-[13px] xl:gap-7 xl:text-sm">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} className={({ isActive }) =>
              'whitespace-nowrap transition-colors ' +
              (isActive ? 'text-primary font-semibold' : 'text-gray-600 hover:text-ink')
            }>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden lg:flex items-center gap-4 shrink-0">
          {user ? (
            <>
              <Link to="/espace" className={boutonPlein}>Mon espace</Link>
              <button onClick={doLogout} className="text-sm text-gray-500 hover:text-ink">Déconnexion</button>
            </>
          ) : (
            <>
              <Link to="/connexion" className="text-sm text-gray-600 hover:text-ink">Connexion</Link>
              <Link to="/inscription" className={boutonPlein}>Mon espace</Link>
            </>
          )}
        </div>

        {/* Burger mobile */}
        <button
          type="button"
          className="lg:hidden -mr-2 p-2 text-ink rounded-xl hover:bg-cream"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="menu-principal"
          aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'}
        >
          {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Panneau mobile */}
      {open && (
        <div id="menu-principal" className="lg:hidden border-t border-bord bg-sable animate-slide-up">
          <nav aria-label="Navigation principale" className="px-4 py-3 flex flex-col">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} onClick={close} className={({ isActive }) =>
                'py-2.5 text-[15px] ' + (isActive ? 'text-primary font-semibold' : 'text-gray-600')
              }>
                {l.label}
              </NavLink>
            ))}
            <div className="h-px bg-bord my-2" />
            {user ? (
              <>
                <Link to="/espace" onClick={close} className={boutonPlein + ' mt-1'}>Mon espace</Link>
                <button onClick={doLogout} className="py-2.5 mt-1 text-[15px] text-gray-500 text-left">Déconnexion</button>
              </>
            ) : (
              <>
                <Link to="/connexion" onClick={close} className="py-2.5 text-[15px] text-gray-600">Connexion</Link>
                <Link to="/inscription" onClick={close} className={boutonPlein + ' mt-1'}>Mon espace</Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
