import { useEffect } from 'react'

/** Définit le titre de l'onglet par page (SEO / partage). */
export function useTitle(title?: string) {
  useEffect(() => {
    document.title = title
      ? `${title} — HELIOS`
      : 'HELIOS — La maison a enfin son expert'
  }, [title])
}
