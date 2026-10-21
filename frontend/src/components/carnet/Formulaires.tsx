import { useState } from 'react'
import FieldInput from '../fiche/FieldInput'
import type { Draft, FieldSpec, FieldValue } from '../fiche/types'
import { CATEGORIES, TYPES, UNITES } from './libelles'

export type Equipement = {
  id: string; categorie: string; type: string; marque: string | null; modele: string | null
  numero_serie: string | null; puissance: number | null; unite: string | null
  date_pose: string | null; annee_pose: number | null; installateur: string | null
  garantie_fabricant_fin: string | null; contrat_entretien: boolean | null
  contrat_prestataire: string | null; travaux_id: string | null; origine_fiche: string | null
  en_service: boolean; note: string | null; age_ans: number | null; age_statut: 'calcule' | 'suppose' | null
  date_pose_retenue: string | null
}

export type Garantie = {
  code: string; libelle: string; duree_ans?: number; fin: string; statut: 'en_cours' | 'bientot' | 'expiree'
}

export type Chantier = {
  id: string; nature: string; entreprise: string | null; date_reception: string | null
  montant_ttc: number | null; facture_document_id: string | null
  attestation_assurance_document_id: string | null; note: string | null; garanties: Garantie[]
}

export type Doc = { id: string; type: string; filename: string }

/** FastAPI renvoie `detail` en texte OU en liste (erreur de validation) : lire les deux. */
export async function messageErreur(res: Response): Promise<string> {
  const corps = await res.json().catch(() => null)
  const d = corps?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) return d.map((e) => e.msg).join(' · ')
  return 'Enregistrement impossible, réessayez.'
}

function Champs({ specs, draft, set }: { specs: FieldSpec[]; draft: Draft; set: (k: string, v: FieldValue) => void }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {specs.map((s) => (
        <div key={s.key} className={s.type === 'textarea' ? 'sm:col-span-2' : ''}>
          <FieldInput spec={s} value={draft[s.key]} onChange={(v) => set(s.key, v)} />
        </div>
      ))}
    </div>
  )
}

function Boutons({ envoi, onAnnuler, erreur }: { envoi: boolean; onAnnuler: () => void; erreur: string | null }) {
  return (
    <>
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={envoi}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50">
          {envoi ? 'Enregistrement…' : 'Enregistrer'}
        </button>
        <button type="button" onClick={onAnnuler}
          className="rounded-lg border border-bord px-4 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">
          Annuler
        </button>
      </div>
    </>
  )
}

/** Ajout ou modification d'un équipement. `initial.id` absent = création. */
export function FormEquipement({ initial, chantiers, enregistrer, onAnnuler }: {
  initial: Draft
  chantiers: Chantier[]
  enregistrer: (draft: Draft) => Promise<string | null>
  onAnnuler: () => void
}) {
  const [draft, setDraft] = useState<Draft>(initial)
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const categorie = (draft.categorie as string) || 'chauffage'

  function set(k: string, v: FieldValue) {
    setDraft((d) => {
      const suivant = { ...d, [k]: v }
      // Le type appartient à sa catégorie : changer l'une remet l'autre à choisir.
      if (k === 'categorie' && !TYPES[v as string]?.some((t) => t.value === d.type)) suivant.type = null
      return suivant
    })
  }

  const specs: FieldSpec[] = [
    { key: 'categorie', label: 'Catégorie', type: 'select', options: CATEGORIES },
    { key: 'type', label: 'Type', type: 'select', options: TYPES[categorie] ?? [] },
    { key: 'marque', label: 'Marque', type: 'text' },
    { key: 'modele', label: 'Modèle', type: 'text' },
    { key: 'puissance', label: 'Puissance ou capacité', type: 'number', min: 0, step: 'any' },
    { key: 'unite', label: 'Unité', type: 'select', options: UNITES },
    { key: 'date_pose', label: 'Date de pose', type: 'date', help: 'Si vous la connaissez' },
    { key: 'annee_pose', label: 'Sinon, année de pose', type: 'number', min: 1900, max: 2100 },
    { key: 'installateur', label: 'Installateur', type: 'text' },
    { key: 'garantie_fabricant_fin', label: 'Fin de la garantie fabricant', type: 'date' },
    { key: 'contrat_entretien', label: "Contrat d'entretien ?", type: 'boolean' },
    { key: 'contrat_prestataire', label: 'Prestataire du contrat', type: 'text' },
    { key: 'numero_serie', label: 'Numéro de série', type: 'text', help: 'Visible par vous seul, jamais transmis à Helios' },
    ...(chantiers.length ? [{ key: 'travaux_id', label: 'Posé lors du chantier', type: 'select' as const,
      options: chantiers.map((c) => ({ value: c.id, label: c.nature })) }] : []),
    { key: 'note', label: 'Note', type: 'textarea', help: 'Pour vous seul, jamais transmise à Helios' },
  ]

  async function soumettre(e: React.FormEvent) {
    e.preventDefault()
    if (!draft.type) { setErreur('Choisissez le type de l’équipement.'); return }
    setEnvoi(true)
    setErreur(await enregistrer({ ...draft, categorie }))
    setEnvoi(false)
  }

  return (
    <form onSubmit={soumettre} className="space-y-4 rounded-xl border border-primary/40 bg-cream/60 p-4">
      <Champs specs={specs} draft={{ ...draft, categorie }} set={set} />
      <Boutons envoi={envoi} onAnnuler={onAnnuler} erreur={erreur} />
    </form>
  )
}

export function FormChantier({ initial, documents, enregistrer, onAnnuler }: {
  initial: Draft
  documents: Doc[]
  enregistrer: (draft: Draft) => Promise<string | null>
  onAnnuler: () => void
}) {
  const [draft, setDraft] = useState<Draft>(initial)
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const optionsDocs = documents.map((d) => ({ value: d.id, label: d.filename }))

  const specs: FieldSpec[] = [
    { key: 'nature', label: 'Nature des travaux', type: 'text', help: 'Par exemple : isolation des combles' },
    { key: 'entreprise', label: 'Entreprise', type: 'text' },
    { key: 'date_reception', label: 'Date de réception', type: 'date',
      help: 'Celle du procès-verbal. Sans elle, pas de garantie calculée.' },
    { key: 'montant_ttc', label: 'Montant TTC (€)', type: 'number', min: 0, step: 'any' },
    ...(optionsDocs.length ? [
      { key: 'facture_document_id', label: 'Facture (dans vos papiers)', type: 'select' as const, options: optionsDocs },
      { key: 'attestation_assurance_document_id', label: "Attestation d'assurance", type: 'select' as const, options: optionsDocs },
    ] : []),
    { key: 'note', label: 'Note', type: 'textarea' },
  ]

  async function soumettre(e: React.FormEvent) {
    e.preventDefault()
    if (!draft.nature) { setErreur('Indiquez la nature des travaux.'); return }
    setEnvoi(true)
    setErreur(await enregistrer(draft))
    setEnvoi(false)
  }

  return (
    <form onSubmit={soumettre} className="space-y-4 rounded-xl border border-primary/40 bg-cream/60 p-4">
      <Champs specs={specs} draft={draft} set={(k, v) => setDraft((d) => ({ ...d, [k]: v }))} />
      <Boutons envoi={envoi} onAnnuler={onAnnuler} erreur={erreur} />
    </form>
  )
}
