/**
 * Les indicateurs — le même calcul, deux formes selon la place disponible.
 *
 * `carte` : flottante en haut à droite de la scène, sur grand écran (à partir de `xl`).
 * C'est la mise en page « configurateur » : la scène occupe le centre, les chiffres se
 * posent dans un coin, et ils suivent le défilement.
 * `bandeau` : une rangée collée sous l'en-tête du site, en dessous de `xl`, où une
 * colonne de plus ne tiendrait pas sans écraser la scène.
 *
 * Dans les deux cas la règle est la même : ils ne bougent JAMAIS de place, et rien ne les
 * recouvre — on doit voir l'autonomie et la facture changer pendant qu'on règle.
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
  variante?: 'bandeau' | 'carte'
}

/** Ce qui a bougé depuis le calcul précédent, en clair, et qui s'effacera. */
function useVariation(indicateurs: Indicateurs | null): string | null {
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

  return variation
}

function Case({ label, valeur, sous }: { label: string; valeur: string; sous?: string }) {
  return (
    <div className="min-w-0">
      <p className="truncate text-xs uppercase tracking-wide text-dark/60">{label}</p>
      <p className="truncate font-display text-[15px] font-bold leading-tight text-ink sm:text-xl">{valeur}</p>
      {sous && <p className="truncate text-xs text-dark/60">{sous}</p>}
    </div>
  )
}

/**
 * Une ligne de la carte : le mot, le chiffre dessous, la précision en dessous encore.
 *
 * Empilé et non côte à côte : mis sur une seule ligne, « Facture / mois » et son montant
 * imposaient à eux seuls la largeur de la colonne, et la carte mangeait la scène. En
 * hauteur, la colonne se resserre à 11 rem sans qu'aucun chiffre soit tronqué.
 */
function Rangee({ label, valeur, sous }: { label: string; valeur: string; sous?: string }) {
  return (
    <div className="py-2">
      <dt className="text-[11px] uppercase leading-tight tracking-wide text-dark/60">{label}</dt>
      <dd className="font-display text-xl font-bold leading-tight text-ink">
        {valeur}
        {sous && (
          <span className="mt-0.5 block font-sans text-xs font-normal leading-snug text-dark/60">
            {sous}
          </span>
        )}
      </dd>
    </div>
  )
}

export default function Bandeau({ indicateurs, calculEnCours, variante = 'bandeau' }: Props) {
  const variation = useVariation(indicateurs)
  const i = indicateurs

  /* L'état du calcul et la variation : même contenu dans les deux formes. */
  const etat = (
    <>
      {variation && (
        <span className="animate-fade-in whitespace-nowrap rounded-full bg-leaf/15 px-2.5 py-0.5
          font-semibold text-leaf">
          {variation}
        </span>
      )}
      {calculEnCours && <span className="text-dark/50">calcul…</span>}
    </>
  )

  if (variante === 'carte') {
    return (
      <section aria-label="Vos indicateurs"
        className="rounded-2xl border border-ink/10 bg-white/95 p-3 shadow-question backdrop-blur">
        <div className="flex justify-center">
          <Anneau pct={i?.autonomie_pct ?? 0} partVirtuelle={i?.autonomie_part_virtuelle_pct ?? 0}
            classe="h-20 w-20" />
        </div>

        <dl className="mt-1 divide-y divide-ink/5">
          <Rangee label="Facture / mois"
            valeur={i ? euros(i.facture_mois_eur) : '—'}
            sous={i ? `au lieu de ${euros(i.facture_mois_reference_eur)}` : undefined} />
          <Rangee label="Économies"
            valeur={i ? euros(i.economie_1re_annee_eur) : '—'}
            sous="la 1re année" />
          <Rangee label="Retour"
            valeur={i ? ans(i.temps_retour_ans) : '—'}
            sous="sur l’investissement" />
        </dl>

        {/* Hauteur réservée : la carte ne doit pas sauter quand la notification apparaît. */}
        <div className="mt-2 flex min-h-[1.5rem] flex-wrap items-center gap-2 text-sm" aria-live="polite">
          {etat}
        </div>

        {i?.conso_estimee && (
          <p className="mt-1 text-xs text-dark/60">
            Consommation estimée — indiquez la vôtre pour affiner.
          </p>
        )}
      </section>
    )
  }

  /* `md:hidden` est porté par l'élément collé lui-même : un conteneur intermédiaire de la
     hauteur du bandeau empêcherait `sticky` de fonctionner. `top-16`, c'est la hauteur de
     l'en-tête du site, qui est collé lui aussi. */
  return (
    <div className="sticky top-16 z-20 border-b border-ink/10 bg-cream/95 backdrop-blur md:hidden">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-2 sm:gap-4">
        <Anneau pct={i?.autonomie_pct ?? 0} partVirtuelle={i?.autonomie_part_virtuelle_pct ?? 0}
          classe="h-14 w-14 shrink-0 sm:h-16 sm:w-16" />

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

        <div className="flex shrink-0 items-center gap-2 text-sm" aria-live="polite">{etat}</div>
      </div>

      {i?.conso_estimee && (
        <p className="mx-auto max-w-6xl px-4 pb-1.5 text-xs text-dark/60">
          Consommation estimée — indiquez la vôtre pour affiner.
        </p>
      )}
    </div>
  )
}
