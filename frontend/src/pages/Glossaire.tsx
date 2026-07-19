import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Hero from '../components/Hero'
import { glossaire } from '../data/glossaire'
import { useTitle } from '../hooks/useTitle'

export default function Glossaire() {
  useTitle('Glossaire')
  const [q, setQ] = useState('')

  const list = useMemo(() => {
    const s = q.trim().toLowerCase()
    const sorted = [...glossaire].sort((a, b) => a.terme.localeCompare(b.terme, 'fr'))
    if (!s) return sorted
    return sorted.filter((t) => t.terme.toLowerCase().includes(s) || t.definition.toLowerCase().includes(s))
  }, [q])

  return (
    <>
      <Hero title="Glossaire" subtitle="Tous les mots de l'énergie, expliqués sans jargon." />
      <section className="max-w-[760px] mx-auto px-4 py-12">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Rechercher un terme (DPE, kWc, pompe à chaleur…)"
          className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm mb-8"
        />

        <dl className="space-y-5">
          {list.map((t) => (
            <div key={t.terme} className="border-b border-gray-100 pb-5">
              <dt className="font-display font-semibold text-ink text-lg">{t.terme}</dt>
              <dd className="text-gray-700 mt-1 leading-relaxed">{t.definition}</dd>
            </div>
          ))}
          {list.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              Aucun terme trouvé — posez votre question à{' '}
              <Link to="/helios" className="text-primary underline">Helios</Link>.
            </p>
          )}
        </dl>
      </section>
    </>
  )
}
