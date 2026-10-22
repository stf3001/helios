import { useCallback, useEffect, useState } from 'react'
import { BadgeCheck, Handshake, Shuffle } from 'lucide-react'
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
  consent_retire_at: string | null
  created_at: string
}

const STATUT_LABEL: Record<string, string> = {
  nouveau: 'Nouveau', transmis: 'Transmis', contacte: 'Contacté',
  devis: 'Devis reçu', signe: 'Signé', perdu: 'Sans suite',
}
const STATUT_STYLE: Record<string, string> = {
  transmis: 'bg-blue-100 text-blue-800', contacte: 'bg-indigo-100 text-indigo-800',
  devis: 'bg-amber-100 text-amber-800', signe: 'bg-green-100 text-green-800',
  perdu: 'bg-gray-100 text-gray-500',
}
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
  async function choisirMetier(m: string) {
    setMetier(m); setPartnerId(''); setError(null); setConfirmation(null); setPropositions(null)
    if (!m) return
    const res = await authFetch(`/api/leads/propositions?metier=${m}`)
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

  async function reportStatus(lead: Lead, statut: string) {
    const body: Record<string, unknown> = { statut }
    if (statut === 'devis' || statut === 'signe') {
      const montant = Number(prompt('Montant des travaux (HT, en euros) :') || 0)
      if (!montant) return
      body.montant_travaux = montant
    }
    const res = await authFetch(`/api/leads/${lead.id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
    if (res.ok) loadLeads()
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
          <div className="bg-gray-50 rounded-2xl p-6 space-y-4">
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
                  <div key={lead.id} className="border border-gray-200 rounded-xl p-4">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="font-medium">{lead.partner?.raison_sociale ?? '—'}
                        {lead.metier && <span className="text-gray-400 font-normal"> · {METIER_LABEL[lead.metier] ?? lead.metier}</span>}
                      </div>
                      <span className={'text-xs px-2 py-0.5 rounded-full ' + (STATUT_STYLE[lead.statut] ?? 'bg-gray-100 text-gray-600')}>
                        {STATUT_LABEL[lead.statut] ?? lead.statut}
                      </span>
                    </div>
                    {lead.partner?.lien_interet && (
                      <div className="text-xs text-terra mb-2">Lien d'intérêt : {lead.partner.lien_interet}</div>
                    )}
                    <div className="flex flex-wrap gap-2 text-xs">
                      {['transmis', 'contacte', 'devis'].includes(lead.statut) && (
                        <>
                          {lead.statut === 'transmis' && (
                            <button onClick={() => reportStatus(lead, 'contacte')} className="underline text-gray-600">Le partenaire m'a contacté</button>
                          )}
                          <button onClick={() => reportStatus(lead, 'devis')} className="underline text-gray-600">J'ai reçu un devis</button>
                          <button onClick={() => reportStatus(lead, 'signe')} className="underline text-gray-600">J'ai signé</button>
                          <button onClick={() => withdraw(lead)} className="underline text-red-500">Retirer mon consentement</button>
                        </>
                      )}
                      {lead.statut === 'signe' && (
                        <button onClick={() => review(lead)} className="underline text-primary">Noter ce partenaire</button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
