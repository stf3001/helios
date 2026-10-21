import { useState } from 'react'
import { Check, ChevronDown, Phone, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Attente, BTN_PRIMAIRE, Erreur, TitrePage, useAdminData } from '../../components/admin/AdminLayout'
import { useAuth } from '../../context/AuthContext'
import { useTitle } from '../../hooks/useTitle'

/**
 * Les rendez-vous téléphoniques réservés sur le site (point 2 de TODO.md, moitié « écran »).
 * Aucune notification ici : elle attend le fournisseur d'e-mail (point 1). Les heures sont
 * celles de Paris, été comme hiver, quel que soit le fuseau du navigateur.
 */

interface RendezVous {
  id: string
  nom: string
  telephone: string
  email: string | null
  sujet: string | null
  debut: string
  duree_min: number
  statut: 'reserve' | 'honore' | 'absent' | 'annule'
  note_interne: string | null
  foyer_email: string | null
}

const STATUTS: { v: RendezVous['statut']; l: string; actif: string }[] = [
  { v: 'reserve', l: 'Réservé', actif: 'border-ink bg-ink text-white' },
  { v: 'honore', l: 'Honoré', actif: 'border-leaf bg-leaf text-white' },
  { v: 'absent', l: 'Absent', actif: 'border-terra bg-terra text-white' },
  { v: 'annule', l: 'Annulé', actif: 'border-dark/40 bg-dark/40 text-white' },
]

/** « Jeudi 22 octobre à 11:30 » — majuscule à la première lettre seulement. */
const quand = (iso: string) => {
  const texte = new Date(iso).toLocaleString('fr-FR', {
    timeZone: 'Europe/Paris', weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit',
  })
  return texte.charAt(0).toUpperCase() + texte.slice(1)
}

function Ligne({ r, enregistrer }: { r: RendezVous; enregistrer: (champs: Partial<RendezVous>) => Promise<void> }) {
  const [note, setNote] = useState(r.note_interne ?? '')
  const [busy, setBusy] = useState(false)
  const passe = async (champs: Partial<RendezVous>) => { setBusy(true); await enregistrer(champs); setBusy(false) }

  return (
    <div className={'rounded-2xl border border-bord bg-white p-4 ' + (r.statut === 'annule' ? 'opacity-60' : '')}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-display text-xl leading-tight text-ink">{quand(r.debut)}</p>
          <p className="text-sm text-dark/70">{r.nom} · {r.duree_min} min</p>
        </div>
        <a href={`tel:${r.telephone.replace(/[^\d+]/g, '')}`}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-xl bg-primary px-3 py-1.5 text-sm font-semibold text-white hover:bg-terra">
          <Phone className="h-4 w-4" /> {r.telephone}
        </a>
      </div>

      {r.sujet && <p className="mt-2 rounded-xl bg-cream px-3 py-2 text-sm text-dark">« {r.sujet} »</p>}
      <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-dark/55">
        {r.email && <a href={`mailto:${r.email}`} className="hover:text-primary hover:underline">{r.email}</a>}
        {r.foyer_email && (
          <Link to="/admin/foyers" className="inline-flex items-center gap-1 hover:text-primary hover:underline"
            title="Ce visiteur a un compte : le retrouver dans Foyers & RGPD">
            <UserRound className="h-3.5 w-3.5" /> compte {r.foyer_email}
          </Link>
        )}
      </p>

      <div className="mt-3 flex flex-wrap gap-1.5" role="group" aria-label="Statut du rendez-vous">
        {STATUTS.map((s) => (
          <button key={s.v} disabled={busy} onClick={() => s.v !== r.statut && passe({ statut: s.v })}
            aria-pressed={s.v === r.statut}
            className={'rounded-xl border px-3 py-1 text-sm transition disabled:opacity-50 '
              + (s.v === r.statut ? s.actif : 'border-bord bg-white text-dark hover:bg-cream')}>
            {s.l}
          </button>
        ))}
      </div>

      <details className="group mt-2" open={!!r.note_interne}>
        <summary className="flex cursor-pointer list-none items-center gap-1.5 text-sm text-primary hover:text-terra">
          <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
          {r.note_interne ? 'Note interne' : 'Ajouter une note interne'}
        </summary>
        <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2}
          placeholder="Visible seulement en administration"
          className="mt-2 w-full rounded-xl border border-bord px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
        <button disabled={busy || note === (r.note_interne ?? '')} onClick={() => passe({ note_interne: note })}
          className={BTN_PRIMAIRE + ' mt-1.5'}>
          <Check className="h-3.5 w-3.5" /> Enregistrer la note
        </button>
      </details>
    </div>
  )
}

export default function AdminRendezVous() {
  useTitle('Back-office — Rendez-vous')
  const { authFetch } = useAuth()
  const [periode, setPeriode] = useState<'a_venir' | 'passes'>('a_venir')
  const { data, error, reload } = useAdminData<RendezVous[]>(`/api/admin/rendez-vous?periode=${periode}`)

  async function enregistrer(r: RendezVous, champs: Partial<RendezVous>) {
    await authFetch(`/api/admin/rendez-vous/${r.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(champs),
    })
    reload()
  }

  return (
    <>
      <TitrePage titre="Rendez-vous">
        Les appels réservés sur le site, à l'heure de Paris. Un créneau proposé engage quelqu'un à
        appeler : marquez chaque rendez-vous une fois passé.
      </TitrePage>

      <div className="mt-5 flex flex-wrap gap-2">
        {([['a_venir', 'À venir'], ['passes', 'Passés (60 jours)']] as const).map(([v, l]) => (
          <button key={v} onClick={() => setPeriode(v)}
            className={'rounded-xl px-3 py-1.5 text-sm transition '
              + (periode === v ? 'bg-primary font-semibold text-white' : 'border border-bord bg-white text-dark hover:bg-cream')}>
            {l}
          </button>
        ))}
      </div>

      {error && <Erreur>{error}</Erreur>}
      {!data && !error && <Attente />}

      {data && data.length === 0 && (
        <p className="mt-6 rounded-2xl border border-bord bg-white p-4 text-sm text-dark/70">
          {periode === 'a_venir' ? 'Aucun rendez-vous à venir.' : 'Aucun rendez-vous ces 60 derniers jours.'}
        </p>
      )}

      {data && data.length > 0 && (
        <div className="mt-5 space-y-3">
          {data.map((r) => <Ligne key={`${r.id}-${r.statut}-${r.note_interne ?? ''}`} r={r} enregistrer={(c) => enregistrer(r, c)} />)}
        </div>
      )}
    </>
  )
}
