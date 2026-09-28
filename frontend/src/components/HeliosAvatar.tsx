import { useEffect, useRef, useState } from 'react'

/**
 * Avatar animé d'Helios.
 *
 * Principe : la mascotte n'est pas dessinée en SVG mais composée de trois poses
 * PNG au trait (bras croisés / pouce levé / main au casque) dont le VISAGE EST
 * VIDE. Les yeux et la bouche sont posés par-dessus en SVG, aux coordonnées
 * relevées sur chaque image — c'est ce qui permet de changer d'expression sans
 * multiplier les fichiers, et de garder un poids d'assets minimal.
 *
 * Les mouvements sont des keyframes CSS déclarées dans `index.css`
 * (`hBreathe`, `hNod`, `hWave`…), désactivées si l'utilisateur a demandé moins
 * de mouvement.
 */

/** Boîte du visage relevée sur chaque PNG (en % de l'image) — mesurée sur les
 *  pixels, pas estimée à l'œil : c'est la zone blanche fermée sous le casque. */
type Pose = {
  src: string
  /** largeur / hauteur de l'image, pour dimensionner le cadre sans le déformer */
  ratio: number
  face: { x0: number; x1: number; y0: number; y1: number }
}

const POSES = {
  crossed: { src: '/brand/poses/crossed.png', ratio: 340 / 669, face: { x0: 27.6, x1: 75.0, y0: 16.6, y1: 35.3 } },
  thumbsup: { src: '/brand/poses/thumbsup.png', ratio: 394 / 670, face: { x0: 29.2, x1: 72.1, y0: 16.6, y1: 35.8 } },
  salute: { src: '/brand/poses/salute.png', ratio: 370 / 667, face: { x0: 35.4, x1: 79.5, y0: 16.5, y1: 35.2 } },
  hero: { src: '/brand/poses/hero.png', ratio: 764 / 1205, face: { x0: 25.1, x1: 62.7, y0: 15.1, y1: 33.8 } },
} satisfies Record<string, Pose>

export type HeliosPose = keyof typeof POSES

/** Les états sont nommés côté produit (ce qu'Helios *vit*), pas côté animation. */
export type HeliosState =
  | 'repos'
  | 'attention'
  | 'salutation'
  | 'ecoute'
  | 'reflexion'
  | 'reponse'
  | 'nesaitpas'
  | 'erreur'
  | 'succes'

type Expression = 'calm' | 'smile' | 'happy' | 'unsure' | 'sad'

type StateDef = {
  pose: HeliosPose
  expr: Expression
  /** Nom de base de la keyframe (les variantes A/B sont ajoutées à l'exécution). */
  anim?: 'hNod' | 'hWave' | 'hShrug' | 'hHop' | 'hSlump'
  /** Durée de l'animation, en secondes. */
  dur?: number
  /** Accessoire affiché à côté du casque. */
  badge?: 'bulb' | 'question' | 'bang' | 'dots'
  /** État transitoire : on retombe au repos une fois l'animation jouée. */
  transient: boolean
  /** Texte lu par les lecteurs d'écran (l'avatar n'est pas décoratif quand il
   *  porte une information : « je ne sais pas », « erreur »…). */
  label: string
}

const STATES: Record<HeliosState, StateDef> = {
  repos: { pose: 'crossed', expr: 'calm', transient: false, label: 'Helios vous écoute' },
  /* On tape une question : il ne fait rien de spectaculaire, il s'allume. Le sourire et
     le regard qui se pose sur le champ suffisent — un geste ample, tenu pendant toute la
     frappe d'une longue question, deviendrait vite agaçant. */
  attention: { pose: 'crossed', expr: 'smile', transient: false, label: 'Helios vous écoute' },
  salutation: { pose: 'thumbsup', expr: 'happy', anim: 'hWave', dur: 1.1, transient: true, label: 'Helios vous salue' },
  /* Dictée en cours : la main au casque est le geste de celui qui tend l'oreille. Pas
     d'animation de geste — ce qui doit bouger pendant qu'on parle, c'est le micro, pas
     Helios ; il écoute, et la respiration de repos suffit à le montrer vivant. */
  ecoute: { pose: 'salute', expr: 'smile', transient: false, label: 'Helios vous écoute parler' },
  reflexion: { pose: 'crossed', expr: 'calm', badge: 'dots', transient: false, label: 'Helios réfléchit' },
  reponse: { pose: 'thumbsup', expr: 'smile', anim: 'hNod', dur: 0.9, badge: 'bulb', transient: true, label: 'Helios a une réponse' },
  nesaitpas: { pose: 'salute', expr: 'unsure', anim: 'hShrug', dur: 1.4, badge: 'question', transient: true, label: "Helios n'a pas la réponse" },
  erreur: { pose: 'crossed', expr: 'sad', anim: 'hSlump', dur: 1.3, badge: 'bang', transient: true, label: 'Helios a rencontré un problème' },
  succes: { pose: 'thumbsup', expr: 'happy', anim: 'hHop', dur: 0.75, transient: true, label: "Helios valide l'étape" },
}

