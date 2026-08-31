import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Check, Flag, Send, Sparkles } from 'lucide-react'
import HeliosAvatar, { type HeliosState } from '../HeliosAvatar'

interface Citation {
  titre: string
  cat: string | null
  score: number
}

interface ChatMessage {
  role: 'user' | 'helios'
  content: string
  citations?: Citation[]
  /** Réponse servie directement depuis la base de connaissances (sans LLM). */
  instant?: boolean
  /** Question d'origine — pour le bouton « développer avec Helios ». */
  question?: string
  /** Identifiant en base — permet de signaler la réponse (envoyé en fin de flux). */
  messageId?: string
  /** Signalement déjà envoyé : on remercie au lieu de reproposer le bouton. */
  signale?: boolean
}

/** Attente vivante : la génération locale est lente (30-60 s sur CPU), on montre
    que Helios travaille au lieu d'un « … » muet. */
const WAIT_STEPS = [
  { after: 0, text: 'Helios cherche dans sa base de connaissances…' },
  { after: 6, text: 'Helios rédige sa réponse…' },
  { after: 20, text: 'Helios rédige — la version locale prend parfois une minute, merci de patienter…' },
]

function WaitIndicator() {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + 1), 1000)
    return () => clearInterval(t)
  }, [])
  const step = [...WAIT_STEPS].reverse().find((s) => elapsed >= s.after) ?? WAIT_STEPS[0]
  return (
    <span className="inline-flex items-center gap-2 text-gray-500">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span key={i} className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
        ))}
      </span>
      {step.text}
    </span>
  )
}

const GREETING: ChatMessage = {
  role: 'helios',
  content: "Bonjour, je suis Helios 👋 Posez-moi vos questions sur l'énergie de votre logement — je suis franc et je n'ai rien à vous vendre.",
}

const SUGGESTIONS = [
  'Par quoi commencer pour isoler ma maison ?',
  'Ai-je intérêt à passer au solaire ?',
  'Quelles aides pour changer ma chaudière ?',
]

