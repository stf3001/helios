import { useEffect, useState, type FormEvent } from 'react'
import { Building2 } from 'lucide-react'
import PasswordInput from '../components/PasswordInput'

interface PLead {
  id: string
  type: string
  metier: string | null
  statut: string
  code_postal: string | null
  montant_travaux: number | null
  commission: number | null
  consent_retire: boolean
  created_at: string
}

const STATUT_LABEL: Record<string, string> = {
  transmis: 'Transmis', contacte: 'Contacté', devis: 'Devis', signe: 'Signé', perdu: 'Perdu',
}
const METIER_LABEL: Record<string, string> = {
  pv: 'Photovoltaïque', pac: 'Pompe à chaleur', isolation: 'Isolation',
  menuiseries: 'Menuiseries', vmc: 'Ventilation', regulation: 'Régulation',
}
const TOKEN_KEY = 'helios_partner_token'

export default function PartnerPortal() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [name, setName] = useState<string | null>(null)
  const [leads, setLeads] = useState<PLead[]>([])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  function pFetch(path: string, init?: RequestInit) {
    return fetch(path, { ...init, headers: { ...(init?.headers || {}), Authorization: `Bearer ${token}` } })
  }

  function loadLeads() {
    if (!token) return
    pFetch('/api/partner/leads').then((r) => {
      if (r.status === 401) { logout(); return [] }
      return r.ok ? r.json() : []
    }).then(setLeads)
  }
  useEffect(loadLeads, [token])

  async function login(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const res = await fetch('/api/partner/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) { setError('Identifiants invalides.'); return }
    const data = await res.json()
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setToken(data.access_token)
    setName(data.raison_sociale)
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setLeads([])
  }

  async function advance(lead: PLead, statut: string) {
    const body: Record<string, unknown> = { statut }
    if (statut === 'devis' || statut === 'signe') {
      const montant = Number(prompt('Montant des travaux (HT, €) :') || 0)
      if (!montant) return
      body.montant_travaux = montant
    }
    if (statut === 'perdu') {
      body.motif_perdu = prompt('Motif (obligatoire) :') || 'Non précisé'
    }
    const res = await pFetch(`/api/partner/leads/${lead.id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
    if (res.ok) loadLeads()
    else { const b = await res.json().catch(() => null); alert(b?.detail || 'Action impossible.') }
  }

  if (!token) {
    return (
      <section className="max-w-sm mx-auto px-4 py-16">
        <div className="flex items-center gap-2 mb-6">
          <Building2 className="w-7 h-7 text-primary" />
          <h1 className="text-2xl font-bold">Espace partenaire</h1>
        </div>
        <form onSubmit={login} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Mot de passe</label>
            <PasswordInput required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <button type="submit" className="w-full rounded-xl bg-primary text-white font-semibold px-4 py-2.5 hover:opacity-90">
            Se connecter
          </button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </form>
        <p className="text-xs text-gray-400 mt-6">
          Vous n'êtes pas encore partenaire ? Faites votre demande sur la page « Devenir partenaire ».
        </p>
      </section>
    )
  }

  const next: Record<string, { statut: string; label: string }[]> = {
    transmis: [{ statut: 'contacte', label: 'Marquer contacté' }, { statut: 'perdu', label: 'Perdu' }],
    contacte: [{ statut: 'devis', label: 'Devis émis' }, { statut: 'perdu', label: 'Perdu' }],
    devis: [{ statut: 'signe', label: 'Signé' }, { statut: 'perdu', label: 'Perdu' }],
  }

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Building2 className="w-7 h-7 text-primary" />
          <h1 className="text-2xl font-bold">{name || 'Mes leads'}</h1>
        </div>
        <button onClick={logout} className="text-sm text-gray-500 hover:text-primary">Déconnexion</button>
      </div>

      {leads.length === 0 ? (
        <p className="text-gray-400">Aucun lead reçu pour l'instant.</p>
      ) : (
        <div className="space-y-3">
          {leads.map((l) => (
            <div key={l.id} className="border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between gap-2 mb-1">
                <div className="font-medium">
                  {l.metier ? (METIER_LABEL[l.metier] ?? l.metier) : 'Travaux'} · {l.code_postal}
                </div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                  {STATUT_LABEL[l.statut] ?? l.statut}
                </span>
              </div>
              <div className="text-xs text-gray-400 mb-2">
                Reçu le {new Date(l.created_at).toLocaleDateString('fr-FR')}
                {l.commission != null && <> · commission {l.commission.toLocaleString('fr-FR')} €</>}
                {l.consent_retire && <span className="text-red-500"> · consentement retiré</span>}
              </div>
              {!l.consent_retire && next[l.statut] && (
                <div className="flex flex-wrap gap-2">
                  {next[l.statut].map((a) => (
                    <button key={a.statut} onClick={() => advance(l, a.statut)}
                      className="text-xs rounded-lg border border-gray-300 px-3 py-1.5 hover:bg-gray-50">
                      {a.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
