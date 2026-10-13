/**
 * Une animation par équipement, et rien d'autre.
 *
 * POURQUOI CE FICHIER EXISTE — le 12/10/2026, la scène n'avait que deux animations : le
 * pointillé des flux (une liaison, pas un équipement) et les rotors des éoliennes. Poser
 * quatorze équipements et n'en voir bouger qu'un seul donnait une scène morte. Le pointillé
 * est parti, les rotors restent dans `SceneMaison`, et tout le reste est ici.
 *
 * LA RÈGLE QUI TIENT L'ENSEMBLE : une animation ne joue QUE si l'équipement est installé.
 * C'est la récompense du clic — on ajoute la piscine, l'eau se met à onduler. Rien ne bouge
 * tant qu'on n'a rien posé, et la scène ne bout pas quand tout est posé parce que chaque
 * boucle est lente (3 à 9 s), discrète, et décalée des autres.
 *
 * CE QUI NE DÉPEND PAS DE LA SAISON (demande de Stéphane, 12/10/2026) : absolument tout.
 * La climatisation souffle du bleu en janvier comme en juillet, le puits canadien sort du
 * bleu ET de l'orange ensemble. Seuls les rayons du soleil s'éteignent la nuit, parce que
 * le soleil lui-même disparaît sous le voile nocturne — c'est la règle du décor, pas une
 * règle de saison.
 *
 * COORDONNÉES : pixels de l'image source (1584 × 672), comme `reperes.ts`. Elles ont été
 * relevées objet par objet sur l'illustration. Pour en recaler une : ouvrir le simulateur
 * avec `?calibrage=1`, cliquer, les chiffres partent dans le presse-papiers.
 *
 * ELLES VIVENT ICI ET NON DANS `reperes.ts` : chacune ne sert qu'à l'animation qui la suit
 * immédiatement. `reperes.ts` garde ce que PLUSIEURS parties de la scène se partagent
 * (l'image, les repères, les ancres de flux, les rotors).
 *
 * TOUT EST EN `transform` ET `opacity`, plus `stroke-dashoffset` sur des traits courts :
 * quatorze boucles simultanées ne coûtent rien tant qu'on ne touche ni à la géométrie ni
 * aux filtres. Les keyframes sont dans `index.css`, toutes neutralisées sous
 * `prefers-reduced-motion`.
 */

import { COULEURS } from '../../data/couleurs'

/** Le soleil de l'illustration, d'où partent les rayons. */
const SOLEIL = { x: 386, y: 32, r: 30 }

/** Un peu de bois, repris des bacs du potager pour que le support n'ait pas l'air rapporté. */
const BOIS = { clair: '#D9B176', fonce: '#A9813F' }

/* ------------------------------------------------------------------ 1 et 2. Les rayons */

/**
 * Des rayons fins qui descendent du soleil jusqu'aux panneaux. Le trait ne reste pas
 * affiché : c'est une comète courte qui parcourt le rayon, puis recommence.
 *
 * `pathLength={100}` est la clé : le pointillé s'exprime alors en CENTIÈMES DE RAYON, donc
 * la même classe CSS marche sur un rayon long (le toit) comme sur un rayon court (le
 * carport), sans recalculer quoi que ce soit.
 */
function Rayons({ cibles, cle }: { cibles: { x: number; y: number }[]; cle: string }) {
  return (
    <g>
      {cibles.map((c, i) => {
        // Le rayon part du BORD du soleil, pas de son centre : sinon il naît sous le dessin.
        const dx = c.x - SOLEIL.x
        const dy = c.y - SOLEIL.y
        const n = Math.hypot(dx, dy)
        const x0 = SOLEIL.x + (dx / n) * SOLEIL.r
        const y0 = SOLEIL.y + (dy / n) * SOLEIL.r
        const d = `M ${x0.toFixed(0)} ${y0.toFixed(0)} L ${c.x} ${c.y}`
        return (
          <g key={`${cle}-${i}`}>
            {/* LE RAYON ENTIER, FIXE ET PÂLE. Sans lui, la comète seule est un segment
                orange qui flotte dans le ciel : c'est le trait continu qui la relie au
                soleil et en fait un rayon. L'illustration dessine les siens de la même
                façon — quatre rayons pleins qui finissent sur un éclat. */}
            <path d={d} fill="none" stroke={COULEURS.or} strokeWidth={2} strokeOpacity={0.3}
              strokeLinecap="round" />
            <path d={d} pathLength={100} fill="none" stroke={COULEURS.or} strokeWidth={3.5}
              strokeLinecap="round" strokeDasharray="26 74" className="sc-comete"
              style={{ animationDuration: `${2.6 + i * 0.35}s`, animationDelay: `${-i * 0.9}s` }} />
          </g>
        )
      })}
    </g>
  )
}

