import { CloudOff } from 'lucide-react'

/** Bannière affichée quand un appel /api échoue — jamais de page silencieusement vide,
    un visiteur doit comprendre que c'est temporaire, pas que le produit est vide. */
export default function ApiError({ retry }: { retry?: () => void }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center my-6">
      <CloudOff className="w-8 h-8 text-amber-500 mx-auto mb-2" />
      <p className="font-semibold text-ink">Helios est momentanément indisponible.</p>
      <p className="text-sm text-gray-600 mt-1">
        Nos services ne répondent pas — cela ne vient pas de vous. Réessayez dans un instant.
      </p>
      {retry && (
        <button
          onClick={retry}
          className="mt-4 rounded-xl bg-primary text-white text-sm font-semibold px-5 py-2 hover:opacity-90"
        >
          Réessayer
        </button>
      )}
    </div>
  )
}
