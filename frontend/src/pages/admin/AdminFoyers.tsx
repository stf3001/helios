import { useState } from 'react'
import { Download, Search, ShieldCheck, Trash2 } from 'lucide-react'
import { Section, useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

interface Foyer {
  id: string
  email: string
  prenom: string | null
  created_at: string
  email_verified: boolean
  is_admin: boolean
  consent_leads: boolean
  nb_conversations: number
}

interface Acces {
  admin: string
  action: string
  cible: string | null
  created_at: string
}

export default function AdminFoyers() {
  useTitle('Back-office — Foyers & RGPD')
  const { authFetch } = useAuth()
  const [recherche, setRecherche] = useState('')
  const [requete, setRequete] = useState('')
  const { data, error, reload } = useAdminData<Foyer[]>(
    `/api/admin/foyers${requete ? `?q=${encodeURIComponent(requete)}` : ''}`,
  )
  const { data: journal, reload: reloadJournal } = useAdminData<Acces[]>('/api/admin/journal-acces?limit=30')
  const [busy, setBusy] = useState<string | null>(null)

  async function exporter(f: Foyer) {
    setBusy(f.id)
    try {
      const r = await authFetch(`/api/admin/foyers/${f.id}/export`)
      const data = await r.json()
      // Téléchargement local : l'export ne transite par aucun service tiers.
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `export-rgpd-${f.email}.json`
      a.click()
      URL.revokeObjectURL(url)
      reloadJournal()
    } finally {
      setBusy(null)
    }
  }

  async function supprimer(f: Foyer) {
    // Double confirmation : l'action est irréversible et efface aussi fiches, études et documents.
    if (!confirm(`Supprimer définitivement le compte ${f.email} ?\n\nToutes ses données (fiche, études, audits, documents, conversations) seront effacées. Action irréversible.`)) return
    if (prompt(`Pour confirmer, tapez l'email exact du compte à supprimer :`) !== f.email) {
      alert('Email non concordant — suppression annulée.')
      return
    }
    setBusy(f.id)
    try {
      const r = await authFetch(`/api/admin/foyers/${f.id}`, { method: 'DELETE' })
      if (!r.ok && r.status !== 204) {
        const body = await r.json().catch(() => null)
        alert(body?.detail ?? `Erreur ${r.status}`)
        return
      }
      reload()
      reloadJournal()
    } finally {
      setBusy(null)
    }
  }

  return (
    <>
      <h1 className="text-xl font-semibold text-white">Foyers & RGPD</h1>
      <p className="text-sm text-slate-500 mt-1">
        Export (portabilité) et suppression (droit à l'effacement), à la demande du foyer.
        Chaque accès nominatif est journalisé plus bas.
      </p>

      <form
        onSubmit={(e) => { e.preventDefault(); setRequete(recherche) }}
        className="mt-5 flex gap-2 max-w-md"
      >
        <input
          value={recherche}
          onChange={(e) => setRecherche(e.target.value)}
          placeholder="Rechercher par email ou prénom…"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600"
        />
        <button type="submit" className="flex items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600">
          <Search className="w-4 h-4" /> Chercher
        </button>
      </form>

      {error && <p className="mt-4 text-rose-400">{error}</p>}

      {data && (
        <div className="mt-5 space-y-2">
          {data.map((f) => (
            <div key={f.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4 flex flex-wrap items-center gap-x-4 gap-y-2">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-white">{f.email}</span>
                  {f.prenom && <span className="text-slate-400">{f.prenom}</span>}
                  {f.is_admin && (
                    <span className="flex items-center gap-1 rounded bg-sky-950 px-1.5 py-0.5 text-xs text-sky-300">
                      <ShieldCheck className="w-3 h-3" /> admin
                    </span>
                  )}
                  {!f.email_verified && (
                    <span className="rounded bg-amber-950 px-1.5 py-0.5 text-xs text-amber-300">email non vérifié</span>
                  )}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Inscrit le {new Date(f.created_at).toLocaleDateString('fr-FR')} · {f.nb_conversations} conversation(s)
                  {f.consent_leads && ' · consent. mise en relation'}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  disabled={busy === f.id}
                  onClick={() => exporter(f)}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" /> Exporter
                </button>
                <button
                  disabled={busy === f.id || f.is_admin}
                  onClick={() => supprimer(f)}
                  title={f.is_admin ? 'Un compte admin ne se supprime pas ici' : 'Droit à l’effacement'}
                  className="flex items-center gap-1.5 rounded-lg border border-rose-900/60 px-3 py-1.5 text-sm text-rose-400 hover:bg-rose-950/40 disabled:opacity-30"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Supprimer
                </button>
              </div>
            </div>
          ))}
          {data.length === 0 && <p className="text-sm text-slate-500">Aucun compte trouvé.</p>}
        </div>
      )}

      <Section title="Journal des accès aux données personnelles">
        <p className="text-xs text-slate-500 mb-3">
          Contrepartie de l'accès complet : chaque consultation nominative est tracée.
        </p>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">Administrateur</th>
                <th className="px-4 py-2 font-medium">Action</th>
                <th className="px-4 py-2 font-medium">Cible</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-900/50 text-slate-300">
              {(journal ?? []).map((a, i) => (
                <tr key={i}>
                  <td className="whitespace-nowrap px-4 py-2 tabular-nums text-slate-500">
                    {new Date(a.created_at).toLocaleString('fr-FR')}
                  </td>
                  <td className="px-4 py-2">{a.admin}</td>
                  <td className="whitespace-nowrap px-4 py-2">
                    <span className={'rounded px-1.5 py-0.5 text-xs ' + (a.action === 'suppression_rgpd' ? 'bg-rose-950 text-rose-300' : 'bg-slate-800 text-slate-400')}>
                      {a.action}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-slate-400">{a.cible ?? '—'}</td>
                </tr>
              ))}
              {(!journal || journal.length === 0) && (
                <tr><td colSpan={4} className="px-4 py-3 text-sm text-slate-500">Aucun accès enregistré.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Section>
    </>
  )
}
