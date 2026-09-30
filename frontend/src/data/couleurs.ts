/**
 * La palette, en hexadecimal, pour ce que le CSS ne peut pas habiller.
 *
 * Les couleurs du site vivent dans `src/index.css` (variables `--h-*`) et se
 * posent par des classes Tailwind. Restent les dessins SVG du simulateur et les
 * portraits : leurs `fill` et `stroke` sont des attributs de presentation, ou
 * `var(--h-accent)` n'est pas resolu de maniere fiable par les navigateurs. Ces
 * quelques valeurs sont donc recopiees ici — un seul fichier, a tenir a jour
 * EN MEME TEMPS que `index.css` si la palette bouge.
 */
export const COULEURS = {
  sable: '#F5EFE4',
  sable2: '#EDE3D1',
  bord: '#E2D8C6',
  ink: '#1B2A2F',
  nuit: '#121D21',
  texte2: '#4A5A5F',
  accent: '#A8420F',
  accentFonce: '#8F3A0D',
  or: '#F2B45A',
  bleu: '#2F6F8F',
  vert: '#2F7A5B',
  blanc: '#FFFFFF',
} as const
