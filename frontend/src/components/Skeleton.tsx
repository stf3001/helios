/** Placeholder de chargement animé (au lieu d'un texte « Chargement… »). */
export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={'animate-pulse rounded-lg bg-black/5 ' + className} />
}

/** Grille de cartes fantômes — pour les pages qui chargent une liste. */
export function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="border border-gray-100 rounded-2xl p-5 space-y-3">
          <Skeleton className="h-6 w-6" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-3 w-full" />
        </div>
      ))}
    </div>
  )
}