/** Quatre points relevés sur la nappe bleue du toit, répartis de gauche à droite. */
const CIBLES_TOIT = [
  { x: 570, y: 118 }, { x: 660, y: 100 }, { x: 750, y: 85 }, { x: 818, y: 72 },
]

/** Trois points sur le toit du carport. Ils restent à gauche : un rayon visant plus à
 *  droite traverserait les jardinières du toit végétalisé. */
const CIBLES_CARPORT = [
  { x: 210, y: 287 }, { x: 282, y: 274 }, { x: 352, y: 252 },
]

/* ----------------------------------------------------------------- 4. La machine à eau */

/**
 * LA FONTAINE. Deuxième version, 12/10/2026 : la première posait la machine sur un
 * plateau de bois à pieds, et c'était minable — un tréteau sous un appareil, et surtout
 * aucune place pour voir l'eau couler, puisque la machine touche l'herbe (y = 508).
 *
 * LE PRINCIPE QUI RÈGLE TOUT : la vasque est DEVANT la machine, pas dessous. Son rim
 * (ellipse 1070, 500) recouvre les 20 derniers pixels de la machine, qui n'a donc plus de
 * pied posé dans l'herbe : elle émerge de derrière la vasque, comme la colonne d'une
 * fontaine. Rien n'a été déplacé, rien n'a été masqué, et il reste 22 px de chute entre le
 * bec et l'eau — c'est ce qui manquait pour que « ça coule » se voie.
 *
 * Ce qu'elle ÉVITE, et qu'il ne faut pas réintroduire en l'élargissant : la bouche du
 * puits canadien (1023-1055 × 521-535) passe à 3 px sous le bord gauche de la vasque, et
 * les cuves des éoliennes (1045-1096 × 402-440) sont juste au-dessus de la machine.
 *
 * La vasque est dessinée EN PERMANENCE, l'eau seulement quand la machine est installée :
 * une fontaine à sec dit aussi bien les choses qu'un meuble qui disparaîtrait.
 */
function MachineEau({ installe }: { installe: boolean }) {
  const blanc = { fill: COULEURS.blanc, stroke: COULEURS.texte2, strokeWidth: 2 }
  return (
    <g>
      {/* Le fût et le pied, dessinés avant la vasque : elle les coiffe. */}
      <path d="M 1061 524 L 1079 524 L 1077 554 L 1063 554 Z" {...blanc} strokeLinejoin="round" />
      <ellipse cx={1070} cy={557} rx={26} ry={7} {...blanc} />
      {/* La panse de la vasque : entre le bord avant et le dessous. */}
      <path d="M 1026 500 A 44 11 0 0 0 1114 500 Q 1070 560 1026 500 Z" {...blanc}
        strokeLinejoin="round" />
      {/* L'ouverture, vue de dessus. */}
      <ellipse cx={1070} cy={500} rx={44} ry={11} {...blanc} />

      {installe && (
        <g>
          {/* L'eau du bassin, et l'onde qui part du point de chute. */}
          <ellipse cx={1070} cy={501} rx={37} ry={8.5} fill={COULEURS.bleu} fillOpacity={0.4} />
          <g clipPath="url(#sc-vasque)">
            <ellipse cx={1070} cy={501} rx={30} ry={7} fill="none" stroke={COULEURS.blanc}
              strokeWidth={2.5} className="sc-onde"
              style={{ transformOrigin: '1070px 501px' }} />
            <ellipse cx={1070} cy={501} rx={30} ry={7} fill="none" stroke={COULEURS.blanc}
              strokeWidth={2.5} className="sc-onde"
              style={{ transformOrigin: '1070px 501px', animationDelay: '-1.4s' }} />
          </g>
          {/* Le bec, ajouté sur la face avant de la machine : elle n'en avait pas. */}
          <path d="M 1058 468 L 1070 468 L 1070 474" fill="none" stroke={COULEURS.texte2}
            strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
          {/* Le filet : un trait CONTINU — elle verse sans discontinuer — et une comète
              par-dessus, qui seule dit que ça coule. */}
          <path d="M 1070 474 L 1070 496" fill="none" stroke={COULEURS.bleu} strokeWidth={2.5}
            strokeOpacity={0.7} strokeLinecap="round" />
          <path d="M 1070 474 L 1070 496" pathLength={100} fill="none" stroke={COULEURS.bleu}
            strokeWidth={3.5} strokeLinecap="round" strokeDasharray="30 70"
            className="sc-comete" style={{ animationDuration: '0.9s' }} />
        </g>
      )}
    </g>
  )
}

