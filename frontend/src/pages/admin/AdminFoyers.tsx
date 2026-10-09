import { useState } from 'react'
import { Download, ScrollText, Search, ShieldCheck, Trash2, Users2 } from 'lucide-react'
import Depliant from '../../components/Depliant'
import {
  Attente, BTN_DANGER, BTN_PRIMAIRE, BTN_SECONDAIRE, Erreur, TitrePage, useAdminData,
} from '../../components/admin/AdminLayout'
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
      <TitrePage titre="Foyers & RGPD">
        Export (portabilité) et suppression (droit à l'effacement), à la demande du foyer.
        Chaque accès nominatif est journalisé dans le second bloc.
      </TitrePage>

      {error && <Erreur>{error}</Erreur>}

      <div className="mt-6 space-y-3">
        <Depliant
          titre="Comptes"
          ouvert
          icone={<Users2 className="h-5 w-5 shrink-0 text-primary" />}
          resume={data ? <span className="tabular-nums">{data.length} compte(s)</span> : null}
        >
          <form
            onSubmit={(e) => { e.preventDefault(); setRequete(recherche) }}
            className="flex max-w-md gap-2"
          >
            <input
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              placeholder="Rechercher par email ou prénom…"
              className="flex-1 rounded-xl border border-bord bg-white px-3 py-2 text-dark placeholder:text-dark/40"
            />
            <button type="submit" className={BTN_PRIMAIRE}>
              <Search className="h-4 w-4" /> Chercher
            </button>
          </form>

          {!data ? (
            <Attente />
          ) : data.length === 0 ? (
            <p className="text-sm text-dark/70">Aucun compte trouvé.</p>
          ) : (
            <div className="space-y-2">
              {data.map((f) => (
                <div key={f.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-bord bg-cream/50 p-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold text-ink">{f.email}</span>
                      {f.prenom && <span className="text-dark/70">{f.prenom}</span>}
                      {f.is_admin && (
                        <span className="flex items-center gap-1 rounded-full border border-sky/40 bg-sky/10 px-2 py-0.5 text-xs text-sky">
                          <ShieldCheck className="h-3 w-3" /> admin
                        </span>
                      )}
                      {!f.email_verified && (
                        <span className="rounded-full border border-terra/40 bg-terra/10 px-2 py-0.5 text-xs text-terra">
                          email non vérifié
                        </span>
                      )}
                    </div>
                    <div className="mt-1 text-xs text-dark/60">
                      Inscrit le {new Date(f.created_at).toLocaleDateString('fr-FR')} · {f.nb_conversations} conversation(s)
                      {f.consent_leads && ' · consent. mise en relation'}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button disabled={busy === f.id} onClick={() => exporter(f)} className={BTN_SECONDAIRE}>
                      <Download className="h-3.5 w-3.5" /> Exporter
                    </button>
                    <button
                      disabled={busy === f.id || f.is_admin}
                      onClick={() => supprimer(f)}
                      title={f.is_admin ? 'Un compte admin ne se supprime pas ici' : "Droit à l'effacement"}
                      className={BTN_DANGER}
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Supprimer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Depliant>

        <Depliant
          titre="Journal des accès aux données personnelles"
          aide="Contrepartie de l'accès complet : chaque consultation nominative, chaque export et chaque suppression est tracé."
          icone={<ScrollText className="h-5 w-5 shrink-0 text-sky" />}
          resume={journal ? <span className="tabular-nums">{journal.length} accès</span> : null}
        >
          <div className="-mx-1 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-dark/55">
                <tr>
                  <th className="px-2 py-2 font-semibold">Date</th>
                  <th className="px-2 py-2 font-semibold">Administrateur</th>
                  <th className="px-2 py-2 font-semibold">Action</th>
                  <th className="px-2 py-2 font-semibold">Cible</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-bord">
                {(journal ?? []).map((a, i) => (
                  <tr key={i}>
                    <td className="whitespace-nowrap px-2 py-2 tabular-nums text-dark/55">
                      {new Date(a.created_at).toLocaleString('fr-FR')}
                    </td>
                    <td className="px-2 py-2">{a.admin}</td>
                    <td className="whitespace-nowrap px-2 py-2">
                      <span className={'rounded-full px-2 py-0.5 text-xs ' + (a.action === 'suppression_rgpd' ? 'bg-primary/10 text-primary' : 'bg-cream text-dark/70')}>
                        {a.action}
                      </span>
                    </td>
                    <td className="px-2 py-2 text-dark/70">{a.cible ?? '—'}</td>
                  </tr>
                ))}
                {(!journal || journal.length === 0) && (
                  <tr><td colSpan={4} className="px-2 py-3 text-sm text-dark/60">Aucun accès enregistré.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Depliant>
      </div>
    </>
  )
}
