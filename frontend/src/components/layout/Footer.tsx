import { Link } from 'react-router-dom'
import piliers from '../../data/piliers.json'
import MarqueHelios from '../MarqueHelios'

const ressources = [
  { to: '/qui-sommes-nous', label: 'Qui sommes-nous' },
  { to: '/vision', label: 'Notre vision' },
  { to: '/colibri', label: "L'esprit colibri" },
  { to: '/helios', label: 'Qui est Helios' },
  { to: '/engagements', label: 'Nos engagements' },
  { to: '/eau', label: "L'eau atmosphérique" },
  { to: '/la-terre', label: 'Cultiver sa terre' },
  { to: '/glossaire', label: 'Glossaire' },
  { to: '/faq', label: 'FAQ' },
  { to: '/partenaires', label: 'Partenaires' },
  { to: '/devenir-partenaire', label: 'Devenir partenaire' },
]

/** Sur l'encre, le texte courant est l'ivoire attenue et le survol le remet plein :
 *  un seul mecanisme de survol pour toutes les colonnes. */
const lien = 'text-sable/70 hover:text-sable transition-colors'

export default function Footer() {
  return (
    <footer className="bg-ink text-sable/70">
      <div className="max-w-[1200px] mx-auto px-4 py-12 grid gap-8 md:grid-cols-5 text-sm">
        <div>
          <div className="flex items-center gap-2.5 mb-3">
            <MarqueHelios taille={24} className="text-sun" />
            <p className="font-display text-xl text-sable leading-none">Helios</p>
          </div>
          <p>Le carnet de votre maison, tenu avec vous. Gratuit, indépendant, à votre rythme.</p>
        </div>
        <div>
          <p className="font-semibold text-sable mb-3">Sujets</p>
          <ul className="space-y-1.5">
            {piliers.map((s) => (
              <li key={s.slug}><Link to={`/${s.slug}`} className={lien}>{s.titre}</Link></li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-sable mb-3">Ressources</p>
          <ul className="space-y-1.5">
            {ressources.map((r) => (
              <li key={r.to}><Link to={r.to} className={lien}>{r.label}</Link></li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-sable mb-3">Transparence</p>
          <p>HELIOS est gratuit pour vous, toujours. La plateforme se rémunère par une commission versée
             par les entreprises partenaires — jamais par le client. Les conseils d'Helios sont indépendants.</p>
          <p className="mt-2"><Link to="/engagements" className={'underline underline-offset-2 ' + lien}>Tous nos engagements →</Link></p>
        </div>
        <div>
          <p className="font-display text-lg text-sable mb-2 leading-snug">« Je le sais, mais je fais ma part. »</p>
          <p>L'esprit colibri guide chacun de nos conseils : aucun geste n'est trop petit.</p>
        </div>
      </div>
      <div className="border-t border-sable/10 py-4 text-center text-xs text-sable/50">
        © 2026 HELIOS — Mentions légales · CGU · Confidentialité (à venir)
      </div>
    </footer>
  )
}
