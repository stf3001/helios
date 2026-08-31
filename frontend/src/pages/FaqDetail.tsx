import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, MessageSquare } from 'lucide-react'
import ApiError from '../components/ApiError'
import { getCategoryIcon } from '../data/categoryIcons'
import { faqSlug } from '../lib/faqSlug'
import piliers from '../data/piliers.json'
import { useTitle } from '../hooks/useTitle'

interface FaqEntry {
  question: string
  answer: string
  cat: string | null
  tags: string[]
}

/** Page d'une fiche. Son HTML est aussi généré au build (scripts/prerender.mjs) : c'est cette
 *  version statique que voient les moteurs de recherche, celle-ci prend le relais ensuite. */
export default function FaqDetail() {
  const { slug } = useParams()
  const [entries, setEntries] = useState<FaqEntry[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  const load = useCallback(() => {
    setLoaded(false)
    setError(false)
    fetch('/api/faq')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setEntries)
      .catch(() => setError(true))
      .finally(() => setLoaded(true))
  }, [])
  useEffect(load, [load])

  const fiche = useMemo(
    () => entries.find((e) => faqSlug(e.question) === slug),
    [entries, slug],
  )

  // Fiches de la même catégorie — maillage interne : il aide autant le lecteur que le référencement.
  const voisines = useMemo(
    () =>
      fiche
        ? entries.filter((e) => e.cat === fiche.cat && e.question !== fiche.question).slice(0, 5)
        : [],
    [entries, fiche],
  )

  useTitle(fiche?.question)

  if (error) {
    return (
      <section className="max-w-[720px] mx-auto px-4 py-12">
        <ApiError retry={load} />
      </section>
    )
  }

  if (!loaded) {
    return <section className="max-w-[720px] mx-auto px-4 py-16 text-gray-400">Chargement…</section>
  }

  if (!fiche) {
    return (
      <section className="max-w-[720px] mx-auto px-4 py-16 text-center">
        <p className="text-gray-600">Cette question n'existe pas ou a été renommée.</p>
        <Link to="/faq" className="text-primary underline mt-3 inline-block">
          Voir toutes les questions
        </Link>
      </section>
    )
  }

  const { Icon, color } = getCategoryIcon(fiche.cat)
  // Page chapeau du sujet : le lien retour ferme la boucle du maillage interne
  // (chapeau -> fiches -> chapeau), ce qui signale un domaine traité en profondeur.
  const pilier = piliers.find((p) => fiche.cat && p.cats.includes(fiche.cat))

  return (
    <article className="max-w-[720px] mx-auto px-4 py-12">
      <Link to="/faq" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary mb-6">
        <ArrowLeft className="w-4 h-4" /> Questions fréquentes
      </Link>

      <div className={'inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gray-50 mb-4 ' + color}>
        <Icon className="w-6 h-6" />
      </div>
      {fiche.cat && (
        <div className={'text-xs font-semibold uppercase mb-2 ' + color}>{fiche.cat.replace(/_/g, ' ')}</div>
      )}

      <h1 className="text-3xl font-bold leading-tight mb-5">{fiche.question}</h1>
      {pilier && (
        <p className="-mt-3 mb-5 text-sm text-gray-500">
          Sujet :{' '}
          <Link to={`/${pilier.slug}`} className="text-primary underline underline-offset-2">
            {pilier.titre}
          </Link>
        </p>
      )}
      <p className="text-gray-700 whitespace-pre-line leading-relaxed text-lg">{fiche.answer}</p>

      <div className="mt-8 rounded-2xl bg-cream border border-black/5 p-5">
        <p className="text-sm text-gray-700">
          Cette réponse est générale. Pour savoir ce qu'elle donne <strong>chez vous</strong>,
          posez la question à Helios avec les données de votre logement.
        </p>
        <Link
          to={`/helios?q=${encodeURIComponent(fiche.question)}`}
          className="inline-flex items-center gap-2 mt-3 rounded-xl bg-primary text-white font-semibold px-4 py-2.5 hover:opacity-90"
        >
          <MessageSquare className="w-4 h-4" /> Poser la question à Helios
        </Link>
      </div>

      {voisines.length > 0 && (
        <section className="mt-10 border-t border-gray-100 pt-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
            Sur le même sujet
          </h2>
          <ul className="space-y-2">
            {voisines.map((v) => (
              <li key={v.question}>
                <Link to={`/faq/${faqSlug(v.question)}`} className="text-ink hover:text-primary underline-offset-2 hover:underline">
                  {v.question}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  )
}
