import { useEffect, useState } from 'react'
import { AlertTriangle, ArrowLeft, MessageSquare, TriangleAlert, User2, UserCircle2, Users2 } from 'lucide-react'
import Depliant from '../../components/Depliant'
import { Attente, Erreur, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Ligne {
  id: string
  mode: string
  started_at: string
  dernier_message: string | null
  email: string | null
  prenom: string | null
  nb_messages: number
  sans_reponse: boolean
}

interface MessageDetail {
  role: string
  content: string
  created_at: string
  model_used: string | null
  rag_score: number | null
  citations: { titre: string; cat: string | null; score: number }[] | null
  tokens: number | null
  cout_eur: number | null
  constitution_version: string | null
}

interface Detail {
  id: string
  mode: string
  started_at: string
  foyer: { email: string; prenom: string | null } | null
  messages: MessageDetail[]
  seuil_pertinence: number
}

const VOIE: Record<string, { label: string; classe: string }> = {
  kb: { label: 'instantané', classe: 'border-leaf/40 bg-leaf/10 text-leaf' },
  local: { label: 'local', classe: 'border-sky/40 bg-sky/10 text-sky' },
  api: { label: 'API', classe: 'border-terra/40 bg-terra/10 text-terra' },
}

export default function AdminConversations() {
  useTitle('Back-office — Conversations')
  const [ouverte, setOuverte] = useState<string | null>(null)
  const { data, error } = useAdminData<{ total: number; conversations: Ligne[] }>(
    '/api/admin/conversations?limit=60',
  )

  if (ouverte) return <DetailConversation id={ouverte} onRetour={() => setOuverte(null)} />

  /* Les trois filtres « Toutes / Public / Connecté » ont été remplacés par trois blocs
     repliables (demande de Stéphane, 08/10/2026). Ils disent la même chose, mais sans
     cacher les deux autres populations — et surtout ils sortent EN TÊTE les échanges où
     Helios n'a rien trouvé de pertinent, qui sont les seuls à appeler un travail. Les
     groupes sont exclusifs : une conversation sans réponse n'est pas répétée plus bas. */
  const toutes = data?.conversations ?? []
  const sansReponse = toutes.filter((c) => c.sans_reponse)
  const reste = toutes.filter((c) => !c.sans_reponse)
  const groupes = [
    {
      cle: 'sans_reponse',
      titre: 'À regarder en priorité',
      aide: "Helios n'a trouvé aucune source au-dessus du seuil de pertinence : la base de connaissances a un trou, ou la question était hors de son champ.",
      Icone: TriangleAlert,
      couleur: 'text-terra',
      lignes: sansReponse,
      ouvert: sansReponse.length > 0,
    },
    {
      cle: 'connecte',
      titre: 'Foyers connectés',
      aide: 'Échanges où Helios disposait de la fiche maison et des études du foyer.',
      Icone: UserCircle2,
      couleur: 'text-primary',
      lignes: reste.filter((c) => c.mode === 'connecte'),
      ouvert: sansReponse.length === 0,
    },
    {
      cle: 'public',
      titre: 'Visiteurs anonymes',
      aide: 'Échanges publics, sans compte : Helios ne répond que sur la base de connaissances.',
      Icone: Users2,
      couleur: 'text-sky',
      lignes: reste.filter((c) => c.mode !== 'connecte'),
      ouvert: false,
    },
  ]

  return (
    <>
      <TitrePage titre="Conversations">
        Échanges réels avec Helios. L'identité du foyer est affichée — accès complet assumé, et
        chaque consultation nominative est tracée dans le journal des accès.
      </TitrePage>

      {error && <Erreur>{error}</Erreur>}
      {!data && !error && <Attente />}

      {data && (
        <>
          <p className="mt-4 text-xs text-dark/55">
            {data.total} conversation(s) au total · {toutes.length} affichée(s)
          </p>
          <div className="mt-3 space-y-3">
            {groupes.map((g) => (
              <Depliant
                key={g.cle}
                titre={g.titre}
                aide={g.aide}
                ouvert={g.ouvert}
                icone={<g.Icone className={'h-5 w-5 shrink-0 ' + g.couleur} />}
                resume={<span className="tabular-nums">{g.lignes.length}</span>}
              >
                {g.lignes.length === 0 ? (
                  <p className="text-sm text-dark/70">Aucune conversation dans ce groupe.</p>
                ) : (
                  <div className="space-y-2">
                    {g.lignes.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => setOuverte(c.id)}
                        className="w-full rounded-xl border border-bord bg-cream/50 p-3 text-left transition hover:border-primary/40 hover:bg-cream"
                      >
                        <div className="flex flex-wrap items-center gap-2 text-sm">
                          <span className="rounded-full border border-bord bg-white px-2 py-0.5 text-xs text-dark/70">
                            {c.mode}
                          </span>
                          <span className="flex items-center gap-1.5 text-ink">
                            <User2 className="h-3.5 w-3.5 text-dark/45" />
                            {c.email ?? <span className="text-dark/55">visiteur anonyme</span>}
                          </span>
                          <span className="flex items-center gap-1 text-xs text-dark/55">
                            <MessageSquare className="h-3.5 w-3.5" /> {c.nb_messages}
                          </span>
                          {c.sans_reponse && (
                            <span className="flex items-center gap-1 rounded-full border border-terra/40 bg-terra/10 px-2 py-0.5 text-xs text-terra">
                              <AlertTriangle className="h-3 w-3" /> sans réponse pertinente
                            </span>
                          )}
                          <span className="ml-auto text-xs tabular-nums text-dark/45">
                            {new Date(c.dernier_message ?? c.started_at).toLocaleString('fr-FR')}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </Depliant>
            ))}
          </div>
        </>
      )}
    </>
  )
}

function DetailConversation({ id, onRetour }: { id: string; onRetour: () => void }) {
  const { authFetch } = useAuth()
  const [detail, setDetail] = useState<Detail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let annule = false
    authFetch(`/api/admin/conversations/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`Erreur ${r.status}`))))
      .then((d) => { if (!annule) setDetail(d) })
      .catch((e) => { if (!annule) setError(e.message) })
    return () => { annule = true }
    // `authFetch` est recréé à chaque rendu du provider : l'exclure évite une boucle de requêtes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  return (
    <>
      <button onClick={onRetour} className="flex items-center gap-1.5 text-sm text-primary hover:text-terra">
        <ArrowLeft className="h-4 w-4" /> Toutes les conversations
      </button>

      {error && <Erreur>{error}</Erreur>}
      {!detail && !error && <Attente />}

      {detail && (
        <>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <h1 className="font-display text-2xl text-ink">
              {detail.foyer ? `${detail.foyer.prenom ?? ''} ${detail.foyer.email}`.trim() : 'Visiteur anonyme'}
            </h1>
            <span className="rounded-full border border-bord bg-white px-2 py-0.5 text-xs text-dark/70">{detail.mode}</span>
            <span className="text-xs text-dark/55">{new Date(detail.started_at).toLocaleString('fr-FR')}</span>
          </div>

          <div className="mt-5 space-y-3">
            {detail.messages.map((m, i) => {
              const estHelios = m.role === 'helios'
              const voie = m.model_used ? VOIE[m.model_used] : null
              const scoreFaible = m.rag_score != null && m.rag_score < detail.seuil_pertinence
              return (
                <div
                  key={i}
                  className={
                    'rounded-2xl border border-bord p-4 ' + (estHelios ? 'bg-white' : 'bg-cream/60')
                  }
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                    <span className={estHelios ? 'font-semibold text-primary' : 'font-semibold text-dark/70'}>
                      {estHelios ? 'Helios' : 'Foyer'}
                    </span>
                    {voie && <span className={'rounded-full border px-2 py-0.5 ' + voie.classe}>{voie.label}</span>}
                    {m.rag_score != null && (
                      <span className={scoreFaible ? 'text-terra' : 'text-dark/55'}>
                        score {m.rag_score}
                        {scoreFaible && ' · sous le seuil'}
                      </span>
                    )}
                    {m.cout_eur != null && <span className="text-dark/55">{m.cout_eur.toFixed(4)} €</span>}
                    {m.constitution_version && <span className="text-dark/45">constitution {m.constitution_version}</span>}
                    <span className="ml-auto text-dark/45">{new Date(m.created_at).toLocaleTimeString('fr-FR')}</span>
                  </div>

                  <p className="whitespace-pre-line text-sm text-dark">{m.content}</p>

                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 border-t border-bord pt-2">
                      <div className="mb-1 text-xs text-dark/55">Sources mobilisées</div>
                      <div className="flex flex-wrap gap-1.5">
                        {m.citations.map((c, j) => (
                          <span key={j} className="rounded-full bg-cream px-2 py-0.5 text-xs text-dark/70">
                            {c.titre.slice(0, 60)} <span className="text-dark/45">{c.score}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </>
  )
}
