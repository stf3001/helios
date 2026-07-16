import { useState } from 'react'
import FieldInput from './FieldInput'
import type { Draft, FieldSpec, FieldValue } from './types'

export default function BlockCard({
  title,
  weightLabel,
  pct,
  fields,
  draft,
  onChange,
  onSave,
}: {
  title: string
  weightLabel: string
  pct?: number
  fields: FieldSpec[]
  draft: Draft
  onChange: (key: string, value: FieldValue) => void
  onSave: (keys: string[]) => Promise<void>
}) {
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

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

  return (
    <div className="bg-gray-50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-semibold">{title}</h2>
        <span className="text-xs text-gray-500">{weightLabel}</span>
      </div>
      {pct !== undefined && (
        <div className="h-1.5 rounded-full bg-gray-200 mb-5 overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        {fields.map((f) => (
          <FieldInput key={f.key} spec={f} value={draft[f.key]} onChange={(v) => onChange(f.key, v)} />
        ))}
      </div>
      <div className="flex items-center gap-3 mt-5">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-xl bg-primary text-white text-sm font-semibold px-4 py-2 hover:opacity-90 disabled:opacity-50"
        >
          {saving ? 'Enregistrement…' : 'Enregistrer ce bloc'}
        </button>
        {saved && <span className="text-sm text-green-600">Enregistré ✓</span>}
      </div>
    </div>
  )
}
