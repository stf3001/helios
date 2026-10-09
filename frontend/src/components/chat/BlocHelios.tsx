import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, History, Plus } from 'lucide-react'
import ChatWidget from './ChatWidget'
import Depliant from '../Depliant'
import MarqueHelios from '../MarqueHelios'
import { useAuth } from '../../context/AuthContext'

/**
 * La conversation avec Helios, telle qu'elle vit DANS « Mon espace ».
 *
 * Elle remplace la page « Mon Helios » (`/espace/helios`, supprimee le 30/09/2026) :
 * cette page ne servait qu'a loger le meme widget a cote d'une colonne d'historique,
 * et obligeait a quitter l'espace pour poser une question. L'historique n'avait pas
 * besoin d'une page, il tient dans un menu deroulant.
 *
 * L'etat vit ici et non dans la page : « Mon espace » n'a pas a connaitre les
 * conversations pour afficher le reste de ses blocs.
 */

interface Citation {
  titre: string
  cat: string | null
  score: number
}

interface ConversationResumee {
  id: string
  mode: string
  started_at: string
}

interface MessageArchive {
  role: 'user' | 'helios'
  content: string
  citations?: Citation[]
}

/** « Aujourd'hui » et « Hier » plutot qu'une date : dans une liste ou toutes les
 *  lignes se ressemblent, c'est le repere le plus rapide a lire. */
