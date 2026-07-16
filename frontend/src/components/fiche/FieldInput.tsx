import type { FieldSpec, FieldValue } from './types'

const inputClass =
  'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'

export default function FieldInput({
  spec,
  value,
  onChange,
}: {
  spec: FieldSpec
  value: FieldValue
  onChange: (value: FieldValue) => void
}) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{spec.label}</label>

      {spec.type === 'select' && (
        <select
          className={inputClass}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value || null)}
        >
          <option value="">— non renseigné —</option>
          {spec.options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      )}

      {spec.type === 'multiselect' && (
        <div className="flex flex-wrap gap-2">
          {spec.options.map((o) => {
            const selected = Array.isArray(value) && value.includes(o.value)
            return (
              <button
                type="button"
                key={o.value}
                onClick={() => {
                  const current = Array.isArray(value) ? value : []
                  onChange(
                    selected ? current.filter((v) => v !== o.value) : [...current, o.value]
                  )
                }}
                className={
                  'px-3 py-1.5 rounded-full text-sm border transition-colors ' +
                  (selected
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-primary')
                }
              >
                {o.label}
              </button>
            )
          })}
        </div>
      )}

      {spec.type === 'number' && (
        <input
          type="number"
          className={inputClass}
          min={spec.min}
          max={spec.max}
          value={value === null || value === undefined ? '' : (value as number)}
          onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
        />
      )}

      {spec.type === 'boolean' && (
        <select
          className={inputClass}
          value={value === null || value === undefined ? '' : String(value)}
          onChange={(e) => onChange(e.target.value === '' ? null : e.target.value === 'true')}
        >
          <option value="">— non renseigné —</option>
          <option value="true">Oui</option>
          <option value="false">Non</option>
        </select>
      )}

      {spec.type === 'text' && (
        <input
          type="text"
          className={inputClass}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value || null)}
        />
      )}

      {spec.type === 'textarea' && (
        <textarea
          className={inputClass}
          rows={3}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value || null)}
        />
      )}

      {spec.help && <p className="text-xs text-gray-500 mt-1">{spec.help}</p>}
    </div>
  )
}
