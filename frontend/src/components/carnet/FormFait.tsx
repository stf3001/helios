import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import FieldInput from '../fiche/FieldInput'
import type { Draft, FieldSpec } from '../fiche/types'
import { messageErreur, type Doc } from './Formulaires'
import { aujourdhui, signalerMaj } from './commun'

/** « C'est fait » : la date, qui l'a fait, le coût, un document déjà déposé. Rien d'autre. */
export default function FormFait({ tacheId, equipementId, documents, onFini }: {
  tacheId: string; equipementId: string | null; documents: Doc[]; onFini: () => void
}) {
  const { authFetch } = useAuth()
  const [draft, setDraft] = useState<Draft>({ date: aujourdhui(), qui: 'moi' })
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  const specs: FieldSpec[] = [
    { key: 'date', label: 'Fait le', type: 'date' },
    { key: 'qui', label: 'Par', type: 'select', options: [{ value: 'moi', label: 'Moi' }, { value: 'pro', label: 'Un professionnel' }] },
    ...(draft.qui === 'pro' ? [{ key: 'nom_pro', label: 'Nom du professionnel', type: 'text' as const }] : []),
    { key: 'cout_eur', label: 'Coût TTC (€), facultatif', type: 'number', min: 0, step: 'any' },
    ...(documents.length ? [{ key: 'document_id', label: 'Justificatif (dans vos papiers)', type: 'select' as const,
      options: documents.map((d) => ({ value: d.id, label: d.filename })) }] : []),
  ]

  async function envoyer(e: React.FormEvent) {
    e.preventDefault()
    if (!draft.date || String(draft.date) > aujourdhui()) { setErreur('Indiquez une date passée ou celle du jour.'); return }
    setEnvoi(true)
    const res = await authFetch(`/api/houses/me/entretien/${tacheId}/fait`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        equipement_id: equipementId, date: draft.date,
        intervenant: draft.qui === 'pro' ? (draft.nom_pro || 'Un professionnel') : 'moi',
        cout_eur: draft.cout_eur ?? null, document_id: draft.document_id || null,
      }),
    })
    setEnvoi(false)
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    signalerMaj()
    onFini()
  }

  return (
    <form onSubmit={envoyer} className="mt-2 space-y-3 rounded-lg border border-primary/40 bg-cream/60 p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        {specs.map((s) => (
          <FieldInput key={s.key} spec={s} value={draft[s.key]} onChange={(v) => setDraft((d) => ({ ...d, [s.key]: v }))} />
        ))}
      </div>
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={envoi}
          className="rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50">
          {envoi ? 'Enregistrement…' : 'Inscrire au journal'}
        </button>
        <button type="button" onClick={onFini}
          className="rounded-lg border border-bord px-3.5 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">
          Annuler
        </button>
      </div>
    </form>
  )
}
