import { COULEURS } from '../data/couleurs'

/**
 * Portrait d'un conseiller — DESSINÉ, pas photographié.
 *
 * Pourquoi pas une photo de banque d'images : parce qu'elle serait fausse. Mettre le
 * visage d'un inconnu sous le nom d'un conseiller Helios, c'est exactement ce que la
 * charte interdit ailleurs. Et une photo achetée se reconnaît — on l'a vue sur trente
 * sites d'assurance.
 *
 * Ces portraits sont donc des SILHOUETTES, visiblement dessinées, dans les couleurs de la
 * marque. Elles tiennent la place de vraies photos sans prétendre en être. Le jour où
 * Stéphane fournit les vraies, on remplace ce composant par une balise `img` : les cartes
 * n'ont rien d'autre à changer.
 */

/** Quatre déclinaisons, pour que les visages ne se ressemblent pas. */
const TEINTES = [
  { fond: '#EDE3D1', peau: '#E8B88A', cheveux: '#3D2B1F', vetement: COULEURS.bleu },
  { fond: '#E4EBE7', peau: '#C98D63', cheveux: '#1D1410', vetement: COULEURS.vert },
  { fond: '#F1E4D8', peau: '#F0C9A6', cheveux: '#8A5A2B', vetement: COULEURS.accent },
  { fond: '#E3EAED', peau: '#9C6B45', cheveux: '#2A1C13', vetement: COULEURS.ink },
] as const

export default function AvatarExpert({
  variante, taille = 96, className = '',
}: { variante: number; taille?: number; className?: string }) {
  const t = TEINTES[variante % TEINTES.length]
  // Cheveux : une frange plus ou moins couvrante selon la variante, pour varier les visages.
  const frange = variante % 2 === 0
  return (
    <svg viewBox="0 0 100 100" width={taille} height={taille} className={className}
      role="img" aria-label="Portrait d'illustration">
      <circle cx="50" cy="50" r="50" fill={t.fond} />
      {/* Épaules */}
      <path d="M 16 100 Q 20 72 50 72 Q 80 72 84 100 Z" fill={t.vetement} />
      {/* Col */}
      <path d="M 41 73 L 50 84 L 59 73" fill="none" stroke={t.fond} strokeWidth="3"
        strokeLinecap="round" strokeLinejoin="round" />
      {/* Cou */}
      <rect x="44" y="57" width="12" height="16" rx="6" fill={t.peau} />
      {/* Visage */}
      <ellipse cx="50" cy="42" rx="17" ry="20" fill={t.peau} />
      {/* Cheveux */}
      {frange ? (
        <path d="M 33 40 Q 33 20 50 20 Q 67 20 67 40 Q 60 30 50 32 Q 40 30 33 40 Z" fill={t.cheveux} />
      ) : (
        <path d="M 32 44 Q 30 19 50 19 Q 70 19 68 44 Q 66 28 50 27 Q 34 28 32 44 Z" fill={t.cheveux} />
      )}
      {/* Yeux et sourire — le minimum pour que ce soit quelqu'un, pas un pictogramme */}
      <circle cx="43.5" cy="42" r="1.9" fill={COULEURS.ink} />
      <circle cx="56.5" cy="42" r="1.9" fill={COULEURS.ink} />
      <path d="M 44 50 Q 50 54 56 50" fill="none" stroke={COULEURS.ink} strokeWidth="1.8"
        strokeLinecap="round" />
    </svg>
  )
}
