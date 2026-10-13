/**
 * Tout ce qui se pose SUR l'illustration de la scène : repères, rotors, ancres de flux,
 * fenêtres qui s'allument la nuit.
 *
 * UNE SEULE UNITÉ DANS CE FICHIER : le pixel de l'image source (1584 × 672). C'est le
 * repère du `viewBox` de la scène, donc aussi celui des flux et des rotors — un chiffre
 * relevé sur l'image se recopie ici tel quel, et tout grandit ensemble quand la scène
 * change de taille.
 *
 * NE PAS passer en pourcentages de la largeur du conteneur : les flux et les rotors
 * vivent dans le repère SVG, un calque HTML en pourcentage serait un SECOND système de
 * coordonnées, et les deux dériveraient l'un de l'autre au premier changement d'image.
 *
 * POUR RECALER UN REPÈRE : ouvrir le simulateur avec `?calibrage=1`, cliquer sur la
 * scène, les coordonnées s'affichent et partent dans le presse-papiers.
 */

/** Les dimensions de `/maison-demain-v2.webp`. Le viewBox montre l'image entière. */
export const IMAGE = { w: 1584, h: 672 } as const

/** Rayon du repère, et taille du chiffre qu'il porte, en pixels de l'image source. */
export const RAYON_REPERE = 34

/**
 * Où se pose le repère de chaque emplacement.
 *
 * UN REPÈRE NE DOIT PAS COUVRIR CE QU'IL DÉSIGNE. Quatre objets sont plus petits que la
 * pastille (le puits canadien, le disque d'inertie, la machine à eau, la voiture) : leur
 * repère est posé À CÔTÉ, sur la pelouse, et non dessus — sinon on clique sur un objet
 * qu'on ne voit plus. Les grands objets (le toit, le carport, la piscine, le potager)
 * gardent le leur au centre, ils restent reconnaissables en dessous.
 *
 * Relevés sur la nouvelle illustration le 01/10/2026. Trois n'ont pas d'objet dessiné et
 * sont marqués : la batterie virtuelle (c'est le propos : elle est « dans le nuage »),
 * l'eau chaude (le circuit orange en tient lieu) et le raccordement, qui n'a VOLONTAIREMENT
 * plus de repère — sa vignette est devenue un raccourci vers les réglages (voir
 * `SimulateurSolaire.tsx`). Un emplacement absent d'ici n'affiche simplement pas de repère.
 */
export const POSITIONS: Record<string, { x: number; y: number }> = {
  panneaux: { x: 640, y: 108 },           // la nappe bleue du toit
  carport: { x: 250, y: 262 },            // le toit du carport, qui existe vraiment maintenant
  eolienne: { x: 1150, y: 248 },          // juste au-dessus des trois rotors
  eau: { x: 960, y: 495 },                // A COTE du boitier bleu a la goutte (AWG)
  // A COTE du coffret vert, sur le mur : le coffret ne fait que 29 px de large quand la
  // pastille en fait 68, elle le recouvrait entierement — et avec lui la jauge de charge
  // ajoutee le 12/10/2026. Meme regle que le puits, le disque, la machine a eau et la
  batterie: { x: 520, y: 402 },
  inertie: { x: 750, y: 520 },            // A COTE du disque de beton pose sur la pelouse
  batterie_virtuelle: { x: 250, y: 152 }, // dans le ciel : elle n'a pas d'objet, c'est le propos
  ballon: { x: 770, y: 200 },             // approximatif : sur le circuit orange (chaleur)
  clim: { x: 872, y: 321 },               // l'unite interieure, derriere la baie
  piscine: { x: 600, y: 478 },            // le bassin
  voiture: { x: 170, y: 425 },            // A COTE de la voiture, au pied du carport
  puits_canadien: { x: 1090, y: 592 },    // A COTE de l'embouchure qui sort de la pelouse
  jardin: { x: 1250, y: 478 },            // les planches du potager
  energie: { x: 82, y: 152 },             // le poteau electrique, en haut a gauche
}

/**
 * Les trois rotors des éoliennes verticales, relevés sur l'image source.
 *
 * COMMENT ÇA TOURNE : on redécoupe le rotor dans l'image elle-même et on l'écrase
 * horizontalement, en rythme. Une pale hélicoïdale vue de côté fait exactement cela en
 * tournant — elle s'affine de profil, s'élargit de face. Pas de redessin, donc pas de
 * dédoublement avec le trait d'origine ; pas de cache blanc non plus, qui ferait un trou
 * dans le mur strié derrière la première.
 *
 * Les tuyaux d'eau bleus descendent PILE au centre des rotors 2 et 3 : à l'écrasement ils
 * ne bougent donc quasiment pas. C'est ce qui permet de prendre le rotor entier plutôt que
 * de couper au-dessus d'eux, ce qui aurait laissé un haut de pale immobile.
 */
export const ROTORS = [
  { x0: 1046, x1: 1082, y0: 278, y1: 380 },
  { x0: 1104, x1: 1143, y0: 282, y1: 382 },
  { x0: 1165, x1: 1206, y0: 282, y1: 380 },
] as const

/**
 * Le soleil du décor : son halo s'y accroche, et les rayons animés en partent.
 *
 * IL EST SEUL DEPUIS LE 12/10/2026. Les trois autres ancres (maison, batterie, réseau)
 * ne servaient qu'aux cinq arcs de flux, supprimés ce jour-là — voir l'en-tête de
 * `SceneMaison.tsx`. Les rouvrir n'aurait de sens que si ces arcs revenaient.
 */
export const ANCRE = {
  soleil: { x: 390, y: 40 },
} as const

/** Les vitrages qui s'allument quand la scène passe en mode nuit. */
export const FENETRES = [
  { cx: 910, cy: 150, rx: 95, ry: 55 },  // l'etage
  { cx: 840, cy: 338, rx: 145, ry: 58 }, // le sejour et la salle a manger
  { cx: 960, cy: 330, rx: 70, ry: 55 },  // le salon, cote droit
] as const
