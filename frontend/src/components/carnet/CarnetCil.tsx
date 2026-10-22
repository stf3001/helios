import { useState } from 'react'
import { ClipboardList, Pencil, Plus, Trash2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import FieldInput from '../fiche/FieldInput'
import type { FieldSpec } from '../fiche/types'
import { messageErreur } from './Formulaires'
import { signalerMaj } from './commun'
import { dateFr } from './libelles'

/**
 * Carnet d'information du logement (carnet, lot 11) : les isolants d'un chantier, et la liste
 * « À compléter pour votre carnet d'information du logement ».
 *
 * La liste est un INDICATEUR, sans valeur légale (`services/cil.py`) : rien n'est
 * obligatoire, elle dit ce qui manque et ouvre le formulaire qui le complète.
 */

export type Isolant = {
  id: string; travaux_id: string; nature: string | null; marque_reference: string | null
  resistance_thermique: number | null; conductivite: number | null; epaisseur_mm: number | null
  surface_m2: number | null; interfaces: string | null
}
export type Manque = { objet: 'travaux' | 'equipement' | 'isolant' | 'journal'; id: string; champs: string[] }
export type BlocCil = {
  travaux_id: string; nature: string; categorie_cil: string; date_reception: string; manques: Manque[]
}

const CHAMPS_ISOLANT: FieldSpec[] = [
  { key: 'nature', label: "Nature de l'isolant", type: 'text', help: 'Laine de verre, ouate de cellulose…' },
  { key: 'marque_reference', label: 'Marque et référence', type: 'text' },
  { key: 'resistance_thermique', label: 'Résistance thermique R (m².K/W)', type: 'number', min: 0, step: 'any' },
  { key: 'conductivite', label: 'Conductivité λ (W/m.K)', type: 'number', min: 0, step: 'any' },
  { key: 'epaisseur_mm', label: 'Épaisseur (mm)', type: 'number', min: 0, step: 'any' },
  { key: 'surface_m2', label: 'Surface (m²)', type: 'number', min: 0, step: 'any' },
  { key: 'interfaces', label: 'Traitement des interfaces', type: 'textarea',
    help: 'Raccords, passages de conduits, trappes, pare-vapeur…' },
]

// Ce que le foyer lit pour chaque champ manquant.
const MANQUES: Record<string, string> = {
  description: 'la description des travaux', isolant: 'les isolants posés',
  equipement: "l'appareil posé (reliez-le à ce chantier dans Mes équipements)",
  marque: 'la marque', modele: 'le modèle', numero_serie: 'le numéro de série', puissance: 'la puissance',
  mode_evacuation: "l'évacuation des fumées", etiquette_energie: "l'étiquette énergie",
  nature: "la nature de l'isolant", marque_reference: 'la marque et la référence',
  resistance_thermique: 'la résistance thermique', conductivite: 'la conductivité', epaisseur_mm: "l'épaisseur",
  surface_m2: 'la surface', interfaces: 'le traitement des interfaces', attestation: "l'attestation d'entretien",
}
const OBJETS: Record<Manque['objet'], string> = {
  travaux: 'Chantier', equipement: 'Appareil', isolant: 'Isolant', journal: 'Entretien noté au journal',
}

function FormIsolant({ travauxId, initial, onFini }: { travauxId: string; initial: Partial<Isolant>; onFini: () => void }) {
  const { authFetch } = useAuth()
  const [d, setD] = useState<Partial<Isolant>>(initial)
  const [erreur, setErreur] = useState<string | null>(null)

  async function envoyer(e: React.FormEvent) {
    e.preventDefault()
    const corps = Object.fromEntries(CHAMPS_ISOLANT.map((s) => [s.key, (d as Record<string, unknown>)[s.key] ?? null]))
    const res = await authFetch(initial.id ? `/api/houses/me/isolants/${initial.id}` : `/api/houses/me/travaux/${travauxId}/isolants`, {
      method: initial.id ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
    })
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    signalerMaj()
    onFini()
  }
  return (
    <form onSubmit={envoyer} className="mt-2 space-y-3 rounded-lg border border-primary/30 bg-cream/60 p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        {CHAMPS_ISOLANT.map((s) => (
          <div key={s.key} className={s.type === 'textarea' ? 'sm:col-span-2' : ''}>
            <FieldInput spec={s} value={(d as Record<string, string | number | null>)[s.key] ?? null}
              onChange={(v) => setD({ ...d, [s.key]: v })} />
          </div>
        ))}
      </div>
      <p className="text-xs text-dark/60">Tout est facultatif : recopiez ce qui figure sur la facture ou la fiche du produit.</p>
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90">Enregistrer</button>
        <button type="button" onClick={onFini}
          className="rounded-lg border border-bord px-4 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">Annuler</button>
      </div>
    </form>
  )
}

