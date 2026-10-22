import { Lock } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { FieldSpec, FieldValue } from './types'

/** Où se modifie un champ que fixe un équipement du carnet (lot 7). */
export const LIEN_EQUIPEMENTS = '/espace?aller=mes-equipements'

/** La valeur telle que le foyer la lit : le libellé de l'option, « Oui » / « Non »… */
function valeurLue(spec: FieldSpec, value: FieldValue): string {
  if (value === null || value === undefined || value === '') return 'non renseigné'
  if (typeof value === 'boolean') return value ? 'Oui' : 'Non'
  if (spec.type === 'select') return spec.options.find((o) => o.value === value)?.label ?? String(value)
  return String(value)
}

const inputClass =
  'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary'

export default function FieldInput({
  spec,
  value,
  onChange,
  verrouille,
}: {
  spec: FieldSpec
  value: FieldValue
  onChange: (value: FieldValue) => void
  /** Carnet, lot 7 : ce champ est une COPIE de l'équipement qui le fixe. En lecture, avec
   *  le lien vers la seule saisie qui vaille — le serveur refuserait de le changer ici. */
  verrouille?: boolean
}) {
  if (verrouille) {
    return (
      <div>
        <label className="block text-sm font-medium mb-1">{spec.label}</label>
        <p className="flex items-center gap-2 rounded-lg border border-bord bg-cream px-3 py-2 text-sm text-ink">
          <Lock className="h-3.5 w-3.5 shrink-0 text-dark/40" aria-hidden="true" />
          <span className="min-w-0">{valeurLue(spec, value)}</span>
        </p>
        <p className="mt-1 text-xs text-dark/60">
          Vient de vos équipements.{' '}
          <Link to={LIEN_EQUIPEMENTS} className="font-semibold text-primary hover:underline">
            Modifier dans Mes équipements
          </Link>
        </p>
      </div>
    )
  }

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
          step={spec.step}
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

      {spec.type === 'date' && (
        <input
          type="date"
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
