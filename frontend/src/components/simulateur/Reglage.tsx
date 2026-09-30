/**
 * Le réglage d'un équipement : panneau flottant sur grand écran, feuille qui glisse depuis
 * le bas sur petit écran. Dans les deux cas il ne recouvre JAMAIS les indicateurs — on doit
 * voir bouger l'autonomie et la facture pendant qu'on règle.
 *
 * D'où l'ancrage EN BAS à droite à partir de `xl` : c'est là que se trouve la carte des
 * indicateurs, en haut à droite. Un panneau posé en haut la masquerait. En dessous de `xl`,
 * les indicateurs sont en bandeau collé en haut, et la feuille monte du bas sans les
 * atteindre. Le seuil est le même que celui de la mise en page du simulateur.
 */

import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

interface Props {
  titre: string
  ouvert: boolean
  onFermer: () => void
  children: ReactNode
}

export function Feuille({ titre, ouvert, onFermer, children }: Props) {
  const panneau = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ouvert) return
    const echap = (e: KeyboardEvent) => { if (e.key === 'Escape') onFermer() }
    window.addEventListener('keydown', echap)
    panneau.current?.focus()
    return () => window.removeEventListener('keydown', echap)
  }, [ouvert, onFermer])

  if (!ouvert) return null

  return (
    <>
      {/* Voile sur petit écran seulement : plus haut, le panneau cohabite avec la scène. */}
      <div className="fixed inset-0 z-30 bg-black/30 xl:hidden" onClick={onFermer} aria-hidden="true" />
      <div
        ref={panneau}
        tabIndex={-1}
        role="dialog"
        aria-modal="false"
        aria-label={titre}
        className="feuille-reglage fixed inset-x-0 bottom-0 z-40 max-h-[70vh] overflow-y-auto rounded-t-2xl
          border-t border-ink/10 bg-white p-4 shadow-question outline-none
          xl:inset-x-auto xl:bottom-4 xl:right-4 xl:top-auto xl:max-h-[min(60vh,32rem)] xl:w-[22rem]
          xl:rounded-2xl xl:border"
      >
        <div className="mb-3 flex items-center justify-between gap-4">
          <h3 className="font-display text-lg font-bold text-ink">{titre}</h3>
          <button type="button" onClick={onFermer} aria-label="Fermer le réglage"
            className="rounded-full p-1.5 text-dark/60 hover:bg-cream hover:text-ink">
            <X size={20} />
          </button>
        </div>
        <div className="space-y-4">{children}</div>
      </div>
    </>
  )
}

export function Nombre({
  label, valeur, min = 0, max = 99, pas = 1, suffixe, onChange, aide,
}: {
  label: string; valeur: number; min?: number; max?: number; pas?: number
  suffixe?: string; onChange: (v: number) => void; aide?: string
}) {
  const borner = (v: number) => Math.max(min, Math.min(max, v))
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <label className="font-semibold text-ink">{label}</label>
        <div className="flex items-center gap-1">
          <button type="button" aria-label={`Diminuer ${label}`} onClick={() => onChange(borner(valeur - pas))}
            disabled={valeur <= min}
            className="h-9 w-9 rounded-full border border-ink/20 text-lg font-bold text-ink
              disabled:opacity-30 hover:border-primary hover:text-primary">−</button>
          <span className="min-w-[4.5rem] text-center font-bold text-ink" aria-live="polite">
            {valeur}{suffixe ? ` ${suffixe}` : ''}
          </span>
          <button type="button" aria-label={`Augmenter ${label}`} onClick={() => onChange(borner(valeur + pas))}
            disabled={valeur >= max}
            className="h-9 w-9 rounded-full border border-ink/20 text-lg font-bold text-ink
              disabled:opacity-30 hover:border-primary hover:text-primary">+</button>
        </div>
      </div>
      {aide && <p className="mt-1 text-sm text-dark/60">{aide}</p>}
    </div>
  )
}

export function Choix<T extends string>({
  label, valeur, options, onChange, aide,
}: {
  label: string; valeur: T; options: { value: T; label: string }[]
  onChange: (v: T) => void; aide?: string
}) {
  const id = `choix-${label.replace(/\s+/g, '-').toLowerCase()}`
  return (
    <div>
      <label htmlFor={id} className="block font-semibold text-ink">{label}</label>
      <select id={id} value={valeur} onChange={(e) => onChange(e.target.value as T)}
        className="mt-1 w-full rounded-lg border border-ink/20 bg-white px-3 py-2 text-ink
          focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30">
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      {aide && <p className="mt-1 text-sm text-dark/60">{aide}</p>}
    </div>
  )
}