function libelleDate(iso: string): string {
  const d = new Date(iso)
  const jour = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const aujourdhui = new Date()
  const zero = new Date(aujourdhui.getFullYear(), aujourdhui.getMonth(), aujourdhui.getDate())
  const ecart = Math.round((zero.getTime() - jour.getTime()) / 86_400_000)
  const heure = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  if (ecart === 0) return `Aujourd'hui · ${heure}`
  if (ecart === 1) return `Hier · ${heure}`
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

export default function BlocHelios({ askPrefill }: { askPrefill?: string }) {
  const { authFetch } = useAuth()
  const [conversations, setConversations] = useState<ConversationResumee[]>([])
  const [selectionnee, setSelectionnee] = useState<string | null>(null)
  const [messages, setMessages] = useState<MessageArchive[] | undefined>(undefined)
  const [ouvert, setOuvert] = useState(false)
  const [chargement, setChargement] = useState(false)
  const menu = useRef<HTMLDivElement>(null)

  const charger = useCallback(() => {
    setChargement(true)
    authFetch('/api/chat/conversations')
      .then((res) => (res.ok ? res.json() : []))
      .then(setConversations)
      .catch(() => setConversations([]))
      .finally(() => setChargement(false))
  }, [authFetch])

  // La liste se relit A L'OUVERTURE du menu : une conversation entamee juste avant
  // doit s'y trouver, et un chargement au montage de la page serait deja perime.
  useEffect(() => { if (ouvert) charger() }, [ouvert, charger])

  // Fermeture au clic en dehors et a Echap — un menu qui reste ouvert par-dessus
  // la conversation empeche de la lire.
  useEffect(() => {
    if (!ouvert) return
    const auClic = (e: MouseEvent) => {
      if (menu.current && !menu.current.contains(e.target as Node)) setOuvert(false)
    }
    const auClavier = (e: KeyboardEvent) => { if (e.key === 'Escape') setOuvert(false) }
    document.addEventListener('mousedown', auClic)
    document.addEventListener('keydown', auClavier)
    return () => {
      document.removeEventListener('mousedown', auClic)
      document.removeEventListener('keydown', auClavier)
    }
  }, [ouvert])

  async function ouvrirConversation(id: string) {
    const res = await authFetch(`/api/chat/conversations/${id}/messages`)
    if (!res.ok) return
    const data = await res.json()
    setMessages(data.map((m: MessageArchive) => ({ role: m.role, content: m.content, citations: m.citations })))
    setSelectionnee(id)
    setOuvert(false)
  }

  function nouvelleConversation() {
    setSelectionnee(null)
    setMessages(undefined)
    setOuvert(false)
  }

  return (
    /* PLIABLE, comme le reste de l'espace (demande de Stephane, 06/10/2026), mais
       OUVERT A L'ARRIVEE : la conversation est ce pour quoi on vient ici, la replier
       d'office reviendrait a remettre un clic entre le client et Helios — ce que la
       fusion du 30/09 avait justement supprime.

       Les commandes (« Mes conversations », « Nouvelle ») sont DANS le panneau et non
       dans l'en-tete : un bouton pose dans un `<summary>` replie le bloc quand on le
       clique, et le rattraper demanderait d'intercepter l'evenement a chaque fois. */
    <Depliant
      titre="Parler à Helios"
      icone={<MarqueHelios taille={18} className="text-primary" />}
      aide="Il connaît déjà votre fiche et vos simulations — pas besoin de tout réexpliquer."
      ouvert
    >
      <div className="flex flex-wrap items-center justify-end gap-2">
        {selectionnee && (
          <button
            type="button"
            onClick={nouvelleConversation}
            className="inline-flex items-center gap-1.5 rounded-xl border border-bord bg-white px-3 py-2 text-sm font-semibold text-ink hover:border-gray-300 transition-colors"
          >
            <Plus className="w-4 h-4" aria-hidden="true" /> Nouvelle
          </button>
        )}

        <div className="relative" ref={menu}>
          <button
            type="button"
            onClick={() => setOuvert((v) => !v)}
            aria-expanded={ouvert}
            aria-controls="liste-conversations"
            className="inline-flex items-center gap-1.5 rounded-xl border border-bord bg-white px-3 py-2 text-sm font-semibold text-ink hover:border-gray-300 transition-colors"
          >
            <History className="w-4 h-4" aria-hidden="true" />
            Mes conversations
            <ChevronDown
              className={'w-4 h-4 transition-transform ' + (ouvert ? 'rotate-180' : '')}
              aria-hidden="true"
            />
          </button>

          {ouvert && (
            <div
              id="liste-conversations"
              /* Ancre A GAUCHE du bouton par defaut : sur un telephone les commandes
                 passent a la ligne et se rangent a gauche, un panneau aligne a droite
                 sortait alors de l'ecran. Il ne bascule a droite qu'a partir du moment
                 ou le bouton est lui-meme a droite du titre. */
              className="absolute left-0 sm:left-auto sm:right-0 z-30 mt-2 w-[19rem] max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-bord bg-white shadow-question"
            >
              <button
                type="button"
                onClick={nouvelleConversation}
                className="flex w-full items-center gap-2 border-b border-bord px-4 py-3 text-sm font-semibold text-primary hover:bg-cream transition-colors"
              >
                <Plus className="w-4 h-4" aria-hidden="true" /> Nouvelle conversation
              </button>

              <div className="max-h-72 overflow-y-auto">
                {chargement && <p className="px-4 py-3 text-sm text-gray-500">Chargement…</p>}
                {!chargement && conversations.length === 0 && (
                  <p className="px-4 py-3 text-sm text-gray-500">
                    Aucune conversation enregistrée pour l'instant.
                  </p>
                )}
                {conversations.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => ouvrirConversation(c.id)}
                    aria-current={c.id === selectionnee}
                    className={
                      'block w-full truncate px-4 py-2.5 text-left text-sm transition-colors ' +
                      (c.id === selectionnee
                        ? 'bg-primary/5 font-semibold text-primary'
                        : 'text-gray-600 hover:bg-cream')
                    }
                  >
                    {libelleDate(c.started_at)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* `key` : rouvrir une conversation doit REMONTER le widget, sinon il garderait
          les messages et l'identifiant de la precedente. */}
      <ChatWidget
        key={selectionnee ?? 'nouvelle'}
        fetchImpl={authFetch}
        compact
        initialConversationId={selectionnee}
        initialMessages={messages}
        initialInput={!selectionnee ? askPrefill : undefined}
      />
    </Depliant>
  )
}
