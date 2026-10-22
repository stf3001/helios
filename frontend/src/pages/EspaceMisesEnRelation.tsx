import { useCallback, useEffect, useRef, useState } from 'react'
import { BadgeCheck, Handshake, PhoneMissed, Shuffle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import ApiError from '../components/ApiError'
import FormulaireDemande from '../components/mer/FormulaireDemande'

/** Une proposition tirée au sort par le serveur (`services/propositions.py`) : l'écran n'en
 *  choisit ni le nombre ni l'ordre, et le texte du consentement vient de l'API. */
interface Proposition {
  id: string; raison_sociale: string; rge: boolean; note_moyenne: number | null; nb_avis: number
  lien_interet: string | null; consentement: string
}
interface Lead {
  id: string
  partner: { id: string; raison_sociale: string; lien_interet: string | null } | null
  type: string
  metier: string | null
  statut: string
  montant_travaux: number | null
  consent_client_at: string
  consent_retire_at: string | null
  created_at: string
  // Suivi (lot 5) : ce que dit le partenaire et ce que dit le foyer restent séparés.
  contacte_le: string | null
  contact_foyer: 'oui' | 'non' | null
  declarations_foyer: { type: string; le: string }[]
  sans_contact_signale: boolean
  etape: string
  question_contact: boolean
  peut_noter: boolean
}

// L'étape vue du foyer (`services/suivi_foyer.etape`) : la plus avancée des deux déclarations.
const ETAPES: [string, string][] = [
  ['transmise', 'Transmise'], ['contactee', 'Contacté'], ['devis', 'Devis'], ['signee', 'Travaux signés'],
]
const DECLARE: Record<string, string> = { devis_recu: 'devis reçu', travaux_signes: 'travaux signés', projet_abandonne: 'projet abandonné' }
const ETAPE_FIN: Record<string, string> = { sans_suite: 'Sans suite', retiree: 'Consentement retiré' }
const DECLARATIONS: [string, string][] = [
  ['devis_recu', "J'ai reçu un devis"], ['travaux_signes', "J'ai signé les travaux"], ['projet_abandonne', "J'abandonne le projet"],
]
// Les métiers d'une demande : ceux de l'annuaire (`regions.METIERS`, sans le courtage).
const METIERS: [string, string][] = [
  ['solaire', 'Panneaux solaires'], ['pac', 'Pompe à chaleur'], ['isolation', 'Isolation'],
  ['eau', "Machine à eau de l'air"], ['eolien', 'Éolienne'], ['inertie', 'Stockage par inertie'],
]
// Pour relire les demandes passées, anciens codes compris.
const METIER_LABEL: Record<string, string> = {
  ...Object.fromEntries(METIERS), pv: 'Photovoltaïque', menuiseries: 'Menuiseries', vmc: 'Ventilation',
  regulation: 'Régulation',
}

export default function EspaceMisesEnRelation() {
  const { authFetch } = useAuth()
  const [propositions, setPropositions] = useState<Proposition[] | null>(null)
  const [leads, setLeads] = useState<Lead[]>([])
  const [confirmation, setConfirmation] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [partnerId, setPartnerId] = useState('')
  const [metier, setMetier] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [exclu, setExclu] = useState<string | null>(null)
  const formulaire = useRef<HTMLDivElement>(null)

  const [loadError, setLoadError] = useState(false)

  // 404 = pas encore de fiche (état normal) ; toute autre erreur = service indisponible.
  const fetchLeads = useCallback(
    () => authFetch('/api/leads').then((r) => (r.ok ? r.json() : r.status === 404 ? [] : Promise.reject(new Error(String(r.status))))),
    [authFetch],
  )

  function loadLeads() {
    fetchLeads().then(setLeads).catch(() => setLoadError(true))
  }

  const load = useCallback(() => {
    setLoading(true)
    setLoadError(false)
    fetchLeads().then(setLeads).catch(() => setLoadError(true)).finally(() => setLoading(false))
  }, [fetchLeads])
  useEffect(load, [load])

  // Un nouveau tirage à chaque choix de métier : l'ordre est celui du serveur, jamais trié ici.
  async function choisirMetier(m: string, exclure?: string) {
    setMetier(m); setPartnerId(''); setError(null); setConfirmation(null); setPropositions(null)
    setExclu(exclure ?? null)
    if (!m) return
    const res = await authFetch(`/api/leads/propositions?metier=${m}${exclure ? `&exclure=${exclure}` : ''}`)
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      setError(typeof body?.detail === 'string' ? body.detail : 'Propositions indisponibles.')
      return
    }
    setPropositions((await res.json()).propositions)
  }

  function envoye() {
    const choisi = propositions?.find((p) => p.id === partnerId)
    setPartnerId(''); setMetier(''); setPropositions(null)
    setConfirmation(`Votre demande a été transmise à ${choisi?.raison_sociale ?? 'ce partenaire'}. Il pourra vous contacter au sujet de ce projet, dans les créneaux que vous avez donnés.`)
    loadLeads()
  }

  async function poster(lead: Lead, chemin: string, corps: object) {
    const res = await authFetch(`/api/leads/${lead.id}/${chemin}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
    })
    if (res.ok) loadLeads()
  }

  /** « Non » : nouveau tirage SANS ce partenaire, puis le formulaire habituel. */
  function autreEntreprise(lead: Lead) {
    if (!lead.metier || !lead.partner) return
    choisirMetier(lead.metier, lead.partner.id)
    formulaire.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  async function withdraw(lead: Lead) {
    const res = await authFetch(`/api/leads/${lead.id}/withdraw`, { method: 'POST' })
    if (res.ok) loadLeads()
  }

  async function review(lead: Lead) {
    const note = Number(prompt('Votre note sur 5 :') || 0)
    if (note < 1 || note > 5) return
    const commentaire = prompt('Un commentaire (optionnel) :') || undefined
    const res = await authFetch(`/api/leads/${lead.id}/review`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ note, commentaire }),
    })
    if (res.ok) { alert('Merci pour votre avis !'); loadLeads() }
  }

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <Handshake className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Mes mises en relation</h1>
      </div>
      <p className="text-gray-600 mb-8">
        Demandez à être mis en relation avec un partenaire de confiance. Votre demande n'est transmise
        qu'avec votre accord, et vous pouvez le retirer tant que le devis n'est pas signé.
      </p>

      {loading ? (
        <p className="text-gray-400">Chargement…</p>
      ) : loadError ? (
        <ApiError retry={load} />
      ) : (
        <div className="space-y-10">
          {/* Nouvelle mise en relation : métier, puis au plus trois partenaires TIRÉS AU SORT
              (série 4, lot 1). Hélios est payé le même prix fixe quel que soit le choix. */}
          <div ref={formulaire} className="bg-gray-50 rounded-2xl p-6 space-y-4">
            <h2 className="font-semibold">Nouvelle demande</h2>
            {confirmation && <p className="rounded-lg bg-leaf/10 px-3 py-2 text-sm text-leaf">{confirmation}</p>}
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="metier-demande">Pour quels travaux ?</label>
              <select id="metier-demande" value={metier} onChange={(e) => choisirMetier(e.target.value)}
                className="w-full sm:w-72 rounded-lg border border-gray-300 px-3 py-2 text-sm">
                <option value="">— choisir —</option>
                {METIERS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            {propositions && propositions.length === 0 && (
              <p className="text-sm text-gray-500">Aucun partenaire disponible pour ces travaux dans votre département pour l'instant.</p>
            )}
            {propositions && propositions.length > 0 && (
              <>
                <p className="flex items-center gap-1.5 text-xs text-gray-500">
                  <Shuffle className="h-3.5 w-3.5" /> Ordre tiré au sort. Choisissez l'entreprise que vous voulez.
                  {exclu && " L'entreprise qui ne vous a pas appelé n'est pas proposée."}
                </p>
                <div className="space-y-2" role="radiogroup" aria-label="Partenaires proposés">
                  {propositions.map((p) => (
                    <label key={p.id} className={'flex items-start gap-3 rounded-xl border bg-white p-3 cursor-pointer '
                      + (partnerId === p.id ? 'border-primary' : 'border-gray-200')}>
                      <input type="radio" name="partenaire" value={p.id} checked={partnerId === p.id}
                        onChange={() => setPartnerId(p.id)} className="mt-1" />
                      <span className="min-w-0 text-sm">
                        <span className="flex flex-wrap items-center gap-2 font-semibold text-ink">
                          {p.raison_sociale}
                          {p.rge && <span className="inline-flex items-center gap-1 text-xs font-normal text-sky"><BadgeCheck className="h-3.5 w-3.5" /> RGE</span>}
                          {p.note_moyenne != null && <span className="text-xs font-normal text-gray-500">{p.note_moyenne.toFixed(1)}/5 sur {p.nb_avis} avis</span>}
                        </span>
                        {p.lien_interet && <span className="block text-xs text-terra">Lien d'intérêt : {p.lien_interet}</span>}
                      </span>
                    </label>
                  ))}
                </div>
                {partnerId && (
                  <FormulaireDemande key={partnerId} partnerId={partnerId} metier={metier} onEnvoye={envoye}
                    consentement={propositions.find((p) => p.id === partnerId)?.consentement ?? ''} />
                )}
              </>
            )}
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>

          {/* Suivi des leads */}
          <div>
            <h2 className="font-semibold text-lg mb-3">Suivi de mes demandes</h2>
            {leads.length === 0 ? (
              <p className="text-gray-400">Aucune demande pour l'instant.</p>
            ) : (
              <div className="space-y-3">
                {leads.map((lead) => (
                  <SuiviDemande key={lead.id} lead={lead} onContact={(rep) => poster(lead, 'contact', { reponse: rep })}
                    onDeclarer={(type) => poster(lead, 'declaration', { type })} onAutre={() => autreEntreprise(lead)}
                    onRetirer={() => withdraw(lead)} onNoter={() => review(lead)} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

function SuiviDemande({ lead, onContact, onDeclarer, onAutre, onRetirer, onNoter }: {
  lead: Lead; onContact: (r: 'oui' | 'non') => void; onDeclarer: (t: string) => void; onAutre: () => void
  onRetirer: () => void; onNoter: () => void
}) {
  const faites = new Set(lead.declarations_foyer.map((d) => d.type))
  const indexEtape = ETAPES.findIndex(([k]) => k === lead.etape)
  const ouverte = !lead.consent_retire_at && lead.type === 'travaux' && !ETAPE_FIN[lead.etape]
  return (
    <div className="border border-gray-200 rounded-xl p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-medium">{lead.partner?.raison_sociale ?? '—'}
          {lead.metier && <span className="text-gray-400 font-normal"> · {METIER_LABEL[lead.metier] ?? lead.metier}</span>}
        </div>
        <span className="text-xs text-dark/60">transmise le {new Date(lead.consent_client_at).toLocaleDateString('fr-FR')}</span>
      </div>
      {lead.partner?.lien_interet && <div className="text-xs text-terra">Lien d'intérêt : {lead.partner.lien_interet}</div>}

      {ETAPE_FIN[lead.etape] ? (
        <p className="text-sm text-dark/60">{ETAPE_FIN[lead.etape]}</p>
      ) : (
        <ol className="flex flex-wrap gap-1 text-xs" aria-label="Étapes de la demande">
          {ETAPES.map(([k, l], i) => (
            <li key={k} className={'rounded-full border px-2.5 py-0.5 ' + (i <= indexEtape
              ? 'border-leaf/40 bg-leaf/10 text-leaf' : 'border-bord text-dark/45')}>{l}</li>
          ))}
        </ol>
      )}

      {lead.question_contact && (
        <div role="group" aria-label="Question sur le contact" className="rounded-xl border border-sun/50 bg-sun/10 p-3 text-sm">
          <p className="font-semibold text-ink">L'entreprise vous a-t-elle contacté ?</p>
          <div className="mt-2 flex gap-2">
            <button onClick={() => onContact('oui')} className="rounded-lg border border-bord bg-white px-3 py-1.5">Oui</button>
            <button onClick={() => onContact('non')} className="rounded-lg border border-bord bg-white px-3 py-1.5">Non</button>
          </div>
        </div>
      )}
      {lead.sans_contact_signale && (
        <div className="rounded-xl border border-bord bg-cream/60 p-3 text-sm">
          <p className="flex items-center gap-1.5 text-ink"><PhoneMissed className="h-4 w-4 text-terra" />
            Vous nous avez signalé ne pas avoir été contacté. Nous le voyons de notre côté.</p>
          {lead.metier && ouverte && (
            <button onClick={onAutre} className="mt-2 rounded-xl bg-primary px-4 py-1.5 text-sm font-semibold text-white hover:opacity-90">
              Demander une autre entreprise
            </button>
          )}
        </div>
      )}

      {ouverte && (
        <div className="flex flex-wrap gap-2 text-xs">
          {DECLARATIONS.filter(([t]) => !faites.has(t)).map(([t, l]) => (
            <button key={t} onClick={() => onDeclarer(t)} className="rounded-lg border border-bord bg-white px-3 py-1.5 text-dark/80 hover:bg-cream">{l}</button>
          ))}
          {lead.statut !== 'signe' && !faites.has('travaux_signes') && (
            <button onClick={onRetirer} className="px-1 text-red-500 underline">Retirer mon consentement</button>
          )}
        </div>
      )}
      {lead.declarations_foyer.length > 0 && (
        <p className="text-xs text-dark/60">Vous avez déclaré : {lead.declarations_foyer.map((d) =>
          `${DECLARE[d.type] ?? d.type} (${new Date(d.le).toLocaleDateString('fr-FR')})`).join(' · ')}</p>
      )}
      {lead.peut_noter && <button onClick={onNoter} className="text-xs text-primary underline">Noter cette entreprise</button>}
    </div>
  )
}
