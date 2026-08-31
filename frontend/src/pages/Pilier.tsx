import { Link, useLocation } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useTitle } from '../hooks/useTitle'
import piliers from '../data/piliers.json'

/** Page chapeau d'un domaine : un texte de fond écrit à la main, puis toutes les fiches
 *  du groupe. Le contenu vit dans `data/piliers.json` — même source que le pré-rendu,
 *  ce qui garantit que la version servie aux moteurs dit la même chose que la page. */
export default function Pilier() {
  const { pathname } = useLocation()
  const pilier = piliers.find((p) => `/${p.slug}` === pathname)

  useTitle(pilier?.titre)

  if (!pilier) {
    return (
      <section className="max-w-[720px] mx-auto px-4 py-16 text-center text-gray-600">
        Page introuvable. <Link to="/" className="text-primary underline">Retour à l'accueil</Link>
      </section>
    )
  }

  return (
    <>
      <Hero title={pilier.titre} subtitle={pilier.sousTitre} />

      <section className="max-w-[900px] mx-auto px-4 py-12">
        <p className="text-lg text-gray-700 leading-relaxed max-w-[68ch]">{pilier.intro}</p>
      </section>

      <section className="max-w-[900px] mx-auto px-4 pb-12 space-y-8">
        {pilier.sections.map((s) => (
          <div key={s.titre}>
            <h2 className="text-xl font-semibold text-ink mb-2">{s.titre}</h2>
            <p className="text-gray-700 leading-relaxed max-w-[68ch]">{s.contenu}</p>
          </div>
        ))}
      </section>

      <section className="max-w-[900px] mx-auto px-4 pb-12">
        <div className="rounded-2xl bg-cream border border-black/5 p-6 flex flex-wrap gap-3">
          {pilier.liens.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="inline-flex items-center gap-2 rounded-xl bg-primary text-white font-semibold px-4 py-2.5 hover:opacity-90"
            >
              {l.label} <ArrowRight className="w-4 h-4" />
            </Link>
          ))}
        </div>
      </section>

      <FichesLiees cats={pilier.cats} />
    </>
  )
}
