import { useRef, useState, type FormEvent } from 'react'
import { Send } from 'lucide-react'

interface Citation {
  titre: string
  cat: string | null
  score: number
}

interface ChatMessage {
  role: 'user' | 'helios'
  content: string
  citations?: Citation[]
}

const GREETING: ChatMessage = {
  role: 'helios',
  content: "Bonjour, je suis Helios. Posez-moi vos questions sur l'énergie de votre logement…",
}

export default function ChatWidget({
  fetchImpl = fetch,
  initialConversationId = null,
  initialMessages,
}: {
  /** Passer `authFetch` du AuthContext pour le mode connecté ; sinon fetch anonyme (mode public). */
  fetchImpl?: (input: string, init?: RequestInit) => Promise<Response>
  initialConversationId?: string | null
  initialMessages?: ChatMessage[]
} = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>(
    initialMessages && initialMessages.length > 0 ? initialMessages : [GREETING]
  )
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [simplified, setSimplified] = useState(false)
  const conversationId = useRef<string | null>(initialConversationId)

  function updateLastHelios(update: (m: ChatMessage) => ChatMessage) {
    setMessages((m) => {
      const next = [...m]
      next[next.length - 1] = update(next[next.length - 1])
      return next
    })
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const question = input.trim()
    if (!question || sending) return
    setInput('')
    setSimplified(false)
    setMessages((m) => [...m, { role: 'user', content: question }, { role: 'helios', content: '' }])
    setSending(true)

    try {
      const res = await fetchImpl('/api/chat/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId.current, content: question }),
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
          } else if (event.type === 'token') {
            updateLastHelios((msg) => ({ ...msg, content: msg.content + event.text }))
          } else if (event.type === 'citations') {
            updateLastHelios((msg) => ({ ...msg, citations: event.citations }))
          }
        }
      }
    } catch (err) {
      updateLastHelios(() => ({
        role: 'helios',
        content: err instanceof Error ? err.message : 'Une erreur est survenue.',
      }))
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm max-w-[700px] mx-auto flex flex-col h-[520px]">
      {simplified && (
        <div className="px-4 py-2 text-xs text-center bg-sun/10 text-gray-600 border-b border-gray-100">
          Mode simplifié : réponse générée localement (service avancé indisponible ou limite atteinte).
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <div
              className={
                'max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ' +
                (m.role === 'user' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-800')
              }
            >
              {m.content || (sending && i === messages.length - 1 ? '…' : '')}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300/50 text-xs text-gray-500 space-y-0.5">
                  {m.citations.map((c, ci) => (
                    <div key={ci}>📎 {c.titre}</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={onSubmit} className="border-t border-gray-100 p-3 flex gap-2">
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
  )
}
