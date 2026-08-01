import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

/** Champ de saisie du hero : « essayer le produit avant de scroller ». Le placeholder fait
 * défiler de vraies questions (démontre l'étendue d'Helios), et l'envoi amène l'utilisateur
 * dans le chat public (/helios) avec sa question déjà en place — il garde la main pour l'envoyer. */
const EXEMPLES = [
  'Dois-je isoler mes combles avant de changer ma chaudière ?',
  'Ma facture d\'électricité est-elle normale ?',
  'Par où commencer avec un petit budget ?',
  'Le solaire est-il rentable chez moi ?',
  'Quelles aides pour une pompe à chaleur ?',
]

export default function HeroSearch() {
  const navigate = useNavigate()
  const [value, setValue] = useState('')
  const [idx, setIdx] = useState(0)
  const focused = useRef(false)

  // Rotation du placeholder — figée dès que l'utilisateur interagit (focus ou saisie).
  useEffect(() => {
    const id = setInterval(() => {
      if (!focused.current && value === '') setIdx((i) => (i + 1) % EXEMPLES.length)
    }, 3500)
    return () => clearInterval(id)
  }, [value])

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    const q = value.trim()
    // Sans saisie, le bouton propose quand même d'entrer dans le chat avec l'exemple affiché.
    navigate(q ? `/helios?q=${encodeURIComponent(q)}` : '/helios')
  }

  return (
    <form onSubmit={onSubmit} className="mt-7 max-w-xl">
      <div className="flex items-stretch gap-2 rounded-2xl bg-white p-1.5 shadow-lg shadow-black/5">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => { focused.current = true }}
          onBlur={() => { focused.current = false }}
          placeholder={EXEMPLES[idx]}
          aria-label="Posez votre première question à Helios"
          className="flex-1 min-w-0 bg-transparent px-3 py-2.5 text-ink placeholder:text-gray-400 focus:outline-none"
        />
        <button
          type="submit"
          className="inline-flex items-center gap-2 rounded-xl bg-primary text-white font-semibold px-4 sm:px-5 py-2.5 hover:opacity-90 shrink-0"
        >
          <span className="hidden sm:inline">Demander</span>
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </form>
  )
}
