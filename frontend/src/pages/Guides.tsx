import { useState } from 'react'
import { Link } from 'react-router-dom'
import Hero from '../components/Hero'
import { guides, guideCategories } from '../data/guides'
import { getCategoryIcon } from '../data/categoryIcons'
import { useTitle } from '../hooks/useTitle'

export default function Guides() {
  useTitle('Guides')
  const [cat, setCat] = useState<string | null>(null)
  const list = cat ? guides.filter((g) => g.categorie === cat) : guides

  return (
    <>
      <Hero title="Guides" subtitle="Par où commencer, et dans quel ordre. Le détail de chaque sujet est dans la FAQ." />
      <section className="max-w-[1000px] mx-auto px-4 py-12">
        <div className="flex flex-wrap gap-2 mb-8">
          <button onClick={() => setCat(null)}
            className={'text-sm px-3 py-1.5 rounded-full border ' + (cat === null ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-600')}>
            Tous les guides
          </button>
          {guideCategories.map((c) => {
            const { Icon } = getCategoryIcon(c)
            return (
              <button key={c} onClick={() => setCat(c)}
                className={'flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-full border ' + (cat === c ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-600')}>
                <Icon className="w-3.5 h-3.5" /> {c}
              </button>
            )
          })}
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          {list.map((g) => {
            const { Icon, color } = getCategoryIcon(g.categorie)
            return (
              <Link key={g.slug} to={`/guides/${g.slug}`}
                className="group border border-gray-200 rounded-2xl p-6 hover:border-primary hover:shadow-sm transition bg-white">
                <div className={'flex items-center gap-2 text-xs font-semibold mb-2 ' + color}>
                  <Icon className="w-4 h-4" /> {g.categorie}
                  {g.aVenir && <span className="text-gray-400 font-normal">· bientôt</span>}
                </div>
                <h2 className="font-display font-semibold text-lg text-ink leading-snug group-hover:text-primary">{g.titre}</h2>
                <p className="text-sm text-gray-600 mt-2">{g.chapo}</p>
              </Link>
            )
          })}
        </div>

        <p className="text-center text-xs text-gray-400 mt-10">
          Une question qui n'a pas son guide ? Posez-la directement à{' '}
          <Link to="/helios" className="text-primary underline">Helios</Link>.
        </p>
      </section>
    </>
  )
}
