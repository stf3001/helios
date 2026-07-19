import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { guides } from '../data/guides'
import { useTitle } from '../hooks/useTitle'

export default function GuideDetail() {
  const { slug } = useParams()
  const guide = guides.find((g) => g.slug === slug)
  useTitle(guide?.titre)

  if (!guide) {
    return (
      <section className="max-w-[700px] mx-auto px-4 py-16 text-center">
        <p className="text-gray-500">Guide introuvable.</p>
        <Link to="/guides" className="text-primary underline">Retour aux guides</Link>
      </section>
    )
  }

  return (
    <article className="max-w-[720px] mx-auto px-4 py-12">
      <Link to="/guides" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary mb-6">
        <ArrowLeft className="w-4 h-4" /> Tous les guides
      </Link>
      <div className="text-xs text-primary font-semibold uppercase mb-2">{guide.categorie}</div>
      <h1 className="text-3xl font-bold leading-tight mb-3">{guide.titre}</h1>
      <p className="text-lg text-gray-600 mb-8">{guide.chapo}</p>

      {guide.aVenir && (
        <div className="border-l-4 border-sun bg-sun/10 rounded-r-xl p-4 text-sm text-gray-700 mb-8">
          Ce guide est en cours de rédaction. En attendant, Helios répond à vos questions dans le{' '}
          <Link to="/helios" className="text-primary underline">chat</Link>.
        </div>
      )}

      <div className="space-y-8">
        {guide.sections.map((s, i) => (
          <section key={i}>
            <h2 className="text-xl font-semibold text-ink mb-2">{s.titre}</h2>
            <p className="text-gray-700 whitespace-pre-line leading-relaxed">{s.contenu}</p>
          </section>
        ))}
      </div>

      <div className="mt-12 border-t border-gray-100 pt-6 text-sm text-gray-500">
        Les montants d'aides et les prix évoluent : Helios les vérifie dans sa base à jour.{' '}
        <Link to="/helios" className="text-primary underline">Demandez à Helios</Link> pour votre cas précis.
      </div>
    </article>
  )
}
