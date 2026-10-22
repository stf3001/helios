import { useState } from 'react'
import { Check } from 'lucide-react'
import FieldInput from './FieldInput'
import Depliant from '../Depliant'
import type { Draft, FieldSpec, FieldValue } from './types'

/** Un champ compte comme rempli dès qu'il porte autre chose que le vide.
 *  `false` compte : répondre « non » à « résidence principale ? » est une réponse. */
function estRempli(v: FieldValue | undefined): boolean {
  if (v === undefined || v === null || v === '') return false
  if (Array.isArray(v)) return v.length > 0
  return true
}

export default function BlockCard({
  title,
  weightLabel,
  pct,
  fields,
  draft,
  onChange,
  onSave,
  icone,
  verrouilles,
  id,
  ouvert,
}: {
  title: string
  weightLabel: string
  pct?: number
  fields: FieldSpec[]
  draft: Draft
  onChange: (key: string, value: FieldValue) => void
  onSave: (keys: string[]) => Promise<void>
  icone?: React.ReactNode
  /** Carnet, lot 7 : les champs de ce bloc que tient un équipement — affichés en lecture. */
  verrouilles?: string[]
  /** Pré-audit lot 7 : une ancre (`/mon-espace#energie`) qui ouvre ce bloc. */
  id?: string
  ouvert?: boolean
}) {
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Un champ dont les choix suivent un autre (l'unité suit l'énergie) : ses choix du moment.
  const choix = (f: FieldSpec) => (f.type === 'select' && f.optionsSelon
    ? f.optionsSelon.options[String(draft[f.optionsSelon.key] ?? '')] ?? [] : null)
  // Un champ conditionnel masqué ne compte ni dans l'affichage ni dans « x / n ».
  const visibles = fields
    .filter((f) => !f.si || draft[f.si.key] === f.si.vaut)
    .filter((f) => choix(f)?.length !== 0)
    .map((f) => { const c = choix(f); return c && f.type === 'select' ? { ...f, options: c } : f })

  // Changer l'énergie vide l'unité qui ne lui va plus (jamais une unité devinée à sa place).
  function changer(key: string, value: FieldValue) {
    onChange(key, value)
    for (const f of fields) {
      if (f.type !== 'select' || f.optionsSelon?.key !== key || draft[f.key] == null) continue
      const ok = (f.optionsSelon.options[String(value ?? '')] ?? []).some((o) => o.value === draft[f.key])
      if (!ok) onChange(f.key, null)
    }
  }
  const remplis = visibles.filter((f) => estRempli(draft[f.key])).length
  const complet = remplis === visibles.length

  async function handleSave() {
    setSaving(true)
    setSaved(false)
    try {
      await onSave(fields.map((f) => f.key))
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } finally {
      setSaving(false)
    }
  }

  /* REPLIÉ PAR DÉFAUT (demande de Stéphane, 06/10/2026). La fiche dépliait ses six blocs
     d'un coup, soit 46 champs à faire défiler avant d'avoir une idée de ce qui manquait.
     Le résumé est ce qui rend le pliage utile : fermé, le bloc dit déjà où il en est, donc
     on ouvre celui qu'on veut remplir au lieu de les ouvrir tous pour chercher. */
  const resume = (
    <span className="flex items-center gap-2">
      {complet ? (
        <span className="inline-flex items-center gap-1 text-leaf">
          <Check className="h-4 w-4" aria-hidden="true" /> complet
        </span>
      ) : (
        <span className={remplis === 0 ? 'text-dark/40' : undefined}>
          {remplis} / {visibles.length}
        </span>
      )}
      <span className="hidden sm:inline text-dark/40">·</span>
      <span className="hidden sm:inline text-dark/40">{weightLabel}</span>
    </span>
  )

  return (
    <div id={id} className="scroll-mt-20">
    <Depliant titre={title} resume={resume} icone={icone} ouvert={ouvert}>
      {pct !== undefined && (
        <div className="h-1.5 rounded-full bg-bord overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        {visibles.map((f) => (
          <FieldInput key={f.key} spec={f} value={draft[f.key]} onChange={(v) => changer(f.key, v)}
            verrouille={verrouilles?.includes(f.key)} />
        ))}
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-lg bg-primary text-white text-sm font-semibold px-4 py-2 hover:opacity-90 disabled:opacity-50"
        >
          {saving ? 'Enregistrement…' : 'Enregistrer ce bloc'}
        </button>
        {saved && (
          <span className="inline-flex items-center gap-1.5 text-sm text-leaf">
            <Check className="w-4 h-4" aria-hidden="true" /> Enregistré
          </span>
        )}
      </div>
    </Depliant>
    </div>
  )
}
