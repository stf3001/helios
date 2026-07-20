import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Hero from '../components/Hero'
import { ChevronDown } from 'lucide-react'
import { useTitle } from '../hooks/useTitle'
import ApiError from '../components/ApiError'

interface FaqEntry {
  question: string
  answer: string
  cat: string | null
  tags: string[]
}

export default function Faq() {
  useTitle('Questions fréquentes')
  // ?q= : arrivée depuis une citation du chat → recherche préremplie + fiche ouverte.
  const [searchParams] = useSearchParams()
  const initialQuery = searchParams.get('q') ?? ''
  const [entries, setEntries] = useState<FaqEntry[]>([])
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)
  const [open, setOpen] = useState<number | null>(initialQuery ? 0 : null)
  const [query, setQuery] = useState(initialQuery)
  const [cat, setCat] = useState<string | null>(null)

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

  const categories = useMemo(
    () => Array.from(new Set(entries.map((e) => e.cat).filter(Boolean))).sort() as string[],
    [entries],
  )

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return entries.filter((e) => {
      if (cat && e.cat !== cat) return false
      if (!q) return true
      return (
        e.question.toLowerCase().includes(q) ||
        e.answer.toLowerCase().includes(q) ||
        e.tags.some((t) => t.toLowerCase().includes(q))
      )
    })
  }, [entries, query, cat])

  return (
    <>
      <Hero title="Questions fréquentes" subtitle="Les réponses d'Helios, tirées de sa base de connaissances." />
      <section className="max-w-[800px] mx-auto px-4 py-12">
        {/* Recherche + filtres */}
        <div className="mb-6 space-y-3">
          <input
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(null) }}
            placeholder="Rechercher une question, un mot-clé…"
            className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm"
          />
          {categories.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => { setCat(null); setOpen(null) }}
                className={'text-xs px-3 py-1 rounded-full border ' +
                  (cat === null ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-600')}
              >
                Toutes
              </button>
              {categories.map((c) => (
                <button
                  key={c}
                  onClick={() => { setCat(c); setOpen(null) }}
                  className={'text-xs px-3 py-1 rounded-full border capitalize ' +
                    (cat === c ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-600')}
                >
                  {c.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          )}
        </div>

        {!loaded ? (
          <p className="text-gray-400">Chargement…</p>
        ) : error ? (
          <ApiError retry={load} />
        ) : (
          <>
            <p className="text-xs text-gray-400 mb-3">
              {filtered.length} question{filtered.length > 1 ? 's' : ''}
              {entries.length > 0 && ` sur ${entries.length}`}
            </p>
            <div className="space-y-3">
              {filtered.map((e, i) => (
                <div key={e.question} className="bg-gray-50 rounded-2xl">
                  <button
                    className="w-full flex items-center justify-between p-4 text-left font-semibold"
                    onClick={() => setOpen(open === i ? null : i)}
                  >
                    <span>
                      {e.cat && <span className="text-primary text-xs mr-2 uppercase">{e.cat.replace(/_/g, ' ')}</span>}
                      {e.question}
                    </span>
                    <ChevronDown className={`w-5 h-5 shrink-0 transition-transform ${open === i ? 'rotate-180' : ''}`} />
                  </button>
                  {open === i && <p className="px-4 pb-4 text-gray-700 whitespace-pre-line">{e.answer}</p>}
                </div>
              ))}
              {filtered.length === 0 && (
                <p className="text-gray-500 text-center py-8">Aucune question ne correspond — essayez le chat Helios.</p>
              )}
            </div>
          </>
        )}
      </section>
    </>
  )
}
