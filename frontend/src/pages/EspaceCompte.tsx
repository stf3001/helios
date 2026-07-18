import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, ShieldCheck, Trash2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function EspaceCompte() {
  const { user, authFetch, logout } = useAuth()
  const navigate = useNavigate()
  const [consentLeads, setConsentLeads] = useState<boolean | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    authFetch('/api/account/consents')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setConsentLeads(d.consent_leads))
  }, [authFetch])

  async function exportData() {
    const res = await authFetch('/api/account/export')
    if (!res.ok) return
    const data = await res.json()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'mes-donnees-helios.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  async function toggleConsent(value: boolean) {
    setConsentLeads(value)
    await authFetch('/api/account/consents', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consent_leads: value }),
    })
  }

  async function deleteAccount() {
    if (!confirm('Supprimer définitivement votre compte et toutes vos données ? Cette action est irréversible.')) return
    setBusy(true)
    const res = await authFetch('/api/account', { method: 'DELETE' })
    if (res.ok) {
      await logout()
      navigate('/')
    } else {
      setBusy(false)
      alert('Suppression impossible, réessayez.')
    }
  }

  return (
    <section className="max-w-[700px] mx-auto px-4 py-12">
      <h1 className="text-2xl font-bold mb-2">Mon compte</h1>
      <p className="text-gray-600 mb-8">{user?.email}</p>

      {/* Consentements */}
      <div className="border border-gray-200 rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <ShieldCheck className="w-5 h-5 text-primary" />
          <h2 className="font-semibold">Mes consentements</h2>
        </div>
        <label className="flex items-start gap-3 text-sm text-gray-700">
          <input type="checkbox" checked={consentLeads ?? false}
            onChange={(e) => toggleConsent(e.target.checked)} className="mt-1" />
          <span>
            J'accepte d'être mis en relation avec des partenaires pour mes projets de travaux.
            Vous pouvez retirer ce consentement à tout moment ; il n'est jamais requis pour utiliser Helios.
          </span>
        </label>
      </div>

      {/* Export RGPD */}
      <div className="border border-gray-200 rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Download className="w-5 h-5 text-primary" />
          <h2 className="font-semibold">Mes données</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Téléchargez l'ensemble des données que HELIOS détient sur vous (portabilité RGPD).
        </p>
        <button onClick={exportData}
          className="rounded-xl border border-primary text-primary text-sm font-semibold px-4 py-2 hover:bg-primary/5">
          Exporter mes données (JSON)
        </button>
      </div>

      {/* Suppression */}
      <div className="border border-red-200 bg-red-50 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-2">
          <Trash2 className="w-5 h-5 text-red-600" />
          <h2 className="font-semibold text-red-700">Supprimer mon compte</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Efface définitivement votre compte, votre fiche maison, vos audits, conversations et documents.
          Cette action est irréversible.
        </p>
        <button onClick={deleteAccount} disabled={busy}
          className="rounded-xl bg-red-600 text-white text-sm font-semibold px-4 py-2 hover:opacity-90 disabled:opacity-50">
          {busy ? 'Suppression…' : 'Supprimer définitivement mon compte'}
        </button>
      </div>
    </section>
  )
}