export function Bascule({
  label, actif, onChange, aide,
}: { label: string; actif: boolean; onChange: (v: boolean) => void; aide?: string }) {
  return (
    <div>
      <label className="flex cursor-pointer items-start gap-3">
        <input type="checkbox" checked={actif} onChange={(e) => onChange(e.target.checked)}
          className="mt-1 h-5 w-5 shrink-0 rounded border-ink/30 text-primary
            focus:ring-2 focus:ring-primary/40" />
        <span>
          <span className="block font-semibold text-ink">{label}</span>
          {aide && <span className="block text-sm text-dark/60">{aide}</span>}
        </span>
      </label>
    </div>
  )
}

/**
 * Un champ libre où l'on tape un nombre.
 *
 * `min` / `max` / `decimal` reprennent les bornes du schéma de l'API. Elles sont
 * appliquées À LA SORTIE DU CHAMP, jamais à la frappe : ramener la valeur dans
 * les bornes à chaque touche rendrait « 12000 » impossible à écrire, puisque le
 * « 1 » seul serait aussitôt remonté au minimum.
 *
 * Sans ces bornes (avant le 30/09/2026), un zéro laissé dans « Puissance de la
 * pompe » partait tel quel, l'API le refusait, et l'écran affichait « Le calcul
 * n'a pas abouti » sans dire lequel des champs remplis était en cause.
 */
export function Champ({
  label, valeur, onChange, suffixe, placeholder, aide, type = 'number',
  min, max, decimal = false,
}: {
  label: string; valeur: number | null; onChange: (v: number | null) => void
  suffixe?: string; placeholder?: string; aide?: string; type?: string
  min?: number; max?: number; decimal?: boolean
}) {
  const id = `champ-${label.replace(/\s+/g, '-').toLowerCase()}`

  /** À la sortie du champ : on arrondit et on ramène dans les bornes. */
  function ranger(brut: number | null): number | null {
    if (brut === null || Number.isNaN(brut)) return null
    let v = decimal ? Math.round(brut * 10) / 10 : Math.round(brut)
    if (min !== undefined) v = Math.max(min, v)
    if (max !== undefined) v = Math.min(max, v)
    return v
  }

  return (
    <div>
      <label htmlFor={id} className="block font-semibold text-ink">{label}</label>
      <div className="mt-1 flex items-center gap-2">
        <input id={id} type={type} inputMode={decimal ? 'decimal' : 'numeric'}
          placeholder={placeholder} min={min} max={max} step={decimal ? 0.1 : 1}
          value={valeur ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
          onBlur={(e) => {
            const range = ranger(e.target.value === '' ? null : Number(e.target.value))
            if (range !== valeur) onChange(range)
          }}
          className="w-full rounded-lg border border-ink/20 px-3 py-2 text-ink
            focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
        {suffixe && <span className="shrink-0 text-dark/70">{suffixe}</span>}
      </div>
      {aide && <p className="mt-1 text-sm text-dark/60">{aide}</p>}
    </div>
  )
}

/** Un « déjà là » / « je l'ajoute » : la distinction qui change tout dans le calcul. */
export function DejaLa({ deja, onChange }: { deja: boolean; onChange: (v: boolean) => void }) {
  return (
    <div>
      <span className="block font-semibold text-ink">Cet équipement…</span>
      <div className="mt-1 grid grid-cols-2 gap-2">
        {[
          { v: true, label: 'je l’ai déjà' },
          { v: false, label: 'je l’ajoute' },
        ].map((o) => (
          <button key={String(o.v)} type="button" onClick={() => onChange(o.v)}
            aria-pressed={deja === o.v}
            className={`rounded-lg border px-3 py-2 text-sm font-semibold transition
              ${deja === o.v ? 'border-primary bg-primary text-white' : 'border-ink/20 text-ink hover:border-primary'}`}>
            {o.label}
          </button>
        ))}
      </div>
      <p className="mt-1 text-sm text-dark/60">
        {deja
          ? 'Il est déjà compris dans votre consommation : il ne fait que façonner la courbe.'
          : 'Il s’ajoute à votre consommation actuelle.'}
      </p>
    </div>
  )
}
