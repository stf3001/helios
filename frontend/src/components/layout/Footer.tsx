import { Link } from 'react-router-dom'

const ressources = [
  { to: '/comment-ca-marche', label: 'Comment ça marche' },
  { to: '/engagements', label: 'Nos engagements' },
  { to: '/eau', label: "L'eau atmosphérique" },
  { to: '/guides', label: 'Guides & Aides' },
  { to: '/glossaire', label: 'Glossaire' },
  { to: '/faq', label: 'FAQ' },
  { to: '/partenaires', label: 'Partenaires' },
  { to: '/devenir-partenaire', label: 'Devenir partenaire' },
]

export default function Footer() {
  return (
    <footer className="bg-ink text-white/80 mt-16">
      <div className="max-w-[1200px] mx-auto px-4 py-10 grid gap-8 md:grid-cols-4 text-sm">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <img src="/brand/logo-mark.png" alt="" className="h-7 w-auto" />
            <p className="font-display font-bold text-white text-lg">HELIOS</p>
          </div>
          <p>Diagnostic énergétique assisté par IA. Gratuit, indépendant, à votre rythme.</p>
        </div>
        <div>
          <p className="font-semibold text-white mb-2">Ressources</p>
          <ul className="space-y-1.5">
            {ressources.map((r) => (
              <li key={r.to}><Link to={r.to} className="hover:text-white">{r.label}</Link></li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-white mb-2">Transparence</p>
          <p>HELIOS est gratuit pour vous, toujours. La plateforme se rémunère par une commission versée
             par les entreprises partenaires — jamais par le client. Les conseils d'Helios sont indépendants.</p>
          <p className="mt-2"><Link to="/engagements" className="underline hover:text-white">Tous nos engagements →</Link></p>
        </div>
        <div>
          <p className="font-semibold text-white mb-2">« Je le sais, mais je fais ma part. »</p>
          <p>L'esprit colibri guide chacun de nos conseils : aucun geste n'est trop petit.</p>
        </div>
      </div>
      <div className="border-t border-gray-700 py-4 text-center text-xs text-gray-500">
        © 2026 HELIOS — Mentions légales · CGU · Confidentialité (à venir)
      </div>
    </footer>
  )
}
