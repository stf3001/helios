import { useCallback, useEffect, useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { ouvrirJournal, useMaj } from './commun'

/**
 * Vigilance météo (phase 2) — un PETIT PLUS, volontairement discret : une ligne fine en haut de
 * l'espace, une pastille de la couleur de Météo-France, les gestes repliés. Rien sans vigilance
 * orange ou rouge pour le département ; rien du tout tant que Météo-France n'est pas branché.
 */
export interface Vigilance {
  phenomene: string; libelle: string; couleur: 'orange' | 'rouge'; debut: string; fin: string; en_cours: boolean
  gestes: string | null; autorites: string | null; carte: string
}
export interface ApresEpisode { phenomene: string; libelle: string; fin: string }

const quand = (iso: string) => new Date(iso).toLocaleString('fr-FR', { weekday: 'long', hour: '2-digit', minute: '2-digit' })

export function Pastille({ couleur }: { couleur: string }) {
  return <span aria-hidden className={'inline-block h-2.5 w-2.5 shrink-0 rounded-full '
    + (couleur === 'rouge' ? 'bg-vigirouge' : 'bg-vigiorange')} />
}

/** Le texte de la fiche porte du gras Markdown ; ce rendu minimal suffit. */
function Gestes({ texte }: { texte: string }) {
  return <p className="text-sm text-dark/80">{texte.split(/\*\*(.+?)\*\*/g).map((m, i) => (i % 2 ? <strong key={i}>{m}</strong> : m))}</p>
}

export function LigneVigilance({ v }: { v: Vigilance }) {
  return (
    <div className="min-w-0 text-sm">
      <p className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-ink">
        <Pastille couleur={v.couleur} />
        <span>Vigilance {v.couleur} · {v.libelle}</span>
        <span className="text-dark/60">{v.en_cours ? `jusqu'à ${quand(v.fin)}` : `à partir de ${quand(v.debut)}`}</span>
      </p>
      {v.autorites && <p className="mt-0.5 text-dark/70">{v.autorites}</p>}
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        {v.gestes && (
          <details className="w-full">
            <summary className="cursor-pointer text-primary">Les gestes pour votre maison</summary>
            <div className="mt-1.5"><Gestes texte={v.gestes} /></div>
          </details>
        )}
        <a href={v.carte} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
          Voir la carte de vigilance <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  )
}

/** « Noter un dégât » : le journal vit dans « Ma maison » ; on y passe, puis on l'ouvre pré-rempli. */
export function noterUnDegat(a: ApresEpisode, allerMaison?: () => void) {
  allerMaison?.()
  window.setTimeout(() => ouvrirJournal({
    type: 'autre', titre: `Dégât après ${a.libelle.toLowerCase()}`, intervenant: 'moi',
    note: 'Photo à joindre depuis vos papiers ; utile pour l\'assurance.',
  }), allerMaison ? 250 : 0)
}

export default function VigilanceMeteo() {
  const { authFetch } = useAuth()
  const [actives, setActives] = useState<Vigilance[]>([])
  const charger = useCallback(() => {
    authFetch('/api/houses/me/vigilance').then((r) => (r.ok ? r.json() : { actives: [] }))
      .then((b) => setActives(b.actives ?? [])).catch(() => setActives([]))
  }, [authFetch])
  useEffect(charger, [charger])
  useMaj(charger)

  if (actives.length === 0) return null
  return (
    <div className="mb-3 space-y-2 rounded-xl border border-bord bg-white px-4 py-2.5" aria-label="Vigilance météo">
      {actives.map((v) => <LigneVigilance key={`${v.phenomene}-${v.debut}`} v={v} />)}
    </div>
  )
}
