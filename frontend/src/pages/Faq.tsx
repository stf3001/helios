import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Hero from '../components/Hero'
import { ArrowLeft, ArrowRight, ChevronDown, Search } from 'lucide-react'
import { useTitle } from '../hooks/useTitle'
import ApiError from '../components/ApiError'
import { getCategoryIcon, libelleCategorie } from '../data/categoryIcons'
import { faqSlug } from '../lib/faqSlug'

/** Recherche insensible aux accents : en francais on tape « eolienne » et on
 *  attend « éolienne ». `NFD` separe la lettre de son signe diacritique, que
 *  l'on retire ensuite. Sans cela, la recherche rendait zero resultat sur douze
 *  fiches — et c'est elle qui sert a sortir d'un theme. */
function sansAccents(texte: string): string {
  return texte.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

interface FaqEntry {
  question: string
  answer: string
  cat: string | null
  tags: string[]
}

/**
 * LA PAGE NE DEROULE JAMAIS TOUTE LA BASE.
 *
 * Jusqu'au 30/09/2026, l'etat d'arrivee (« Toutes ») empilait les 357 fiches en
 * accordeons : un mur que personne ne parcourt. On choisit d'abord un theme, et
 * seules ses questions se deroulent.
 *
 * LA RECHERCHE, ELLE, RESTE GLOBALE tant qu'aucun theme n'est choisi — c'est par
 * la qu'arrivent les citations du chat (`/faq?q=<titre>`), qui ne connaissent pas
 * le theme de la fiche qu'elles visent. Supprimer purement le « tout » aurait
 * casse ce parcours.
 */
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

  const themes = useMemo(() => {
    const noms = new Set<string>()
    for (const e of entries) if (e.cat) noms.add(e.cat)
    return [...noms]
      .map((nom) => ({ nom, libelle: libelleCategorie(nom) }))
      .sort((a, b) => a.libelle.localeCompare(b.libelle, 'fr'))
  }, [entries])

  /* Le texte cherchable est prepare UNE FOIS au chargement, pas a chaque touche :
     normaliser 357 fiches a chaque frappe se sentait a la saisie. */
  const index = useMemo(
    () => entries.map((e) => ({ e, texte: sansAccents(`${e.question} ${e.answer} ${e.tags.join(' ')}`) })),
    [entries],
  )

  const filtered = useMemo(() => {
    const q = sansAccents(query.trim())
    return index
      .filter(({ e, texte }) => {
        if (cat && e.cat !== cat) return false
        return !q || texte.includes(q)
      })
      .map(({ e }) => e)
  }, [index, query, cat])

  const recherche = query.trim().length > 0
  // Le seul cas où l'on n'affiche pas de liste : pas de thème choisi, pas de recherche.
  const choisirUnTheme = !cat && !recherche

  function ouvrirTheme(nom: string) {
    setCat(nom)
    setOpen(null)
  }

  function tousLesThemes() {
    setCat(null)
    setQuery('')
    setOpen(null)
  }

  return (
    <>
      <Hero title="Questions fréquentes" subtitle="Les réponses d'Helios, tirées de sa base de connaissances." />
      <section className="max-w-[800px] mx-auto px-4 py-12">
        {/* Recherche — toujours présente, quel que soit l'état de la page. */}
        <div className="relative mb-8">
          <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
          <label htmlFor="faq-recherche" className="sr-only">Rechercher dans les questions fréquentes</label>
          <input
            id="faq-recherche"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(null) }}
            placeholder={cat ? `Rechercher dans « ${libelleCategorie(cat)} »…` : 'Rechercher une question, un mot-clé…'}
            className="w-full rounded-xl border border-bord bg-white pl-11 pr-4 py-3 text-ink placeholder:text-gray-400"
          />
        </div>

        {/* Les thèmes, en pastilles, TOUJOURS visibles : les 28 tiennent sous la
            recherche sans qu'on ait à faire défiler, et changer de thème est un
            seul clic. Pas de compteur — il allongeait chaque pastille pour une
            information dont personne ne fait rien. */}
        {themes.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {themes.map((t) => {
              const { Icon } = getCategoryIcon(t.nom)
              const actif = cat === t.nom
              return (
                <button
                  key={t.nom}
                  type="button"
                  onClick={() => (actif ? tousLesThemes() : ouvrirTheme(t.nom))}
                  aria-pressed={actif}
                  className={
                    'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-colors ' +
                    (actif
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white border-bord text-gray-600 hover:border-gray-300')
                  }
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" strokeWidth={1.5} aria-hidden="true" /> {t.libelle}
                </button>
              )
            })}
          </div>
        )}

        {!loaded ? (
          <p className="text-gray-500">Chargement…</p>
        ) : error ? (
          <ApiError retry={load} />
        ) : choisirUnTheme ? (
          <p className="text-gray-600">
            {entries.length} questions, classées par thème. Choisissez le vôtre ci-dessus — ou
            cherchez directement.
          </p>
        ) : (
          /* ---------------- LES QUESTIONS DU THÈME ---------------- */
          <>
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 mb-4">
              <p className="text-sm text-gray-500">
                {filtered.length} question{filtered.length > 1 ? 's' : ''}
                {recherche && cat && ` dans « ${libelleCategorie(cat)} »`}
                {recherche && !cat && ` sur ${entries.length}`}
              </p>
              <button
                type="button"
                onClick={tousLesThemes}
                className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-primary transition-colors"
              >
                <ArrowLeft className="w-4 h-4" aria-hidden="true" /> Tous les thèmes
              </button>
            </div>

            <div className="space-y-3">
              {filtered.map((e, i) => {
                const { Icon, color } = getCategoryIcon(e.cat)
                return (
                  <div key={e.question} className="rounded-2xl border border-bord bg-white">
                    <button
                      className="w-full flex items-center gap-3 justify-between p-4 text-left font-semibold text-ink"
                      onClick={() => setOpen(open === i ? null : i)}
                      aria-expanded={open === i}
                    >
                      <span className="flex items-center gap-2.5">
                        <Icon className={'w-4 h-4 shrink-0 ' + color} strokeWidth={1.5} aria-hidden="true" />
                        {e.question}
                      </span>
                      <ChevronDown className={`w-5 h-5 shrink-0 text-gray-400 transition-transform ${open === i ? 'rotate-180' : ''}`} />
                    </button>
                    {open === i && (
                      <div className="px-4 pb-4">
                        <p className="text-gray-600 whitespace-pre-line">{e.answer}</p>
                        {/* Lien vers la page dédiée : donne son adresse à chaque fiche et
                            construit le maillage interne dont dépend le référencement. */}
                        <Link
                          to={`/faq/${faqSlug(e.question)}`}
                          className="inline-flex items-center gap-1 text-sm text-primary font-semibold mt-3 hover:gap-2 transition-all"
                        >
                          Ouvrir cette fiche <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    )}
                  </div>
                )
              })}

              {filtered.length === 0 && (
                <div className="text-center py-10">
                  <p className="text-gray-600">
                    Aucune question ne correspond
                    {cat && recherche && <> dans «&nbsp;{libelleCategorie(cat)}&nbsp;»</>}.
                  </p>
                  {/* Une recherche infructueuse DANS un thème a de bonnes chances
                      d'aboutir ailleurs : on propose d'élargir plutôt que de laisser
                      le visiteur repartir. */}
                  {cat && recherche && (
                    <button
                      type="button"
                      onClick={() => { setCat(null); setOpen(null) }}
                      className="inline-flex items-center gap-1.5 text-primary font-semibold mt-3 hover:gap-2.5 transition-all"
                    >
                      Chercher dans tous les thèmes <ArrowRight className="w-4 h-4" />
                    </button>
                  )}
                  <p className="text-sm text-gray-500 mt-4">
                    Vous pouvez aussi <Link to="/helios" className="text-primary font-semibold underline underline-offset-4">poser la question à Helios</Link>.
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </section>
    </>
  )
}