/* ------------------------------------------------------------------- 5. La batterie */

/**
 * Le coffret vert contre le mur du garage (443-472 × 332-420) : trois segments qui se
 * remplissent de bas en haut.
 *
 * Le remplissage suit L'HEURE AFFICHÉE : il monte quand le soleil charge la batterie,
 * descend quand elle rend son énergie à la maison. Aux heures où elle ne fait ni l'un ni
 * l'autre, elle respire lentement — on ne connaît pas son état de charge réel, et le
 * dessin ne prétend pas le donner.
 */
function Batterie({ charge, decharge }: { charge: number; decharge: number }) {
  const sens = charge > 0.05 ? 'charge' : decharge > 0.05 ? 'decharge' : 'repos'
  return (
    <g>
      <rect x={445} y={336} width={27} height={82} rx={2}
        fill={COULEURS.vert} fillOpacity={0.5}
        className="sc-jauge"
        style={{
          transformOrigin: '445px 418px',
          animationDuration: sens === 'repos' ? '8s' : '3.6s',
          animationDirection: sens === 'decharge' ? 'reverse' : undefined,
        }} />
      {/* Les deux séparations, par-dessus : c'est ce qui fait lire trois segments plutôt
          qu'un bloc vert qui monte. */}
      <path d="M 445 364 H 472 M 445 391 H 472" stroke={COULEURS.sable} strokeWidth={3}
        strokeOpacity={0.85} />
    </g>
  )
}

/* -------------------------------------------------------------------- 6. L'inertie */

/**
 * Le disque de béton sur la pelouse (centre 851, 504 ; rayons 59 × 9).
 *
 * Le béton est UNI : le faire tourner ne se verrait pas. C'est un reflet qui balaie son
 * flanc, toujours dans le même sens, qui dit la rotation.
 */
function Inertie() {
  return (
    <g clipPath="url(#sc-inertie)">
      <rect x={770} y={500} width={46} height={36} fill="url(#sc-eclat)"
        className="sc-inertie-reflet" />
    </g>
  )
}

/* ------------------------------------------------------- 7. La batterie virtuelle */

/** Elle n'a pas d'objet dans le décor : c'est le propos. On lui dessine son nuage, et
 *  l'énergie y monte puis en redescend. */
function BatterieVirtuelle() {
  return (
    <g>
      <g fill={COULEURS.blanc} fillOpacity={0.92} stroke={COULEURS.texte2} strokeWidth={2.5}>
        <path d="M 214 68 a 17 17 0 0 1 30 -13 a 20 20 0 0 1 36 6 a 15 15 0 0 1 -2 29
                 L 224 90 a 13 13 0 0 1 -10 -22 Z" />
      </g>
      {[228, 250, 272].map((x, i) => (
        <circle key={x} cx={x} cy={114} r={5} fill={COULEURS.bleu} className="sc-nuage-point"
          style={{ animationDelay: `${-i * 2}s` }} />
      ))}
    </g>
  )
}

/* ---------------------------------------------------------------- 8. L'eau chaude */

/** Une onde tiède descend le circuit orange DÉJÀ DESSINÉ, du toit jusqu'à la bouche de
 *  chaleur du séjour. Le tracé suit le tuyau de l'illustration, il ne le double pas. */
function EauChaude() {
  return (
    <path
      d="M 696 158 L 696 245 Q 696 253 704 253 L 814 253 Q 822 253 822 261 L 822 310"
      pathLength={100} fill="none" stroke={COULEURS.accent} strokeWidth={7}
      strokeLinecap="round" strokeOpacity={0.95} strokeDasharray="16 84"
      className="sc-comete" style={{ animationDuration: '5s' }} />
  )
}

/* ------------------------------------------------------------ 9. La climatisation */

/** La console intérieure (877-953 × 288-316) souffle trois volutes qui s'effacent.
 *  BLEU TOUTE L'ANNÉE : le froid est ce qu'on lui demande, et la scène ne change pas
 *  de couleur avec la saison. */
function Clim() {
  return (
    <g stroke={COULEURS.bleu} strokeWidth={3} fill="none" strokeLinecap="round" opacity={0.75}>
      {[0, 1, 2].map((i) => (
        <path key={i} d={`M ${910 + i * 19} 318 q -9 9 -4 17 q 5 8 -3 16`}
          className="sc-souffle" style={{ animationDelay: `${-i * 1.1}s` }} />
      ))}
    </g>
  )
}

