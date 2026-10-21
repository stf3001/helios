import { useCallback, useEffect, useState } from 'react'
import { BookOpen, FileCheck2, Pencil, Plus, Trash2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import FieldInput from '../fiche/FieldInput'
import type { Draft, FieldSpec } from '../fiche/types'
import { messageErreur, type Doc } from './Formulaires'
import { type EquipementNom, aujourdhui, dateLongue, nomEquipement, signalerMaj, useMaj } from './commun'

/**
 * Le journal de la maison (carnet, lot 4) : ce qui a été fait, du plus récent au plus
 * ancien, entrées et chantiers du lot 1 mêlés. Une entrée avec un document est JUSTIFIÉE.
 * Les coûts s'affichent ligne à ligne et ne sont JAMAIS additionnés (pas de « budget » ici).
 * Un remplacement PROPOSE de passer l'ancien appareil hors service : rien d'automatique.
 */

type Ligne = {
  source: 'journal' | 'travaux'; id: string; date: string; type: string; titre: string
  equipement_id?: string | null; piece_id?: string | null; tache_id?: string | null
  intervenant: string | null; cout_eur: number | null; document_id: string | null; note: string | null
  justifie: boolean; date_reception_connue: boolean
}
type PieceNom = { id: string; nom: string }

const TYPES = [
  { value: 'entretien', label: 'Entretien' }, { value: 'controle', label: 'Contrôle' },
  { value: 'reparation', label: 'Réparation' }, { value: 'remplacement', label: 'Remplacement' },
  { value: 'amelioration', label: 'Amélioration' }, { value: 'autre', label: 'Autre' },
]
const LIBELLE_TYPE: Record<string, string> = { ...Object.fromEntries(TYPES.map((t) => [t.value, t.label])), travaux: 'Travaux' }
const CHAMPS = ['date', 'type', 'titre', 'equipement_id', 'piece_id', 'intervenant', 'cout_eur', 'document_id', 'note']

const euros = (n: number) => n.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 })

