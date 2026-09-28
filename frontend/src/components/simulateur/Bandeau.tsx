/**
 * Le bandeau d'indicateurs — toujours visible, il ne bouge jamais de place.
 *
 * À chaque changement, une courte notification dit ce qui a bougé (« +160 €/an,
 * +3 pts d'autonomie »). C'est ce qui relie un geste à son effet : sans elle, on règle
 * à l'aveugle et on ne comprend pas pourquoi les chiffres ont changé.
 */

import { useEffect, useRef, useState } from 'react'

import { ans, euros, type Indicateurs } from '../../lib/simulateur'
import { Anneau } from './Graphiques'

interface Props {
  indicateurs: Indicateurs | null
  calculEnCours: boolean
}

function Case({ label, valeur, sous }: { label: string; valeur: string; sous?: string }) {
  return (
    <div className="min-w-0">
      <p className="truncate text-xs uppercase tracking-wide text-dark/60">{label}</p>
      <p className="truncate font-display text-[15px] font-bold leading-tight text-ink sm:text-2xl">{valeur}</p>
      {sous && <p className="truncate text-xs text-dark/60">{sous}</p>}
    </div>
  )
}

export default function Bandeau({ indicateurs, calculEnCours }: Props) {
  const [variation, setVariation] = useState<string | null>(null)
  const precedent = useRef<Indicateurs | null>(null)

  useEffect(() => {
    if (!indicateurs) return
    const avant = precedent.current
    precedent.current = indicateurs
    if (!avant) return

    const morceaux: string[] = []
    const deltaEconomie = Math.round(indicateurs.economie_1re_annee_eur - avant.economie_1re_annee_eur)
    const deltaAutonomie = Math.round(indicateurs.autonomie_pct - avant.autonomie_pct)
    if (deltaEconomie !== 0) morceaux.push(`${deltaEconomie > 0 ? '+' : ''}${deltaEconomie} €/an`)
    if (deltaAutonomie !== 0) {
      morceaux.push(`${deltaAutonomie > 0 ? '+' : ''}${deltaAutonomie} pts d’autonomie`)
    }
    if (!morceaux.length) return

    setVariation(morceaux.join(', '))
    const minuteur = setTimeout(() => setVariation(null), 2600)
    return () => clearTimeout(minuteur)
  }, [indicateurs])

  const i = indicateurs

  return (
    <div className="sticky top-0 z-20 border-b border-ink/10 bg-cream/95 backdrop-blur">
      <div className="mx-auto max-w-6xl px-4 py-3">
        <div className="flex items-center gap-4">
          <div className="shrink-0">
            <Anneau pct={i?.autonomie_pct ?? 0} partVirtuelle={i?.autonomie_part_virtuelle_pct ?? 0}
              classe="h-20 w-20 sm:h-28 sm:w-28" />
          </div>
          <div className="grid min-w-0 flex-1 grid-cols-3 gap-2 sm:gap-3">
            <Case label="Facture / mois"
              valeur={i ? euros(i.facture_mois_eur) : '—'}
              sous={i ? `au lieu de ${euros(i.facture_mois_reference_eur)}` : undefined} />
            <Case label="Économies"
              valeur={i ? euros(i.economie_1re_annee_eur) : '—'}
              sous="la 1re année" />
            <Case label="Retour"
              valeur={i ? ans(i.temps_retour_ans) : '—'}
              sous="sur l’investissement" />
          </div>
        </div>

        <div className="mt-1 flex min-h-[1.25rem] items-center gap-3 text-sm" aria-live="polite">
          {variation && (
            <span className="animate-fade-in rounded-full bg-leaf/15 px-2.5 py-0.5 font-semibold text-leaf">
              {variation}
            </span>
          )}
          {calculEnCours && <span className="text-dark/50">calcul…</span>}
          {i?.conso_estimee && (
            <span className="truncate text-dark/60">
              Consommation estimée — indiquez la vôtre pour affiner.
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
