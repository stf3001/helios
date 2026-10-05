import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Home, Menu, X } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import MarqueHelios from '../MarqueHelios'

/** Le menu, en deux moitiés, avec « La maison de demain » au milieu (demande de
 *  Stéphane, 05/10/2026).
 *
 *  L'ordre n'est pas décoratif : à gauche ce que la maison REÇOIT — le soleil, le
 *  vent, l'eau, la terre —, au milieu l'outil qui les assemble, à droite ce qu'elle
 *  ACHÈTE et le reste. L'outil est la charnière, et il est à sa place.
 *
 *  Les quatre éléments restent groupés : ils forment une famille, et les séparer
 *  pour gagner un pixel de centrage aurait coûté plus que ça ne rapporte.
 *
 *  « Le soleil » a été ajouté le 05/10/2026. Son adresse est `/solaire` et non
 *  `/le-soleil` — voir le commentaire de route dans `App.tsx`. */
const AVANT = [
  { to: '/solaire', label: 'Le soleil' },
  { to: '/le-vent', label: 'Le vent' },
  { to: '/eau', label: 'L’eau' },
  { to: '/la-terre', label: 'La terre' },
]

const PHARE = { to: '/simulateur-solaire', label: 'La maison de demain' }

const APRES = [
  { to: '/achat-energie', label: 'L’achat d’énergie' },
  { to: '/helios', label: 'Qui est Helios' },
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

/** UNE SEULE PORTE VERS L'ESPACE (demande de Stephane, 05/10/2026).
 *
 *  « Connexion » et « Creer mon espace » cote a cote, c'etait deux portes pour la
 *  meme chose, et il fallait deviner laquelle etait la sienne. Il n'en reste qu'une,
 *  « Mon espace », qui pointe toujours vers `/espace` : un visiteur deconnecte y est
 *  renvoye vers la connexion par `ProtectedRoute`, et la page de connexion porte deja
 *  son lien « Pas encore de compte ? Creer un compte ». Le parcours d'inscription
 *  n'est donc pas perdu — il est juste derriere la bonne porte au lieu d'etre a cote.
 *
 *  Effet de bord utile : l'en-tete y gagne la place qu'il fallait pour mettre
 *  « La maison de demain » en valeur sans deborder a 1024 px. */
const LIEN_ESPACE = '/espace'

/** Le lien phare. Il ne porte PAS d'aplat plein : l'en-tete n'a qu'un seul bouton
 *  plein, « Mon espace », et deux aplats cote a cote ne designeraient plus rien. Un
 *  contour terracotta et un fond tres pale suffisent a le detacher d'une ligne de
 *  liens en texte — c'est le meme procede que les cartes du site, qui se detachent
 *  par leur bordure et non par une ombre. */
function LienPhare({ onClick, mobile = false }: { onClick?: () => void; mobile?: boolean }) {
  return (
    <NavLink
      to={PHARE.to}
      onClick={onClick}
      className={({ isActive }) =>
        'inline-flex items-center gap-1.5 whitespace-nowrap rounded-xl border font-semibold '
        + 'transition-colors ' + (mobile ? 'my-1 px-3 py-2.5 text-[15px]' : 'px-3 py-1.5')
        + (isActive
          ? ' border-primary bg-primary/10 text-primary'
          : ' border-primary/35 bg-primary/5 text-primary hover:border-primary hover:bg-primary/10')
      }
    >
      <Home className="h-4 w-4 shrink-0" aria-hidden="true" />
      {PHARE.label}
    </NavLink>
  )
}

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

  const lien = ({ isActive }: { isActive: boolean }) =>
    'whitespace-nowrap transition-colors '
    + (isActive ? 'text-primary font-semibold' : 'text-gray-600 hover:text-ink')

  return (
    <header className="sticky top-0 z-50 bg-sable/90 backdrop-blur border-b border-bord">
      <div className="max-w-[1200px] mx-auto px-4 h-16 flex items-center justify-between gap-4">
        <Logo />

        {/* Desktop. `flex-1 justify-center` centre la barre dans le bandeau plutot que
            de la laisser flotter contre le bloc de droite : c'est ce qui donne au lien
            phare sa position centrale, et non un comptage d'entrees. */}
        <nav aria-label="Navigation principale"
          className="hidden lg:flex flex-1 items-center justify-center gap-4 text-[13px] xl:gap-6 xl:text-sm">
          {AVANT.map((l) => (
            <NavLink key={l.to} to={l.to} className={lien}>{l.label}</NavLink>
          ))}
          <LienPhare />
          {APRES.map((l) => (
            <NavLink key={l.to} to={l.to} className={lien}>{l.label}</NavLink>
          ))}
        </nav>

        <div className="hidden lg:flex items-center gap-4 shrink-0">
          <Link to={LIEN_ESPACE} className={boutonPlein}>Mon espace</Link>
          {user && (
            <button onClick={doLogout} className="text-sm text-gray-500 hover:text-ink">Déconnexion</button>
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

      {/* Panneau mobile. Le lien phare garde son traitement : sur un telephone, une
          liste de huit lignes identiques ne dit pas par ou commencer. */}
      {open && (
        <div id="menu-principal" className="lg:hidden border-t border-bord bg-sable animate-slide-up">
          <nav aria-label="Navigation principale" className="px-4 py-3 flex flex-col">
            {AVANT.map((l) => (
              <NavLink key={l.to} to={l.to} onClick={close} className={({ isActive }) =>
                'py-2.5 text-[15px] ' + (isActive ? 'text-primary font-semibold' : 'text-gray-600')
              }>
                {l.label}
              </NavLink>
            ))}
            <LienPhare onClick={close} mobile />
            {APRES.map((l) => (
              <NavLink key={l.to} to={l.to} onClick={close} className={({ isActive }) =>
                'py-2.5 text-[15px] ' + (isActive ? 'text-primary font-semibold' : 'text-gray-600')
              }>
                {l.label}
              </NavLink>
            ))}
            <div className="h-px bg-bord my-2" />
            <Link to={LIEN_ESPACE} onClick={close} className={boutonPlein + ' mt-1'}>Mon espace</Link>
            {user && (
              <button onClick={doLogout} className="py-2.5 mt-1 text-[15px] text-gray-500 text-left">
                Déconnexion
              </button>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