/** Bleu du trait de la mascotte (relevé sur les PNG) — le visage doit être de la
 *  même encre que le dessin, pas de l'orange de la charte. */
const INK = '#0069CE'

export default function HeliosAvatar({
  state = 'repos',
  height = 260,
  className = '',
  showBadges = true,
  idle = true,
  restPose,
  replay = 0,
  regard = true,
  cible = null,
}: {
  state?: HeliosState
  /** Incrémenter pour rejouer le MÊME état (deux réponses d'affilée, par ex.) :
   *  sans cela, une prop identique ne déclencherait aucune nouvelle animation. */
  replay?: number
  /** Hauteur en pixels (la largeur suit le ratio de la pose). */
  height?: number
  className?: string
  /** Ampoule / « ? » / « ! » / points de réflexion à côté du casque. */
  showBadges?: boolean
  /** Respiration + balancement en boucle. À couper pour une vignette figée. */
  idle?: boolean
  /** Pose de repos (par défaut bras croisés). La pose `hero`, plus large et plus
   *  ouverte, convient aux grandes illustrations de page. */
  restPose?: HeliosPose
  /** Le regard suit le pointeur. À couper pour une vignette décorative. */
  regard?: boolean
  /** Point de l'écran à regarder au lieu du pointeur — le champ de saisie pendant qu'on
   *  y écrit, par exemple. Les mains sont sur le clavier : sans cela, les yeux resteraient
   *  figés là où la souris a été abandonnée. */
  cible?: { x: number; y: number } | null
}) {
  // État réellement affiché : le parent décrit ce qui vient de se passer, le
  // composant se charge de retomber au repos quand l'animation est finie.
  const [current, setCurrent] = useState<HeliosState>(state)
  // Compteur d'occurrences : sert à alterner les keyframes A/B pour rejouer une
  // animation identique deux fois de suite (cf. commentaire dans index.css).
  const [play, setPlay] = useState(0)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    clearTimeout(timer.current)
    setCurrent(state)
    setPlay((p) => p + 1)
    const def = STATES[state]
    if (def.transient) {
      // +1,2 s après le geste : le temps de LIRE l'accessoire (ampoule, « ? »,
      // « ! »). Réglé en regardant l'avatar en grand — à 400 ms, l'ampoule
      // disparaissait avant qu'on l'ait vue.
      timer.current = setTimeout(() => setCurrent('repos'), (def.dur ?? 1) * 1000 + 1200)
    }
    return () => clearTimeout(timer.current)
  }, [state, replay])

  const def = STATES[current]
  // La pose de repos peut être choisie par l'appelant ; les états expressifs
  // gardent la leur, sinon le geste ne voudrait plus rien dire.
  const pose = POSES[current === 'repos' && restPose ? restPose : def.pose]
  const width = Math.round(height * pose.ratio)

  // Repère SVG : 100 unités = la largeur de l'image, la hauteur suit le ratio.
  // Un repère carré (plutôt qu'un viewBox 100×100 étiré) évite que les yeux
  // ronds deviennent des ovales sur une pose plus étroite qu'une autre.
  const vbH = 100 / pose.ratio
  const f = pose.face
  const faceW = f.x1 - f.x0
  const cx = (f.x0 + f.x1) / 2
  const toY = (pct: number) => (pct / 100) * vbH

  // Yeux au tiers haut du visage, bouche aux deux tiers — proportions du dessin.
  const eyeY = toY(f.y0 + (f.y1 - f.y0) * 0.4)
  const mouthY = toY(f.y0 + (f.y1 - f.y0) * 0.7)
  const gap = faceW * 0.26
  const r = faceW * 0.062

  let eyeRx = r
  let eyeRy = r * 1.15
  let eyeCy = eyeY
  let blink = 'hBlink 5.2s ease-in-out infinite'
  let mouth: string
  const m = faceW * 0.11 // demi-largeur de bouche

  if (def.expr === 'happy') {
    // Yeux plissés de contentement : plus de clignement à jouer.
    eyeRx = r * 1.15
    eyeRy = r * 0.35
    eyeCy = eyeY - r * 0.25
    blink = 'none'
    mouth = `M ${cx - m} ${mouthY - 1} Q ${cx} ${mouthY + m * 0.95} ${cx + m} ${mouthY - 1}`
  } else if (def.expr === 'smile') {
    mouth = `M ${cx - m * 0.9} ${mouthY} Q ${cx} ${mouthY + m * 0.75} ${cx + m * 0.9} ${mouthY}`
  } else if (def.expr === 'unsure') {
    // Regard levé + bouche neutre : l'hésitation, sans mimique appuyée.
    eyeCy = eyeY - r * 0.5
    mouth = `M ${cx - m * 0.7} ${mouthY} L ${cx + m * 0.7} ${mouthY}`
  } else if (def.expr === 'sad') {
    mouth = `M ${cx - m * 0.85} ${mouthY + m * 0.45} Q ${cx} ${mouthY - m * 0.35} ${cx + m * 0.85} ${mouthY + m * 0.45}`
  } else {
    mouth = `M ${cx - m * 0.78} ${mouthY} Q ${cx} ${mouthY + m * 0.5} ${cx + m * 0.78} ${mouthY}`
  }

  /* ------------------------------------------------------------------
     LE REGARD

     Les yeux sont deux taches d'encre, sans blanc autour : « suivre » veut donc
     dire les décaler légèrement dans le visage, de l'ordre d'un demi-rayon. Au-delà,
     ils sortent du masque et le personnage louche.

     Le décalage est posé à la main sur un `<g>` dédié, PAS par un état React : à
     chaque mouvement de souris, un rendu complet de l'avatar serait du gâchis. Et ce
     `<g>` est distinct de celui du clignement, qui anime déjà `transform` — les deux
     se marcheraient dessus.

     La cible l'emporte sur le pointeur quand elle est donnée (cf. `cible`).
     ------------------------------------------------------------------ */
  const yeux = useRef<SVGGElement>(null)
  const boite = useRef<HTMLDivElement>(null)
  // Géométrie du visage de la pose courante, relue par l'écouteur sans le réabonner.
  const geo = useRef({ cx: 0, eyeCy: 0, vbH: 0, ampli: 0 })
  geo.current = { cx, eyeCy, vbH, ampli: r * 0.55 }

  const cibleX = cible?.x ?? null
  const cibleY = cible?.y ?? null

  useEffect(() => {
    const sobre = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (!regard || sobre) {
      if (yeux.current) yeux.current.style.transform = ''
      return
    }

    let image = 0
    const viser = (x: number, y: number) => {
      cancelAnimationFrame(image)
      image = requestAnimationFrame(() => {
        const cadre = boite.current?.getBoundingClientRect()
        const g = yeux.current
        if (!cadre || !cadre.width || !g) return
        const { cx: fx, eyeCy: fy, vbH: h, ampli } = geo.current
        // Les yeux, en coordonnées d'écran : le repère SVG fait 100 unités de large.
        const ox = cadre.left + (fx / 100) * cadre.width
        const oy = cadre.top + (fy / h) * cadre.height
        const dx = x - ox
        const dy = y - oy
        const d = Math.hypot(dx, dy)
        if (d < 1) { g.style.transform = ''; return }
        // Amplitude pleine à 360 px : plus loin, le regard ne se creuse plus.
        const force = Math.min(1, d / 360)
        g.style.transform =
          `translate(${(dx / d) * force * ampli}px, ${(dy / d) * force * ampli}px)`
      })
    }

    if (cibleX !== null && cibleY !== null) {
      viser(cibleX, cibleY)
      return () => cancelAnimationFrame(image)
    }

    const surPointeur = (e: PointerEvent) => viser(e.clientX, e.clientY)
    window.addEventListener('pointermove', surPointeur, { passive: true })
    return () => {
      window.removeEventListener('pointermove', surPointeur)
      cancelAnimationFrame(image)
    }
    // `current` : changer de pose change la géométrie du visage, donc le décalage.
  }, [regard, cibleX, cibleY, current])

  const variant = play % 2 ? 'A' : 'B'
  const bodyAnim = def.anim ? `${def.anim}${variant} ${def.dur}s cubic-bezier(.34,1.16,.44,1) both` : 'none'
  const idleAnim = idle ? 'hBreathe 5s ease-in-out infinite, hSway 9s ease-in-out infinite' : 'none'
  const badge = showBadges ? def.badge : undefined
  // L'échelle des accessoires suit la taille de l'avatar (une ampoule de 54 px
  // à côté d'une vignette de 36 px serait absurde).
  const badgeSize = Math.max(18, Math.round(height * 0.18))

  return (
    <div
      ref={boite}
      className={`helios-avatar relative shrink-0 ${className}`}
      style={{ width, height, animation: bodyAnim }}
      role="img"
      aria-label={def.label}
    >
      <div className="w-full h-full" style={{ animation: idleAnim, transformOrigin: '50% 92%' }}>
        <img src={pose.src} alt="" className="w-full h-full object-contain block" />
        <svg
          viewBox={`0 0 100 ${vbH}`}
          className="absolute inset-0 w-full h-full pointer-events-none"
          aria-hidden="true"
        >
          {/* Deux groupes imbriqués, et non un seul : le clignement anime `transform`
              (scaleY), le regard le pose à la main. Ensemble ils s'écraseraient. */}
          <g ref={yeux} className="helios-regard">
            <g style={{ animation: blink, transformOrigin: `${cx}px ${eyeCy}px` }}>
              <ellipse cx={cx - gap / 2} cy={eyeCy} rx={eyeRx} ry={eyeRy} fill={INK} />
              <ellipse cx={cx + gap / 2} cy={eyeCy} rx={eyeRx} ry={eyeRy} fill={INK} />
            </g>
          </g>
          {/* Épaisseur exprimée en unités du repère (≈ 2,9 % de la largeur, soit
              le trait du dessin lui-même) : la bouche grossit avec l'avatar au
              lieu de rester à une épaisseur fixe en pixels. */}
          <path d={mouth} fill="none" stroke={INK} strokeWidth={faceW * 0.061} strokeLinecap="round" />
        </svg>
      </div>

      {badge && <Badge kind={badge} size={badgeSize} />}
    </div>
  )
}

