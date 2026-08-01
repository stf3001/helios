import { useEffect, useState } from 'react'
import { ZoomIn, X } from 'lucide-react'

/** Illustration « La maison de demain » (image WebP dans /public) présentée en grand,
 * cliquable pour un affichage plein écran — nécessaire car les légendes de l'infographie
 * sont fines et illisibles à la taille réduite d'un mobile. Aucune dépendance externe. */
export default function MaisonDemain() {
  const [zoom, setZoom] = useState(false)

  // Fermeture au clavier (Échap) + blocage du scroll de fond quand la vue plein écran est ouverte.
  useEffect(() => {
    if (!zoom) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setZoom(false)
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [zoom])

  return (
    <>
      <button
        type="button"
        onClick={() => setZoom(true)}
        className="group relative block w-full overflow-hidden rounded-3xl border border-gray-200 shadow-sm hover:shadow-md transition"
        aria-label="Agrandir l'illustration de la maison de demain"
      >
        <img
          src="/maison-demain.webp"
          alt="La maison de demain : panneaux solaires, stockage par batterie, éoliennes verticales, puits canadien, générateur d'eau atmosphérique, véhicule électrique et pilotage intelligent — avec les flux d'énergie qui circulent entre chaque élément."
          width={1536}
          height={1024}
          loading="lazy"
          className="w-full h-auto"
        />
        <span className="absolute bottom-3 right-3 flex items-center gap-1.5 rounded-full bg-ink/80 text-white text-xs px-3 py-1.5 opacity-90 group-hover:opacity-100">
          <ZoomIn className="w-3.5 h-3.5" /> Agrandir
        </span>
      </button>

      {zoom && (
        <div
          className="fixed inset-0 z-[100] bg-black/85 flex items-center justify-center p-4 animate-fade-in"
          onClick={() => setZoom(false)}
        >
          <button
            type="button"
            className="absolute top-4 right-4 text-white/80 hover:text-white"
            aria-label="Fermer"
            onClick={() => setZoom(false)}
          >
            <X className="w-7 h-7" />
          </button>
          <img
            src="/maison-demain.webp"
            alt="La maison de demain (vue agrandie)"
            className="max-w-full max-h-full rounded-xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  )
}
