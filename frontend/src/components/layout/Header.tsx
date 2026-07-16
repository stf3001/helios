import { Link, NavLink } from 'react-router-dom'
import { Sun } from 'lucide-react'

const links = [
  { to: '/comment-ca-marche', label: 'Comment ça marche' },
  { to: '/helios', label: 'Helios (IA)' },
  { to: '/vision', label: 'Vision' },
  { to: '/partenaires', label: 'Partenaires' },
  { to: '/faq', label: 'FAQ' },
]

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-100">
      <div className="max-w-[1200px] mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <Sun className="w-7 h-7 text-primary" /> HELIOS
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} className={({ isActive }) =>
              isActive ? 'text-primary font-semibold' : 'text-gray-700 hover:text-primary'
            }>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <span className="px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold opacity-60 cursor-not-allowed"
              title="Espace client — jalon 2">
          Mon espace (bientôt)
        </span>
      </div>
    </header>
  )
}
