import { type ReactNode, type Ref } from 'react'
import { ChevronDown } from 'lucide-react'

/**
 * Un bloc repliable — le motif de « La maison de demain », rendu commun.
 *
 * Il vivait dans `components/simulateur/Onglets.tsx`, qui reste son principal usager.
 * Il a été sorti ici le 06/10/2026 quand l'espace client et la fiche maison ont adopté
 * le même pliage (demande de Stéphane) : trois copies auraient divergé au premier
 * ajustement, et c'est le genre de détail qui se voit sur toutes les pages à la fois.
 *
 * `<details>` natif plutôt qu'un état React : le clavier, le lecteur d'écran et la
 * recherche dans la page fonctionnent sans qu'on ait à les recoder, et l'ouverture reste
 * fluide. **Ne pas le passer en composant contrôlé** pour ces raisons.
 *
 * `resume` est ce qui rend le pliage supportable : replié, un bloc doit dire ce qu'il
 * contient — sinon on ouvre les six pour chercher.
 */
export default function Depliant({
  titre,
  children,
  aide,
  resume,
  icone,
  ouvert = false,
  refDetails,
}: {
  titre: string
  children: ReactNode
  aide?: string
  /** Affiché à droite du titre quand le bloc est replié : avancement, compte, poids… */
  resume?: ReactNode
  /** Petite icône devant le titre, pour repérer le bloc d'un coup d'œil. */
  icone?: ReactNode
  ouvert?: boolean
  refDetails?: Ref<HTMLDetailsElement>
}) {
  return (
    <details ref={refDetails} open={ouvert} className="group rounded-xl border border-ink/10 bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-xl
        px-4 py-3 hover:bg-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50">
        <span className="flex min-w-0 items-center gap-2.5">
          {icone}
          <h3 className="font-display text-lg font-bold text-ink truncate">{titre}</h3>
        </span>
        <span className="flex shrink-0 items-center gap-3">
          {resume && <span className="text-sm text-dark/60">{resume}</span>}
          <ChevronDown size={20}
            className="shrink-0 text-primary transition-transform group-open:rotate-180" />
        </span>
      </summary>
      <div className="px-4 pb-4">
        {aide && <p className="-mt-1 mb-3 text-sm text-dark/70">{aide}</p>}
        <div className="space-y-4">{children}</div>
      </div>
    </details>
  )
}