export default function ChatWidget({
  fetchImpl = fetch,
  initialConversationId = null,
  initialMessages,
  initialInput,
}: {
  /** Passer `authFetch` du AuthContext pour le mode connecté ; sinon fetch anonyme (mode public). */
  fetchImpl?: (input: string, init?: RequestInit) => Promise<Response>
  initialConversationId?: string | null
  initialMessages?: ChatMessage[]
  /** Pré-remplit le champ de saisie (ex. question + extrait d'un devis) — l'utilisateur
      garde la main : il relit et envoie lui-même, rien n'est expédié automatiquement. */
  initialInput?: string
} = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>(
    initialMessages && initialMessages.length > 0 ? initialMessages : [GREETING]
  )
  const [input, setInput] = useState(initialInput ?? '')
  const [sending, setSending] = useState(false)
  const [simplified, setSimplified] = useState(false)
  const conversationId = useRef<string | null>(initialConversationId)

  /** État de l'avatar. `n` sert à rejouer l'animation quand deux réponses
   *  d'affilée tombent dans le même état (deux « il a trouvé » de suite). */
  const [avatar, setAvatar] = useState<{ state: HeliosState; n: number }>({ state: 'salutation', n: 0 })
  const showAvatar = (state: HeliosState) => setAvatar((a) => ({ state, n: a.n + 1 }))

  function updateLastHelios(update: (m: ChatMessage) => ChatMessage) {
    setMessages((m) => {
      const next = [...m]
      next[next.length - 1] = update(next[next.length - 1])
      return next
    })
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    send(input.trim())
  }

  /** Signale une réponse. Un motif est demandé, le commentaire reste facultatif :
   *  exiger une justification découragerait justement les retours utiles. */
  async function signaler(messageId: string, index: number) {
    const commentaire = window.prompt(
      "Qu'est-ce qui ne va pas dans cette réponse ? (facultatif — le signalement part dans tous les cas)",
    )
    if (commentaire === null) return // annulation explicite
    try {
      await fetchImpl('/api/chat/signaler', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId, motif: 'autre', commentaire }),
      })
    } finally {
      // On remercie même en cas d'échec réseau : l'utilisateur n'a pas à gérer notre plomberie.
      setMessages((m) => m.map((msg, i) => (i === index ? { ...msg, signale: true } : msg)))
    }
  }

  async function send(question: string, forceLlm = false) {
    if (!question || sending) return
    setInput('')
    setSimplified(false)
    if (forceLlm) {
      // « Développer » : on remplace la réponse fiche par une vraie rédaction, sans dupliquer la question.
      setMessages((m) => [...m, { role: 'helios', content: '', question }])
    } else {
      setMessages((m) => [...m, { role: 'user', content: question }, { role: 'helios', content: '', question }])
    }
    setSending(true)
    showAvatar('reflexion')

    // Une réponse SANS citation veut dire qu'aucune fiche n'a dépassé le seuil de
    // pertinence : Helios répond hors de sa base. C'est exactement le signal que
    // le back-office compte en « questions sans réponse » — on l'affiche
    // honnêtement au client plutôt que de mimer l'assurance.
    let cited = false

    try {
      const res = await fetchImpl('/api/chat/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId.current, content: question, force_llm: forceLlm }),
      })
      if (!res.ok || !res.body) throw new Error('Le service est momentanément indisponible, réessayez.')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.trim()) continue
          const event = JSON.parse(line)
          if (event.type === 'conversation') {
            conversationId.current = event.conversation_id
            setSimplified(!!event.simplified)
            if (event.instant) updateLastHelios((msg) => ({ ...msg, instant: true }))
          } else if (event.type === 'token') {
            updateLastHelios((msg) => ({ ...msg, content: msg.content + event.text }))
          } else if (event.type === 'citations') {
            cited = Array.isArray(event.citations) && event.citations.length > 0
            updateLastHelios((msg) => ({ ...msg, citations: event.citations }))
          } else if (event.type === 'message_id') {
            // Émis une fois la réponse enregistrée : débloque le bouton « signaler ».
            updateLastHelios((msg) => ({ ...msg, messageId: event.message_id }))
          }
        }
      }
      showAvatar(cited ? 'reponse' : 'nesaitpas')
    } catch (err) {
      updateLastHelios(() => ({
        role: 'helios',
        content: err instanceof Error ? err.message : 'Une erreur est survenue.',
      }))
      showAvatar('erreur')
    } finally {
      setSending(false)
    }
  }

  const onlyGreeting = messages.length === 1 && messages[0].role === 'helios'

  return (
    /* Deux colonnes : Helios en pied, en grand, à gauche — la conversation à
       droite. L'avatar réagit à ce qui se passe (il réfléchit, il a trouvé, il
       ne sait pas, ça a raté) : à cette taille le jeu d'expressions se voit
       vraiment, ce qui n'était pas le cas d'une vignette d'en-tête. */
    <div className="rounded-2xl border border-black/5 bg-white shadow-sm max-w-[920px] mx-auto flex h-[70vh] max-h-[620px] min-h-[440px] overflow-hidden">
      <aside className="hidden md:flex flex-col items-center justify-end w-[260px] shrink-0 border-r border-black/5 bg-cream px-5 py-6 bg-gradient-to-b from-white to-cream">
        <div className="flex-1 flex items-center justify-center">
          <HeliosAvatar state={avatar.state} replay={avatar.n} height={300} />
        </div>
        <div className="text-center leading-tight mt-4">
          <div className="font-display font-semibold text-ink text-lg">Helios</div>
          <div className="text-xs text-gray-500 mt-0.5">Assistant énergie</div>
          <div className="text-xs text-gray-500">franc &amp; indépendant</div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
      {/* Mobile : pas de place pour une colonne — Helios repasse en en-tête,
          plus petit mais toujours vivant. */}
      <div className="md:hidden flex items-center gap-3 px-4 py-2 border-b border-black/5 bg-cream">
        <div className="w-16 h-16 flex items-end justify-center">
          <HeliosAvatar state={avatar.state} replay={avatar.n} height={62} />
        </div>
        <div className="leading-tight">
          <div className="font-display font-semibold text-ink">Helios</div>
          <div className="text-xs text-gray-500">Assistant énergie · franc &amp; indépendant</div>
        </div>
      </div>

      {simplified && (
        <div className="px-4 py-2 text-xs text-center bg-sun/10 text-gray-600 border-b border-black/5">
          Mode simplifié : réponse générée localement (service avancé indisponible ou limite atteinte).
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
        {messages.map((m, i) => (
          /* Plus de vignette devant chaque bulle : Helios est présent une fois,
             en grand, à côté de la conversation — le répéter à chaque message
             encombrait la lecture sans rien apporter. */
          <div key={i} className={'animate-fade-in ' + (m.role === 'user' ? 'flex justify-end' : 'flex justify-start')}>
            <div
              className={
                'max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ' +
                (m.role === 'user' ? 'bg-primary text-white' : 'bg-cream text-dark')
              }
            >
              {m.content || (sending && i === messages.length - 1 ? <WaitIndicator /> : '')}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-black/10 text-xs text-gray-500 space-y-0.5">
                  {m.citations.map((c, ci) => (
                    <div key={ci}>
                      📎{' '}
                      <Link to={`/faq?q=${encodeURIComponent(c.titre)}`} className="underline hover:text-primary">
                        {c.titre}
                      </Link>
                    </div>
                  ))}
                </div>
              )}
              {m.instant && m.content && (
                <div className="mt-2 pt-2 border-t border-black/10 text-xs text-gray-500 flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-primary" /> Réponse directe de notre base
                  </span>
                  {m.question && !sending && (
                    <button
                      onClick={() => send(m.question!, true)}
                      className="underline hover:text-primary"
                    >
                      Développer avec Helios
                    </button>
                  )}
                </div>
              )}
              {/* Signalement : rend la constitution vérifiable plutôt que seulement affirmée. */}
              {m.role === 'helios' && m.messageId && !sending && (
                <div className="mt-2 text-xs text-gray-400">
                  {m.signale ? (
                    <span className="inline-flex items-center gap-1 text-leaf">
                      <Check className="w-3.5 h-3.5" /> Merci, c'est signalé — nous le relisons.
                    </span>
                  ) : (
                    <button
                      onClick={() => signaler(m.messageId!, i)}
                      className="inline-flex items-center gap-1 hover:text-primary"
                      title="Cette réponse vous semble fausse ou gênante ?"
                    >
                      <Flag className="w-3.5 h-3.5" /> Signaler cette réponse
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Amorces de questions (page blanche → on propose) */}
        {onlyGreeting && (
          <div className="flex flex-wrap gap-2 pt-1">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)}
                className="text-xs text-ink border border-ink/20 rounded-full px-3 py-1.5 hover:bg-ink/5 transition">
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onSubmit} className="border-t border-black/5 p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Posez votre question à Helios…"
          disabled={sending}
          className="flex-1 rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-gray-50"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-xl bg-primary text-white px-4 py-2 hover:opacity-90 disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
      </div>
    </div>
  )
}