/* ---------------------------------------------------------------- 10. La piscine */

/** Des reflets dérivent sur la surface. Découpés au bassin : rien ne déborde sur la
 *  pelouse, quelle que soit la dérive. */
function Piscine() {
  const reflets = [
    { d: 'M 470 474 q 26 -5 52 0 q 26 5 52 0', duree: 9, delai: 0 },
    { d: 'M 520 490 q 30 -5 60 0 q 30 5 60 0', duree: 11, delai: -3 },
    { d: 'M 600 468 q 24 -4 48 0 q 24 4 48 0', duree: 8, delai: -5 },
    { d: 'M 640 502 q 28 -5 56 0 q 28 5 56 0', duree: 12, delai: -7 },
  ]
  return (
    <g clipPath="url(#sc-piscine)" fill="none" stroke={COULEURS.blanc} strokeWidth={4}
      strokeLinecap="round">
      {reflets.map((r) => (
        <path key={r.d} d={r.d} className="sc-reflet"
          style={{ animationDuration: `${r.duree}s`, animationDelay: `${r.delai}s` }} />
      ))}
    </g>
  )
}

/* ----------------------------------------------------------------- 11. La voiture */

/** La borne clignote et le câble vert s'éclaire par vagues, de la borne vers la voiture.
 *  Le câble suit celui qui est dessiné, de la borne (405, 377) à la roue avant. */
function Voiture() {
  return (
    <g>
      <rect x={404} y={344} width={10} height={12} rx={2} fill={COULEURS.vert}
        className="sc-temoin" />
      <path d="M 406 377 C 410 396 404 414 388 419" pathLength={100} fill="none"
        stroke="#3BD16F" strokeWidth={5} strokeLinecap="round" strokeDasharray="22 78"
        className="sc-comete" style={{ animationDuration: '2.8s' }} />
    </g>
  )
}

/* ----------------------------------------------------------- 12. Le puits canadien */

/**
 * Dehors, l'air descend dans la bouche d'aspiration (1037, 521). Dedans, il ressort par
 * la grille basse du séjour (640-687 × 355-367) — un filet bleu ET un filet orange, parce
 * que le même tuyau rafraîchit l'été et préchauffe l'hiver, et que la scène ne choisit
 * pas une saison.
 */
function PuitsCanadien() {
  return (
    <g fill="none" strokeWidth={3} strokeLinecap="round">
      {/* TROIS FILETS HORIZONTAUX QUI RENTRENT DANS LA BOUCHE, depuis l'herbe à sa
          gauche. Troisième réglage (12/10/2026) : Stéphane ne voyait RIEN à l'écran.
          Trois raisons, toutes corrigées ici — ils étaient trop fins et à moitié effacés
          (4 px, palier d'opacité au lieu d'un pic) ; ils tombaient SOUS la pastille
          « Machine à eau » (960, 495), qui occupe toute l'herbe au-dessus (y < 529) ; et
          ils descendaient à la verticale à côté de la bouche au lieu d'y entrer.
          Au-dessus d'elle il n'y a que la machine, à sa droite le pied de la fontaine :
          la gauche est le seul côté libre. */}
      <g stroke={COULEURS.bleu} strokeWidth={4}>
        <path d="M 958 532 q 13 -5 26 0 q 13 5 24 0" className="sc-aspire" />
        <path d="M 952 541 q 13 -5 26 0 q 13 5 24 0" className="sc-aspire"
          style={{ animationDelay: '-1.2s' }} />
        <path d="M 962 550 q 13 -5 26 0 q 13 5 24 0" className="sc-aspire"
          style={{ animationDelay: '-2.4s' }} />
      </g>
      <path d="M 651 356 q -7 -11 -1 -20 q 6 -9 0 -18" stroke={COULEURS.bleu}
        className="sc-filet" />
      <path d="M 673 356 q 7 -11 1 -20 q -6 -9 0 -18" stroke={COULEURS.accent}
        className="sc-filet" style={{ animationDelay: '-2.2s' }} />
    </g>
  )
}

/* ------------------------------------------------------------------- 13. Le jardin */

/**
 * Le goutte-à-goutte du bac de devant, celui dont la terre est nue et où une goutte se
 * voit tomber. Chaque goutte laisse une tache humide qui sèche.
 */
/** Le tuyau longe LE BORD AVANT du bac, là où la terre est nue. Plus haut, il barrait la
 *  courgette et les grandes feuilles — un bâton bleu posé en travers du dessin. */
