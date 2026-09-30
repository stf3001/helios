import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'

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
  const idChamp = useId()

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
    <form onSubmit={onSubmit} className="w-full">
      {/* Le placeholder tourne : il ne peut pas tenir lieu d'etiquette. Celle-ci
          est donc ecrite, et seulement masquee a l'oeil. */}
      <label htmlFor={idChamp} className="sr-only">Posez votre première question à Helios</label>
      <div className="flex items-center gap-2 rounded-2xl bg-white border border-bord p-2 shadow-question">
        <Sparkles className="ml-2 w-[18px] h-[18px] shrink-0 text-primary" aria-hidden="true" />
        <input
          id={idChamp}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => { focused.current = true }}
          onBlur={() => { focused.current = false }}
          placeholder={EXEMPLES[idx]}
          className="flex-1 min-w-0 bg-transparent py-2 text-ink placeholder:text-gray-400 placeholder:truncate focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 shrink-0 hover:bg-terra transition-colors"
        >
          Demander
        </button>
      </div>
    </form>
  )
}
