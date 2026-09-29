import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const links = [
  { to: '/comment-ca-marche', label: 'Qui est Helios' },
  { to: '/helios', label: 'Helios (IA)' },
  { to: '/simulateur-solaire', label: 'La maison de demain' },
  { to: '/le-vent', label: 'Le vent' },
  { to: '/eau', label: 'L’eau' },
  { to: '/la-terre', label: 'La terre' },
  { to: '/faq', label: 'FAQ' },
]

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2">
      <img src="/brand/logo-mark.png" alt="Helios" className="h-9 w-auto" />
      <span className="font-display font-semibold text-xl text-ink">HELIOS</span>
    </Link>
  )
}

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  function close() { setOpen(false) }
  async function doLogout() { await logout(); close(); navigate('/') }

  return (
    <header className="sticky top-0 z-50 bg-cream/90 backdrop-blur border-b border-black/5">
      <div className="max-w-[1200px] mx-auto px-4 h-16 flex items-center justify-between">
        <Logo />

        {/* Desktop */}
        <nav className="hidden lg:flex items-center gap-3 text-[13px] xl:gap-6 xl:text-sm">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} className={({ isActive }) =>
              'whitespace-nowrap ' + (isActive ? 'text-primary font-semibold' : 'text-dark/80 hover:text-primary')
            }>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="hidden lg:flex items-center gap-2 xl:gap-3">
          {user ? (
            <>
              <Link to="/espace/helios" className="text-sm text-dark/80 hover:text-primary">Mon Helios</Link>
              <Link to="/espace" className="px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold hover:opacity-90">Mon espace</Link>
              <button onClick={doLogout} className="text-sm text-gray-500 hover:text-primary">Déconnexion</button>
            </>
          ) : (
            <>
              <Link to="/connexion" className="text-sm text-dark/80 hover:text-primary">Connexion</Link>
              <Link to="/inscription" className="px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold hover:opacity-90">Mon espace</Link>
            </>
          )}
        </div>

        {/* Burger mobile */}
        <button className="lg:hidden p-2 -mr-2 text-ink" onClick={() => setOpen((v) => !v)} aria-label="Menu">
          {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Panneau mobile */}
      {open && (
        <div className="lg:hidden border-t border-black/5 bg-cream animate-slide-up">
          <nav className="px-4 py-3 flex flex-col">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} onClick={close} className={({ isActive }) =>
                'py-2.5 text-[15px] ' + (isActive ? 'text-primary font-semibold' : 'text-dark/80')
              }>
                {l.label}
              </NavLink>
            ))}
            <div className="h-px bg-black/5 my-2" />
            {user ? (
              <>
                <Link to="/espace/helios" onClick={close} className="py-2.5 text-[15px] text-dark/80">Mon Helios</Link>
                <Link to="/espace" onClick={close} className="mt-1 rounded-xl bg-primary text-white text-center text-sm font-semibold px-4 py-2.5">Mon espace</Link>
                <button onClick={doLogout} className="py-2.5 mt-1 text-[15px] text-gray-500 text-left">Déconnexion</button>
              </>
            ) : (
              <>
                <Link to="/connexion" onClick={close} className="py-2.5 text-[15px] text-dark/80">Connexion</Link>
                <Link to="/inscription" onClick={close} className="mt-1 rounded-xl bg-primary text-white text-center text-sm font-semibold px-4 py-2.5">Créer mon espace</Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