const GOUTTES = [
  { x: 1365, haut: 545, sol: 555 },
  { x: 1398, haut: 553, sol: 563 },
  { x: 1433, haut: 562, sol: 572 },
]

function Jardin() {
  return (
    <g>
      <path d="M 1332 536 Q 1398 551 1462 570" fill="none" stroke={COULEURS.bleu}
        strokeWidth={2.2} strokeOpacity={0.55} strokeLinecap="round" />
      {GOUTTES.map((g, i) => (
        <g key={g.x}>
          <ellipse cx={g.x} cy={g.haut} rx={3} ry={4.5} fill={COULEURS.bleu}
            className="sc-goutte" style={{ animationDelay: `${-i * 1.3}s` }} />
          <ellipse cx={g.x} cy={g.sol + 2} rx={7} ry={2.5} fill="#5B4028" fillOpacity={0.5}
            className="sc-tache" style={{ animationDelay: `${-i * 1.3}s` }} />
        </g>
      ))}
    </g>
  )
}

/* ------------------------------------------------------------ 15. L'achat d'énergie */

/** Une pulsation descend le fil, du poteau vers la maison. TOUJOURS DANS CE SENS : la
 *  vignette dit « achat d'énergie », et l'injection se raconte ailleurs. */
function Poteau() {
  return (
    <path d="M 107 85 Q 280 140 437 103" pathLength={100} fill="none" stroke={COULEURS.bleu}
      strokeWidth={4} strokeOpacity={0.9} strokeLinecap="round" strokeDasharray="12 88"
      className="sc-comete" style={{ animationDuration: '3.6s' }} />
  )
}

/* ------------------------------------------------------------------------ L'ensemble */

interface Props {
  /** Les identifiants des équipements installés — l'animation est la récompense du clic. */
  poses: Set<string>
  nuit: boolean
  /** Ce que le soleil envoie à la batterie, et ce que la batterie rend à la maison, à
   *  l'heure affichée : c'est ce qui donne le sens de la jauge. */
  batterieCharge: number
  batterieDecharge: number
}

export default function AnimationsEquipements({
  poses, nuit, batterieCharge, batterieDecharge,
}: Props) {
  const pose = (id: string) => poses.has(id)
  return (
    <g>
      <defs>
        {/* Le bassin, relevé sur l'illustration : les reflets ne sortent jamais de l'eau. */}
        <clipPath id="sc-piscine">
          <polygon points="437,461 800,453 782,517 455,512" />
        </clipPath>
        {/* L'éclat qui balaie le disque : un dégradé et non un aplat, sinon c'est un
            rectangle blanc qui glisse — les bords francs se voyaient. */}
        <linearGradient id="sc-eclat" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={COULEURS.blanc} stopOpacity="0" />
          <stop offset="50%" stopColor={COULEURS.blanc} stopOpacity="0.7" />
          <stop offset="100%" stopColor={COULEURS.blanc} stopOpacity="0" />
        </linearGradient>
        {/* Le flanc du disque d'inertie, entre son dessus et son dessous. Relevé au pixel :
            ellipse (851, 506), rayons 58 × 13, flanc haut de 11 px. */}
        <clipPath id="sc-inertie">
          <path d="M 793 506 A 58 13 0 0 0 910 506 L 910 517 A 58 13 0 0 1 793 517 Z" />
        </clipPath>
        {/* Le plan d'eau de la vasque : l'onde ne déborde jamais du bassin. */}
        <clipPath id="sc-vasque">
          <ellipse cx={1070} cy={501} rx={37} ry={8.5} />
        </clipPath>
      </defs>

      {/* Les rayons ne jouent pas la nuit : le soleil dont ils partent n'est plus là. */}
      {!nuit && pose('panneaux') && <Rayons cibles={CIBLES_TOIT} cle="toit" />}
      {!nuit && pose('carport') && <Rayons cibles={CIBLES_CARPORT} cle="carport" />}

      <MachineEau installe={pose('eau')} />
      {pose('batterie') && <Batterie charge={batterieCharge} decharge={batterieDecharge} />}
      {pose('inertie') && <Inertie />}
      {pose('batterie_virtuelle') && <BatterieVirtuelle />}
      {pose('ballon') && <EauChaude />}
      {pose('clim') && <Clim />}
      {pose('piscine') && <Piscine />}
      {pose('voiture') && <Voiture />}
      {pose('puits_canadien') && <PuitsCanadien />}
      {pose('jardin') && <Jardin />}
      {pose('energie') && <Poteau />}
    </g>
  )
}