/** Accessoires posés à côté du casque : ampoule (il a trouvé), « ? » (il ne sait
 *  pas), « ! » (problème), points (il réfléchit). Dessinés en CSS/texte pour
 *  rester nets à toute taille et ne coûter aucun asset. */
function Badge({ kind, size }: { kind: NonNullable<StateDef['badge']>; size: number }) {
  const pop = 'hPop .45s cubic-bezier(.2,1.3,.4,1) both'
  const common = { position: 'absolute', top: '-6%', right: '-26%' } as const

  if (kind === 'dots') {
    return (
      <div style={{ ...common, top: '4%', display: 'flex', gap: size * 0.12, alignItems: 'center' }}>
        {[0, 0.18, 0.36].map((d) => (
          <span
            key={d}
            style={{
              width: size * 0.15,
              height: size * 0.15,
              borderRadius: '50%',
              background: INK,
              animation: `hDots 1.1s ease-in-out ${d}s infinite`,
            }}
          />
        ))}
      </div>
    )
  }

  if (kind === 'question' || kind === 'bang') {
    return (
      <div
        style={{
          ...common,
          fontFamily: 'Fraunces, Georgia, serif',
          fontSize: size,
          fontWeight: 600,
          color: INK,
          lineHeight: 1,
          animation: pop,
        }}
      >
        {kind === 'question' ? '?' : '!'}
      </div>
    )
  }

  // Ampoule : verre + culot fixes, rayons qui pulsent.
  const u = size / 54 // les cotes ci-dessous sont dessinées pour une ampoule de 54 px
  return (
    <div style={{ ...common, width: size, height: size, animation: pop }}>
      <div style={{ position: 'absolute', left: 15 * u, top: 12 * u, width: 24 * u, height: 24 * u, borderRadius: '50% 50% 46% 46%', border: `${2.5 * u}px solid ${INK}`, background: '#fff', boxSizing: 'border-box' }} />
      <div style={{ position: 'absolute', left: 21 * u, top: 34 * u, width: 12 * u, height: 2.5 * u, borderRadius: 2, background: INK }} />
      <div style={{ position: 'absolute', left: 22 * u, top: 39 * u, width: 10 * u, height: 2.5 * u, borderRadius: 2, background: INK }} />
      <div style={{ width: '100%', height: '100%', animation: 'hGlow 1.6s ease-in-out infinite' }}>
        <div style={{ position: 'absolute', left: 26 * u, top: 0, width: 2.5 * u, height: 8 * u, borderRadius: 2, background: INK }} />
        <div style={{ position: 'absolute', left: 3 * u, top: 8 * u, width: 9 * u, height: 2.5 * u, borderRadius: 2, background: INK, transform: 'rotate(38deg)' }} />
        <div style={{ position: 'absolute', right: 3 * u, top: 8 * u, width: 9 * u, height: 2.5 * u, borderRadius: 2, background: INK, transform: 'rotate(-38deg)' }} />
        <div style={{ position: 'absolute', left: 0, top: 24 * u, width: 9 * u, height: 2.5 * u, borderRadius: 2, background: INK }} />
        <div style={{ position: 'absolute', right: 0, top: 24 * u, width: 9 * u, height: 2.5 * u, borderRadius: 2, background: INK }} />
      </div>
    </div>
  )
}
