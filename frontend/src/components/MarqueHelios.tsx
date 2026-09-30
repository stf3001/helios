/**
 * La marque Helios : un soleil au trait fin.
 *
 * Elle remplace la mascotte casquee (`/brand/poses/*.png`, supprimee le
 * 30/09/2026) partout ou le produit doit se nommer : en-tete, pied de page,
 * conversation, back-office. Un seul fichier, pour que le jour ou le dessin
 * change, il ne change qu'a un endroit.
 *
 * Le trait suit `currentColor` : la marque prend la couleur de son contexte
 * (terracotta sur fond clair, ivoire sur fond sombre) sans variante a declarer.
 *
 * `anime` fait respirer le halo et tourner lentement la couronne — utilise
 * uniquement quand Helios travaille (etat « reflexion » de la conversation).
 * Les deux animations sont coupees si l'utilisateur demande moins de mouvement
 * (regles `helios-pulse` / `helios-tourne` dans `index.css`).
 */
export default function MarqueHelios({
  taille = 28,
  anime = false,
  className = '',
}: {
  taille?: number
  anime?: boolean
  className?: string
}) {
  // Huit rayons, poses par rotation autour du centre plutot qu'ecrits un par un :
  // l'espacement reste exact si l'on en ajoute ou en retire.
  const rayons = Array.from({ length: 8 }, (_, i) => i * 45)

  return (
    <svg
      width={taille}
      height={taille}
      viewBox="0 0 32 32"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <g className={anime ? 'helios-tourne' : undefined}>
        {rayons.map((angle) => (
          <line
            key={angle}
            x1="16"
            y1="3.2"
            x2="16"
            y2="6.8"
            transform={`rotate(${angle} 16 16)`}
          />
        ))}
      </g>
      <circle cx="16" cy="16" r="6.6" />
      <circle cx="16" cy="16" r="9.6" opacity="0.35" className={anime ? 'helios-pulse' : undefined} />
    </svg>
  )
}