/** Les isolants d'un chantier d'isolation : liste, ajout, modification. */
export function Isolants({ travauxId, isolants, ouvert, setOuvert }: {
  travauxId: string; isolants: Isolant[]
  ouvert: string | null; setOuvert: (cle: string | null) => void  // `nouveau:<travauxId>` ou l'id d'un isolant
}) {
  const { authFetch } = useAuth()
  const siens = isolants.filter((i) => i.travaux_id === travauxId)
  const nombre = (n: number | null, u: string) => (n === null ? null : `${n.toLocaleString('fr-FR')} ${u}`)
  return (
    <div className="mt-2">
      {siens.map((i) => ouvert === i.id
        ? <FormIsolant key={i.id} travauxId={travauxId} initial={i} onFini={() => setOuvert(null)} />
        : (
          <div key={i.id} className="flex items-start justify-between gap-2 rounded-md bg-sable/60 px-2.5 py-1.5 text-xs">
            <span className="min-w-0">
              <span className="block font-semibold text-ink">{i.nature || 'Isolant'}{i.marque_reference ? ` · ${i.marque_reference}` : ''}</span>
              <span className="block text-dark/60">
                {[nombre(i.resistance_thermique, 'm².K/W'), nombre(i.epaisseur_mm, 'mm'), nombre(i.surface_m2, 'm²')].filter(Boolean).join(' · ')}
              </span>
            </span>
            <span className="flex shrink-0 gap-1">
              <button onClick={() => setOuvert(i.id)} aria-label="Modifier l'isolant" className="rounded p-1 text-dark/50 hover:text-primary"><Pencil className="h-3.5 w-3.5" /></button>
              <button aria-label="Supprimer l'isolant" className="rounded p-1 text-dark/50 hover:text-terra"
                onClick={async () => { if (confirm("Supprimer cet isolant ?")) { await authFetch(`/api/houses/me/isolants/${i.id}`, { method: 'DELETE' }); signalerMaj() } }}>
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </span>
          </div>
        ))}
      {ouvert === `nouveau:${travauxId}`
        ? <FormIsolant travauxId={travauxId} initial={{}} onFini={() => setOuvert(null)} />
        : (
          <button onClick={() => setOuvert(`nouveau:${travauxId}`)}
            className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">
            <Plus className="h-3.5 w-3.5" /> Ajouter un isolant
          </button>
        )}
    </div>
  )
}

/** « À compléter pour votre carnet d'information du logement ». */
export function ACompleter({ blocs, onCompleter }: { blocs: BlocCil[]; onCompleter: (m: Manque, bloc: BlocCil) => void }) {
  if (!blocs.length) return null
  const ouverts = blocs.filter((b) => b.manques.length)
  return (
    <div className="mb-4 rounded-lg border border-primary/30 bg-cream/60 p-3">
      <p className="flex items-center gap-2 text-sm font-semibold text-ink">
        <ClipboardList className="h-4 w-4 text-primary" /> À compléter pour votre carnet d'information du logement
      </p>
      <p className="mb-2 text-xs text-dark/60">
        Pour vos travaux de rénovation depuis 2023. Rien n'est obligatoire ici : c'est ce qui manque à votre dossier,
        sans valeur légale.
      </p>
      {ouverts.length === 0 ? (
        <p className="text-sm text-leaf">Rien ne manque pour vos {blocs.length} chantier{blocs.length > 1 ? 's' : ''} concerné{blocs.length > 1 ? 's' : ''}.</p>
      ) : (
        <ul className="space-y-2">
          {ouverts.map((b) => (
            <li key={b.travaux_id}>
              <span className="block text-sm text-ink">{b.nature} <span className="text-xs text-dark/50">· réceptionné le {dateFr(b.date_reception)}</span></span>
              <ul className="mt-1 space-y-1">
                {b.manques.map((m, i) => (
                  <li key={`${m.id}-${i}`} className="flex items-start justify-between gap-2 text-xs text-dark/70">
                    <span>{OBJETS[m.objet]} : {m.champs.map((c) => MANQUES[c] ?? c).join(', ')}</span>
                    <button onClick={() => onCompleter(m, b)} className="shrink-0 font-semibold text-primary hover:underline">Compléter</button>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
