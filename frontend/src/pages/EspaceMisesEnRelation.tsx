import { useEffect, useState, type FormEvent } from 'react'
import { Handshake } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

interface PartnerCard { id: string; raison_sociale: string; metiers: string[]; note_moyenne: number | null }
interface Lead {
  id: string
  partner: { id: string; raison_sociale: string } | null
  type: string
  metier: string | null
  statut: string
  montant_travaux: number | null
  commission: number | null
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
const METIER_LABEL: Record<string, string> = {
  pv: 'Photovoltaïque', pac: 'Pompe à chaleur', isolation: 'Isolation',
  menuiseries: 'Menuiseries', vmc: 'Ventilation', regulation: 'Régulation',
}

export default function EspaceMisesEnRelation() {
  const { authFetch } = useAuth()
  const [partners, setPartners] = useState<PartnerCard[]>([])
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)

  const [partnerId, setPartnerId] = useState('')
  const [metier, setMetier] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function loadLeads() {
    authFetch('/api/leads').then((r) => (r.ok ? r.json() : [])).then(setLeads)
  }

  useEffect(() => {
    Promise.all([
      fetch('/api/partners').then((r) => (r.ok ? r.json() : [])),
      authFetch('/api/leads').then((r) => (r.ok ? r.json() : [])),
    ]).then(([p, l]) => { setPartners(p); setLeads(l) }).finally(() => setLoading(false))
  }, [authFetch])

  async function createLead(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const res = await authFetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ partner_id: partnerId, metier: metier || null, type: 'travaux', consent }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Mise en relation impossible.')
      }
      setPartnerId(''); setMetier(''); setConsent(false)
      loadLeads()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setSubmitting(false)
    }
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
      ) : (
        <div className="space-y-10">
          {/* Nouvelle mise en relation */}
          <form onSubmit={createLead} className="bg-gray-50 rounded-2xl p-6 space-y-4">
            <h2 className="font-semibold">Nouvelle demande</h2>
            {partners.length === 0 ? (
              <p className="text-sm text-gray-500">Aucun partenaire disponible pour l'instant.</p>
            ) : (
              <>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Partenaire</label>
                    <select value={partnerId} onChange={(e) => setPartnerId(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                      <option value="">— choisir —</option>
                      {partners.map((p) => (
                        <option key={p.id} value={p.id}>{p.raison_sociale}{p.note_moyenne != null ? ` (★ ${p.note_moyenne})` : ''}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Type de travaux</label>
                    <select value={metier} onChange={(e) => setMetier(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                      <option value="">— indifférent —</option>
                      {Object.entries(METIER_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                </div>
                <label className="flex items-start gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
                  <span>J'accepte que ma demande et les informations de mon projet (fiche maison, pré-audit)
                    soient transmises à ce partenaire.</span>
                </label>
                <button type="submit" disabled={!partnerId || !consent || submitting}
                  className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-40">
                  {submitting ? 'Envoi…' : 'Demander la mise en relation'}
                </button>
                {error && <p className="text-sm text-red-600">{error}</p>}
              </>
            )}
          </form>

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
                    {lead.commission != null && (
                      <div className="text-xs text-gray-500 mb-2">
                        Travaux signés : {lead.montant_travaux?.toLocaleString('fr-FR')} € HT — commission HELIOS (payée par le partenaire) : {lead.commission.toLocaleString('fr-FR')} €
                      </div>
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
