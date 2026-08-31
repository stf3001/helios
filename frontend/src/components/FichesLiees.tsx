import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { getCategoryIcon } from '../data/categoryIcons'
import { faqSlug } from '../lib/faqSlug'

interface FaqEntry {
  question: string
  answer: string
  cat: string | null
  tags: string[]
}

/**
 * Liste les fiches d'un groupe thématique. Composant réutilisable : il sert aux pages
 * chapeau génériques (`Pilier.tsx`) comme aux pages sur mesure (`/eau`), sans imposer
 * de gabarit à ces dernières.
 *
 * Rôle SEO : c'est ce maillage qui relie une page chapeau à ses fiches détaillées et
 * signale à un moteur de recherche qu'il s'agit d'un domaine traité en profondeur,
 * plutôt que de pages isolées.
 */
export default function FichesLiees({
  cats,
  titre = 'Toutes les questions sur ce sujet',
}: {
  cats: string[]
  titre?: string
}) {
  const [fiches, setFiches] = useState<FaqEntry[]>([])

  useEffect(() => {
    let annule = false
    fetch('/api/faq')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: FaqEntry[]) => {
        if (annule) return
        setFiches(d.filter((f) => f.cat && cats.includes(f.cat)))
      })
      .catch(() => { /* silencieux : l'absence de cette liste ne doit pas casser la page */ })
    return () => { annule = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cats.join(',')])

  if (fiches.length === 0) return null

  return (
    <section className="max-w-[900px] mx-auto px-4 pb-16">
      <h2 className="text-2xl font-bold mb-1">{titre}</h2>
      <p className="text-sm text-gray-500 mb-6">
        {fiches.length} réponses détaillées, tirées de la base de connaissances d'Helios.
      </p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {fiches.map((f) => {
          const { Icon, color } = getCategoryIcon(f.cat)
          return (
            <li key={f.question}>
              <Link
                to={`/faq/${faqSlug(f.question)}`}
                className="group flex items-start gap-2.5 rounded-xl border border-gray-200 p-3 hover:border-primary transition h-full"
              >
                <Icon className={'w-4 h-4 shrink-0 mt-0.5 ' + color} />
                <span className="text-sm text-ink group-hover:text-primary">{f.question}</span>
              </Link>
            </li>
          )
        })}
      </ul>
      <Link
        to="/faq"
        className="inline-flex items-center gap-1.5 text-primary font-semibold mt-5 hover:gap-2.5 transition-all"
      >
        Voir toutes les questions <ArrowRight className="w-4 h-4" />
      </Link>
    </section>
  )
}
