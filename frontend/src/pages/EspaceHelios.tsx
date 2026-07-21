import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ChatWidget from '../components/chat/ChatWidget'
import { useAuth } from '../context/AuthContext'

interface Citation {
  titre: string
  cat: string | null
  score: number
}

interface ConversationSummary {
  id: string
  mode: string
  started_at: string
}

interface ChatMessage {
  role: 'user' | 'helios'
  content: string
  citations?: Citation[]
}

export default function EspaceHelios() {
  const { authFetch } = useAuth()
  // Arrivée depuis "Demander l'avis d'Helios" (documents) : ?ask=<question pré-remplie>.
  const [searchParams] = useSearchParams()
  const askPrefill = searchParams.get('ask') ?? undefined
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [initialMessages, setInitialMessages] = useState<ChatMessage[] | undefined>(undefined)
  const [loading, setLoading] = useState(true)

  function loadConversations() {
    authFetch('/api/chat/conversations')
      .then((res) => (res.ok ? res.json() : []))
      .then(setConversations)
      .finally(() => setLoading(false))
  }

  useEffect(loadConversations, [authFetch])

  async function openConversation(id: string) {
    const res = await authFetch(`/api/chat/conversations/${id}/messages`)
    if (!res.ok) return
    const data = await res.json()
    setInitialMessages(data.map((m: ChatMessage) => ({ role: m.role, content: m.content, citations: m.citations })))
    setSelectedId(id)
  }

  function startNewConversation() {
    setSelectedId(null)
    setInitialMessages(undefined)
  }

  return (
    <section className="max-w-[1000px] mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-2">Mon Helios</h1>
      <p className="text-gray-600 mb-8">
        Conseil personnalisé à partir de votre fiche maison — reprenez une conversation ou démarrez-en une nouvelle.
      </p>

      <div className="grid md:grid-cols-[220px_1fr] gap-6">
        <div className="space-y-2">
          <button
            onClick={startNewConversation}
            className="w-full rounded-xl bg-primary text-white text-sm font-semibold px-3 py-2 hover:opacity-90"
          >
            + Nouvelle conversation
          </button>
          <div className="space-y-1">
            {loading && <p className="text-xs text-gray-400">Chargement…</p>}
            {!loading && conversations.length === 0 && (
              <p className="text-xs text-gray-400">Aucune conversation pour l'instant.</p>
            )}
            {conversations.map((c) => (
              <button
                key={c.id}
                onClick={() => openConversation(c.id)}
                className={
                  'block w-full text-left text-xs rounded-lg px-3 py-2 truncate ' +
                  (c.id === selectedId ? 'bg-primary/10 text-primary font-semibold' : 'hover:bg-gray-100 text-gray-600')
                }
              >
                {new Date(c.started_at).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })}
              </button>
            ))}
          </div>
        </div>

        <ChatWidget
          key={selectedId ?? 'new'}
          fetchImpl={authFetch}
          initialConversationId={selectedId}
          initialMessages={initialMessages}
          initialInput={!selectedId ? askPrefill : undefined}
        />
      </div>
    </section>
  )
}
