import { useEffect } from 'react'

/** Définit le titre de l'onglet par page (SEO / partage). */
export function useTitle(title?: string) {
  useEffect(() => {
    document.title = title
      ? `${title} — HELIOS`
      : 'HELIOS — Votre maison mérite un conseil franc'
  }, [title])
}
