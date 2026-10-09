import type { LucideIcon } from 'lucide-react'

/**
 * Le rail d'onglets en icônes — celui du simulateur, repris pour « Mon espace »
 * (demande de Stéphane, 06/10/2026 : « je le trouve super sympa »).
 *
 * POURQUOI CE N'EST PAS LE MÊME COMPOSANT QUE CELUI DE `SimulateurSolaire.tsx`.
 * Là-bas, le rail est soudé à une grille de trois colonnes : il porte un bouton
 * « Replier » qui fait disparaître le panneau, le panneau s'ouvre en calque flottant
 * au-dessus de la scène sous `xl`, et le rail change de bordure selon qu'il partage ou
 * non la boîte du panneau. Partager un composant aurait demandé une demi-douzaine de
 * props pour piloter tout cela depuis l'extérieur — plus de complexité que les trente
 * lignes dupliquées. **Ce qui est partagé, c'est le dessin d'un bouton** (`BoutonRail`
 * ci-dessous) : c'est lui qu'on voit, et c'est lui qui doit rester identique.
 *
 * Deux formes, comme au simulateur : le rail vertical à partir de `md`, et une bande
 * horizontale en dessous — une colonne d'icônes à gauche ne tient pas sur un téléphone.
 */

export interface OngletRail<T extends string> {
  id: T
  label: string
  Icone: LucideIcon
}

/** Le bouton, seul élément réellement commun aux deux rails du site. */
function BoutonRail<T extends string>({
  onglet, actif, onChoisir, vertical,
}: {
  onglet: OngletRail<T>
  actif: boolean
  onChoisir: (id: T) => void
  vertical: boolean
}) {
  const { id, label, Icone } = onglet
  return (
    <button
      role="tab" type="button" aria-selected={actif} aria-controls="panneau-espace"
      onClick={() => onChoisir(id)}
      className={
        'flex flex-col items-center gap-1 text-[10px] font-semibold leading-none transition '
        + (vertical
          ? `w-[3.75rem] rounded-xl px-1 py-2 ${actif ? 'bg-primary text-white shadow' : 'text-ink hover:bg-white'}`
          : `flex-1 px-0.5 py-1.5 ${actif ? 'text-primary' : 'text-dark/60'}`)
      }
    >
      {vertical ? (
        <Icone size={20} strokeWidth={actif ? 2.4 : 2} aria-hidden="true" />
      ) : (
        /* En bande, c'est une pastille qui marque l'onglet courant : un aplat sur toute
           la largeur du bouton écraserait le mot. */
        <span className={'flex h-7 w-10 items-center justify-center rounded-full '
          + (actif ? 'bg-primary text-white' : '')}>
          <Icone size={18} strokeWidth={actif ? 2.4 : 2} aria-hidden="true" />
        </span>
      )}
      <span className="w-full truncate text-center">{label}</span>
    </button>
  )
}

export function RailOnglets<T extends string>({
  onglets, actif, onChoisir, ariaLabel,
}: {
  onglets: OngletRail<T>[]
  actif: T
  onChoisir: (id: T) => void
  ariaLabel: string
}) {
  return (
    <div
      role="tablist" aria-orientation="vertical" aria-label={ariaLabel}
      /* `sticky` : le rail reste sous la main quand le panneau est long (les documents,
         une conversation qui défile). `top-20` dégage l'en-tête du site, comme partout. */
      className="hidden shrink-0 flex-col gap-1 rounded-2xl border border-ink/10 bg-cream/80
        p-1.5 shadow-question backdrop-blur md:sticky md:top-20 md:flex"
    >
      {onglets.map((o) => (
        <BoutonRail key={o.id} onglet={o} actif={o.id === actif} onChoisir={onChoisir} vertical />
      ))}
    </div>
  )
}

export function BandeOnglets<T extends string>({
  onglets, actif, onChoisir, ariaLabel,
}: {
  onglets: OngletRail<T>[]
  actif: T
  onChoisir: (id: T) => void
  ariaLabel: string
}) {
  return (
    <nav
      role="tablist" aria-label={ariaLabel}
      className="mb-4 flex rounded-2xl border border-ink/10 bg-cream/80 p-1 md:hidden"
    >
      {onglets.map((o) => (
        <BoutonRail key={o.id} onglet={o} actif={o.id === actif} onChoisir={onChoisir} vertical={false} />
      ))}
    </nav>
  )
}
