import { Link } from 'react-router-dom'

/** Invitation à agir réutilisable en fin de page (Vision, Colibri, Qui sommes-nous…). */
export default function CtaFaisTaPart({ compact = false }: { compact?: boolean }) {
  return (
    <section className={compact ? 'max-w-[820px] mx-auto px-4 py-12 text-center' : 'bg-cream py-16'}>
      <div className={compact ? '' : 'max-w-[820px] mx-auto px-4 text-center'}>
        <p className="font-display text-2xl md:text-3xl font-semibold text-ink mb-3">Prêt à faire votre part ?</p>
        <p className="text-gray-700 max-w-xl mx-auto mb-6">
          Un geste à la fois : parlez à Helios, ou commencez votre fiche maison — c'est gratuit,
          et ça ne prend que quelques minutes.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link to="/helios" className="rounded-xl bg-primary text-white font-semibold px-6 py-3 hover:opacity-90">
            Parler à Helios
          </Link>
          <Link to="/inscription" className="rounded-xl border border-gray-300 text-ink font-semibold px-6 py-3 hover:bg-white">
            Créer ma fiche maison
          </Link>
        </div>
      </div>
    </section>
  )
}