export default function Journal({ equipements, documents, onRemplacer }: {
  equipements: EquipementNom[]; documents: Doc[]
  /** Ouvre le formulaire du lot 1 pré-rempli pour le nouvel appareil. */
  onRemplacer: (ancien: EquipementNom, date: string) => void
}) {
  const { authFetch } = useAuth()
  const [lignes, setLignes] = useState<Ligne[]>([])
  const [pieces, setPieces] = useState<PieceNom[]>([])
  const [filtre, setFiltre] = useState('')
  const [form, setForm] = useState<Draft | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [remplacement, setRemplacement] = useState<{ eq: EquipementNom; date: string } | null>(null)

  const charger = useCallback(() => {
    const q = filtre ? `?equipement_id=${filtre}` : ''
    authFetch(`/api/houses/me/journal${q}`).then((r) => (r.ok ? r.json() : [])).then(setLignes)
    authFetch('/api/houses/me/pieces').then((r) => (r.ok ? r.json() : [])).then(setPieces)
  }, [authFetch, filtre])
  useEffect(charger, [charger])
  useMaj(charger)

  const parId = Object.fromEntries(equipements.map((e) => [e.id, e]))
  const optionsEq = equipements.map((e) => ({ value: e.id, label: nomEquipement(e) + (e.en_service ? '' : ' (ancien)') }))
  const specs: FieldSpec[] = [
    { key: 'date', label: 'Date', type: 'date' },
    { key: 'type', label: 'Type', type: 'select', options: TYPES },
    { key: 'titre', label: 'Ce qui a été fait', type: 'text' },
    ...(optionsEq.length ? [{ key: 'equipement_id', label: 'Équipement', type: 'select' as const, options: optionsEq }] : []),
    ...(pieces.length ? [{ key: 'piece_id', label: 'Pièce', type: 'select' as const, options: pieces.map((p) => ({ value: p.id, label: p.nom })) }] : []),
    { key: 'intervenant', label: 'Par (moi, ou le nom du pro)', type: 'text' },
    { key: 'cout_eur', label: 'Coût TTC (€), facultatif', type: 'number', min: 0, step: 'any' },
    ...(documents.length ? [{ key: 'document_id', label: 'Justificatif (dans vos papiers)', type: 'select' as const,
      options: documents.map((d) => ({ value: d.id, label: d.filename })) }] : []),
    { key: 'note', label: 'Note', type: 'textarea' },
  ]

  async function enregistrer(e: React.FormEvent) {
    e.preventDefault()
    if (!form) return
    if (!form.titre || !form.type || !form.date) { setErreur('Indiquez la date, le type et ce qui a été fait.'); return }
    if (String(form.date) > aujourdhui()) { setErreur('Le journal garde ce qui a été fait : pas de date dans le futur.'); return }
    const id = form.id as string | undefined
    const corps = Object.fromEntries(CHAMPS.filter((k) => k in form).map((k) => [k, form[k] === '' ? null : form[k]]))
    const res = await authFetch(id ? `/api/houses/me/journal/${id}` : '/api/houses/me/journal', {
      method: id ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
    })
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    // Un remplacement d'un appareil encore en service : on PROPOSE la suite, on ne la fait pas.
    const ancien = form.equipement_id ? parId[form.equipement_id as string] : undefined
    if (!id && form.type === 'remplacement' && ancien?.en_service) setRemplacement({ eq: ancien, date: String(form.date) })
    setForm(null); setErreur(null)
    signalerMaj()
  }

  async function supprimer(l: Ligne) {
    if (!confirm(`Supprimer « ${l.titre} » du journal ?`)) return
    const res = await authFetch(`/api/houses/me/journal/${l.id}`, { method: 'DELETE' })
    if (res.ok) signalerMaj()
  }

  async function confirmerRemplacement() {
    if (!remplacement) return
    await authFetch(`/api/houses/me/equipements/${remplacement.eq.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ en_service: false }),
    })
    onRemplacer(remplacement.eq, remplacement.date)
    setRemplacement(null)
    signalerMaj()
  }

  return (
    <section className="rounded-xl border border-ink/10 bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-display text-xl text-ink">
          <BookOpen className="h-5 w-5 text-primary" /> Journal de la maison
        </h2>
        {!form && (
          <button onClick={() => { setForm({ date: aujourdhui(), type: 'entretien', intervenant: 'moi' }); setErreur(null) }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90">
            <Plus className="h-4 w-4" /> Ajouter
          </button>
        )}
      </div>

      {remplacement && (
        <div className="mb-3 rounded-lg border border-primary/40 bg-cream px-3 py-2.5 text-sm">
          <p className="text-dark/80">
            Vous avez remplacé : {nomEquipement(remplacement.eq)}. Le passer dans vos anciens équipements et ajouter le nouveau ?
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <button onClick={confirmerRemplacement}
              className="rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-white hover:opacity-90">Oui, ajouter le nouveau</button>
            <button onClick={() => setRemplacement(null)}
              className="rounded-lg border border-bord px-3 py-1.5 text-sm text-dark/70 hover:border-primary hover:text-primary">Non merci</button>
          </div>
        </div>
      )}

      {form && (
        <form onSubmit={enregistrer} className="mb-3 space-y-3 rounded-lg border border-primary/40 bg-cream/60 p-3">
          <div className="grid gap-3 sm:grid-cols-2">
            {specs.map((s) => (
              <div key={s.key} className={s.type === 'textarea' ? 'sm:col-span-2' : ''}>
                <FieldInput spec={s} value={form[s.key]} onChange={(v) => setForm((d) => ({ ...d, [s.key]: v }))} />
              </div>
            ))}
          </div>
          {erreur && <p className="text-sm text-terra">{erreur}</p>}
          <div className="flex flex-wrap gap-2">
            <button type="submit" className="rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90">Enregistrer</button>
            <button type="button" onClick={() => setForm(null)}
              className="rounded-lg border border-bord px-3.5 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">Annuler</button>
          </div>
        </form>
      )}

      {equipements.length > 0 && (
        <label className="mb-3 flex items-center gap-2 text-sm text-dark/70">
          <span className="shrink-0">Voir :</span>
          <select value={filtre} onChange={(e) => setFiltre(e.target.value)}
            className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
            <option value="">toute la maison</option>
            {optionsEq.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </label>
      )}

      {lignes.length === 0 ? (
        <p className="text-sm text-dark/70">Rien encore. Chaque « C'est fait » s'inscrit ici, et vous pouvez ajouter une réparation ou un remplacement à la main.</p>
      ) : (
        <ol className="relative space-y-3 border-l border-bord pl-4">
          {lignes.map((l) => (
            <li key={`${l.source}-${l.id}`} className="relative">
              <span className={'absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-white ' +
                (l.source === 'travaux' ? 'bg-ink' : 'bg-primary')} />
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 text-sm">
                  <p className="text-xs text-dark/50">
                    {dateLongue(l.date)}{!l.date_reception_connue && ' (saisi, réception à indiquer)'} · {LIBELLE_TYPE[l.type] ?? l.type}
                  </p>
                  <p className="flex items-center gap-1.5 font-semibold text-ink">
                    {l.titre}
                    {l.justifie && <FileCheck2 className="h-4 w-4 shrink-0 text-leaf" aria-label="Justifié par un document" />}
                  </p>
                  <p className="text-xs text-dark/60">
                    {[l.equipement_id ? nomEquipement(parId[l.equipement_id]) : null,
                      l.piece_id ? pieces.find((p) => p.id === l.piece_id)?.nom : null,
                      l.intervenant === 'moi' ? 'fait par moi' : l.intervenant,
                      l.cout_eur != null ? euros(l.cout_eur) : null,
                      l.justifie ? 'justifié' : 'déclaré'].filter(Boolean).join(' · ')}
                  </p>
                  {l.note && <p className="text-xs text-dark/50">{l.note}</p>}
                </div>
                {l.source === 'journal' && (
                  <span className="flex shrink-0 gap-1">
                    <button title="Modifier" aria-label={`Modifier « ${l.titre} »`} className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-primary"
                      onClick={() => { setForm(Object.fromEntries([['id', l.id], ...CHAMPS.map((k) => [k, (l as unknown as Draft)[k] ?? null])])); setErreur(null) }}>
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button title="Supprimer" aria-label={`Supprimer « ${l.titre} »`} className="rounded p-1.5 text-dark/50 hover:bg-cream hover:text-terra"
                      onClick={() => supprimer(l)}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </span>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
