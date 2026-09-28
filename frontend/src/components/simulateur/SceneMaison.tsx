/**
 * La scène : la maison Helios, ses emplacements d'équipement, et l'énergie qui circule.
 *
 * DÉCOR = L'ILLUSTRATION DU SITE (`/maison-demain.webp`), celle de `/comment-ca-marche`.
 * Choix du 28/09/2026, après deux tentatives de maison dessinée à la main en SVG (22/07 puis
 * 28/09) jugées insuffisantes : l'architecture au trait, les vitrages, le mobilier vu par
 * transparence et les lointains ne se redessinent pas à la main. On prend donc l'image telle
 * qu'elle est, équipements compris, et on ne code que ce qui doit RÉAGIR.
 *
 * Conséquence assumée : les équipements sont TOUJOURS visibles dans le décor, installés ou non.
 * C'est l'état des repères et des flux qui dit la configuration du foyer, pas le décor. Une
 * version en calques (un fichier par équipement, fond transparent) reste possible plus tard —
 * le cahier des charges est dans `assets-scene/A-LIRE.txt` — et ne changerait que le décor.
 *
 * CADRAGE : l'illustration porte ses propres légendes gravées, plus un bandeau de bénéfices en
 * bas. Elles feraient doublon avec l'interface et la surchargeraient. Le `viewBox` ne montre
 * donc que la maison et son terrain. Toutes les coordonnées ci-dessous sont EN PIXELS DE
 * L'IMAGE SOURCE (1536 × 1024) : c'est ce qui permet de régler un repère en le lisant sur
 * l'image d'origine.
 */

import type { Saison } from '../../lib/simulateur'

export interface EmplacementScene {
  id: string
  label: string
  installe: boolean
  resume: string | null
}

export interface FluxScene {
  soleilMaison: number
  soleilBatterie: number
  soleilReseau: number
  reseauMaison: number
  batterieMaison: number
}

interface Props {
  equipements: EmplacementScene[]
  /** Une éolienne est posée : les rotors se mettent à tourner. */
  eolienne: boolean
  heure: number
  saison: Saison
  flux: FluxScene
  onEmplacement: (id: string) => void
}

const IMAGE = { w: 1536, h: 1024 }
/**
 * Fenêtre montrée : la maison et son terrain. Les bornes sont choisies pour écarter le titre
 * gravé (au-dessus de y = 110), la colonne de légendes de droite (au-delà de x = 1246) et le
 * bandeau de bénéfices du bas (sous y = 775), tout en gardant la voiture, qui commence à
 * x = 140 et qui est l'un des équipements.
 */
const CADRE = { x: 118, y: 112, w: 1105, h: 638 }

/**
 * Certaines légendes gravées tombent DANS le cadre et ne peuvent pas en être exclues sans
 * perdre un objet utile : celles de gauche encadrent la voiture, qui est un équipement. Des
 * dégradés crème les voilent donc bande par bande — ce qui fait en prime une amorce douce.
 * Le trou entre les deux bandes de gauche, c'est la voiture : elle, on la garde.
 */
const VOILES = [
  // Colonne de gauche : « toit végétalisé », « panneaux solaires », « stockage d'énergie ».
  { x: 112, y: 116, w: 206, h: 416, sens: 'droite' as const },
  // Sous la voiture : « mobilité électrique ».
  { x: 112, y: 668, w: 216, h: 92, sens: 'droite' as const },
  // Amorces de légendes et traits de rappel du bord droit.
  { x: 1150, y: 116, w: 78, h: 360, sens: 'gauche' as const },
]

/**
 * Position de chaque repère, en pixels de l'image source.
 *
 * Quatre d'entre eux ne correspondent à AUCUN objet dessiné (l'illustration ne montre ni
 * carport, ni climatisation, ni ballon, ni poteau de raccordement) : ils sont posés à
 * l'endroit le plus plausible et marqués ci-dessous. À revoir si un décor dédié est produit.
 */
const POSITIONS: Record<string, { x: number; y: number }> = {
  panneaux: { x: 596, y: 296 },          // la nappe bleue sur le toit
  batterie: { x: 424, y: 566 },          // l'armoire verte du garage
  inertie: { x: 700, y: 726 },           // approximatif : sous le terrain, elle est enterree
  voiture: { x: 214, y: 592 },           // la voiture et sa borne
  piscine: { x: 516, y: 700 },           // le bassin
  batterie_virtuelle: { x: 318, y: 154 }, // dans le ciel : elle n'a pas d'objet, c'est le propos
  reseau: { x: 1068, y: 286 },           // approximatif : pas de poteau dessiné
  carport: { x: 286, y: 500 },           // approximatif : l'auvent du garage en tient lieu
  eolienne: { x: 1108, y: 176 },         // approximatif : dans le ciel, a droite du toit
  ballon: { x: 664, y: 474 },            // approximatif : posé sur le circuit orange (chaleur)
  clim: { x: 968, y: 574 },              // approximatif : côté technique de la maison
}

/**
 * Les trois rotors des éoliennes verticales, relevés sur l'image source.
 *
 * Elles TOURNENT quand une éolienne est posée, et restent immobiles sinon — c'est ce qui
 * donne l'information : la scène montre l'état du foyer, elle ne décore pas.
 *
 * COMMENT : on redécoupe le rotor dans l'image elle-même et on l'écrase horizontalement,
 * en rythme. Une pale hélicoïdale vue de côté fait exactement cela en tournant — elle
 * s'affine quand elle passe de profil, s'élargit quand elle revient de face. Pas de
 * redessin, donc pas de dédoublement avec le trait d'origine ; pas de cache blanc non
 * plus, qui ferait un trou dans le mur strié derrière la première.
 */
const ROTORS = [
  { x0: 1056, x1: 1108, y0: 484, y1: 594 },
  { x0: 1131, x1: 1178, y0: 484, y1: 590 },
  { x0: 1189, x1: 1238, y0: 486, y1: 590 },
]

/** Où arrivent et d'où partent les flux, en pixels de l'image source. */
const ANCRE = {
  soleil: { x: 536, y: 148 },
  maison: { x: 860, y: 452 },
  batterie: { x: 424, y: 566 },
  reseau: { x: 1068, y: 286 },
}

function estNuit(heure: number, saison: Saison): boolean {
  const [lever, coucher] = saison === 'ete' ? [6, 21] : saison === 'hiver' ? [8, 17] : [7, 19]
  return heure < lever || heure >= coucher
}

/** Épaisseur du trait proportionnelle aux kW, bornée pour rester lisible. */
function epaisseur(kw: number): number {
  if (kw <= 0.01) return 0
  return Math.max(4, Math.min(22, 4 + kw * 3.4))
}

function Flux({ d, kw, couleur }: { d: string; kw: number; couleur: string }) {
  const largeur = epaisseur(kw)
  if (largeur === 0) return null
  // Plus il passe de kW, plus le flux va vite : la vitesse dit la puissance autant que l'épaisseur.
  const duree = Math.max(0.6, 2.4 - kw * 0.28)
  return (
    <g>
      {/* Un liseré blanc détache le flux du décor, qui est clair et chargé. */}
      <path d={d} fill="none" stroke="#FFFFFF" strokeWidth={largeur + 6} strokeOpacity={0.55}
        strokeLinecap="round" />
      <path d={d} fill="none" stroke={couleur} strokeWidth={largeur} strokeOpacity={0.28}
        strokeLinecap="round" />
      <path d={d} fill="none" stroke={couleur} strokeWidth={largeur} strokeLinecap="round"
        strokeDasharray="14 22" className="scene-flux"
        style={{ animationDuration: `${duree}s` }} />
    </g>
  )
}

function Repere({
  numero, emplacement, onClick,
}: { numero: number; emplacement: EmplacementScene; onClick: () => void }) {
  const pos = POSITIONS[emplacement.id]
  if (!pos) return null
  const installe = emplacement.installe
  const r = 30
  return (
    <g
      role="button"
      tabIndex={0}
      aria-label={`${emplacement.label} — ${installe ? emplacement.resume ?? 'installé' : 'non installé, ajouter'}`}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } }}
      style={{ cursor: 'pointer' }}
    >
      {/* Halo : ce qui est installé s'allume sur le décor. */}
      {installe && <circle cx={pos.x} cy={pos.y} r={r + 14} fill="#B85A08" opacity={0.16} />}
      <circle cx={pos.x} cy={pos.y + 3} r={r} fill="#1D3F63" opacity={0.2} />
      <circle cx={pos.x} cy={pos.y} r={r}
        fill={installe ? '#B85A08' : '#FDF8F3'}
        stroke={installe ? '#FDF8F3' : '#B85A08'}
        strokeWidth={3}
        strokeDasharray={installe ? undefined : '7 5'} />
      <text x={pos.x} y={pos.y + 11} textAnchor="middle" fontSize={30} fontWeight={700}
        fill={installe ? '#FFFFFF' : '#B85A08'} style={{ pointerEvents: 'none' }}>
        {installe ? numero : '+'}
      </text>
    </g>
  )
}

export default function SceneMaison({ equipements, eolienne, heure, saison, flux, onEmplacement }: Props) {
  const nuit = estNuit(heure, saison)
  const installes = equipements.filter((e) => e.installe)
  const numeroDe = new Map(installes.map((e, i) => [e.id, i + 1]))

  const { soleil, maison, batterie, reseau } = ANCRE

  return (
    <div>
      <svg
        viewBox={`${CADRE.x} ${CADRE.y} ${CADRE.w} ${CADRE.h}`}
        className="w-full h-auto rounded-xl"
        role="img"
        aria-label={`Votre maison à ${String(heure).padStart(2, '0')} h, en ${saison}`}
      >
        <defs>
          <radialGradient id="sc-halo-soleil" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#F5B700" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#F5B700" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="sc-nuit" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0E1C33" stopOpacity="0.72" />
            <stop offset="100%" stopColor="#1D3F63" stopOpacity="0.5" />
          </linearGradient>
          <filter id="sc-lueur" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="26" />
          </filter>
          <linearGradient id="sc-voile-droite" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#FDF8F3" stopOpacity="1" />
            <stop offset="86%" stopColor="#FDF8F3" stopOpacity="0.99" />
            <stop offset="100%" stopColor="#FDF8F3" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="sc-voile-gauche" x1="1" y1="0" x2="0" y2="0">
            <stop offset="0%" stopColor="#FDF8F3" stopOpacity="1" />
            <stop offset="86%" stopColor="#FDF8F3" stopOpacity="0.99" />
            <stop offset="100%" stopColor="#FDF8F3" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* LE DÉCOR : l'illustration du site, à sa taille naturelle. Le viewBox fait le cadrage. */}
        <image href="/maison-demain.webp" x="0" y="0" width={IMAGE.w} height={IMAGE.h} />

        {/* Les rotors qui tournent, redécoupés dans le décor et posés par-dessus. Chacun
            part avec un décalage : trois éoliennes parfaitement synchrones auraient l'air
            d'un mécanisme, pas de trois machines dans le vent. */}
        {eolienne && ROTORS.map((r, i) => (
          <g key={i} className="scene-eolienne"
            style={{
              transformOrigin: `${(r.x0 + r.x1) / 2}px ${(r.y0 + r.y1) / 2}px`,
              animationDelay: `${-i * 1.1}s`,
            }}>
            <clipPath id={`sc-rotor-${i}`}>
              <rect x={r.x0} y={r.y0} width={r.x1 - r.x0} height={r.y1 - r.y0} />
            </clipPath>
            <image href="/maison-demain.webp" x="0" y="0" width={IMAGE.w} height={IMAGE.h}
              clipPath={`url(#sc-rotor-${i})`} />
          </g>
        ))}

        {/* Voiles sur les légendes gravées qui tombent dans le cadre. */}
        {VOILES.map((v, i) => (
          <rect key={i} x={v.x} y={v.y} width={v.w} height={v.h}
            fill={`url(#sc-voile-${v.sens})`} />
        ))}

        {/* La nuit : un voile bleu par-dessus, et les fenêtres qui s'allument. */}
        {nuit && (
          <>
            <rect x="0" y="0" width={IMAGE.w} height={IMAGE.h} fill="url(#sc-nuit)" />
            <g filter="url(#sc-lueur)" opacity="0.85">
              <ellipse cx="830" cy="300" rx="120" ry="60" fill="#F5B700" />
              <ellipse cx="900" cy="500" rx="150" ry="70" fill="#F5B700" />
              <ellipse cx="640" cy="520" rx="90" ry="46" fill="#F5B700" />
            </g>
          </>
        )}

        {/* Le soleil : son halo se renforce quand la production est forte. */}
        {!nuit && (
          <circle cx={soleil.x} cy={soleil.y}
            r={120 + Math.min(80, flux.soleilMaison * 14 + flux.soleilReseau * 10)}
            fill="url(#sc-halo-soleil)" />
        )}

        {/* ---------- LES FLUX ---------- */}
        <Flux d={`M ${soleil.x + 40} ${soleil.y + 60} Q ${maison.x - 180} ${maison.y - 240} ${maison.x - 30} ${maison.y - 20}`}
          kw={flux.soleilMaison} couleur="#F5B700" />
        <Flux d={`M ${soleil.x - 10} ${soleil.y + 70} Q ${batterie.x + 20} ${batterie.y - 300} ${batterie.x + 10} ${batterie.y - 50}`}
          kw={flux.soleilBatterie} couleur="#57A64A" />
        <Flux d={`M ${soleil.x + 70} ${soleil.y - 10} Q ${reseau.x - 280} ${reseau.y - 130} ${reseau.x - 30} ${reseau.y - 10}`}
          kw={flux.soleilReseau} couleur="#2E86C1" />
        <Flux d={`M ${reseau.x - 20} ${reseau.y + 40} Q ${maison.x + 340} ${maison.y - 30} ${maison.x + 110} ${maison.y + 30}`}
          kw={flux.reseauMaison} couleur="#2E86C1" />
        <Flux d={`M ${batterie.x + 40} ${batterie.y - 20} Q ${maison.x - 250} ${maison.y + 150} ${maison.x - 60} ${maison.y + 60}`}
          kw={flux.batterieMaison} couleur="#57A64A" />

        {/* ---------- LES REPÈRES ---------- */}
        {equipements.map((e) => (
          <Repere key={e.id} numero={numeroDe.get(e.id) ?? 0} emplacement={e}
            onClick={() => onEmplacement(e.id)} />
        ))}
      </svg>

      {/* Les mots vivent ici, le dessin ne porte que des numéros — rien ne peut se chevaucher.
          Pastilles SANS fond ni cadre : seuls le rond et le mot sont visibles, et ils entourent
          la scène au lieu de la concurrencer. Le résumé d'un équipement installé (« 12 panneaux »)
          remplace le libellé plutôt que de s'ajouter dessous : deux fois moins de hauteur. */}
      <ul className="mt-3 flex flex-wrap justify-center gap-x-1 gap-y-0.5">
        {equipements.map((e) => {
          const numero = numeroDe.get(e.id)
          return (
            <li key={e.id}>
              <button type="button" onClick={() => onEmplacement(e.id)}
                aria-label={`${e.label} — ${e.installe ? e.resume ?? 'installé' : 'non installé, ajouter'}`}
                className="flex items-center gap-1.5 rounded-full px-2 py-1 text-left transition
                  hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-primary/50">
                <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold
                  ${e.installe
                    ? 'bg-primary text-white'
                    : 'border border-dashed border-primary text-primary'}`}>
                  {e.installe ? numero : '+'}
                </span>
                {/* Le libellé, et rien d'autre. Le résumé (« 18 panneaux · 9 kWc »,
                    « Ballon électrique ») s'affichait ici : il allongeait chaque pastille,
                    cassait l'alignement de la rangée et redisait ce que le panneau de
                    réglage montre déjà. Il reste dans l'étiquette d'accessibilité, où il
                    sert vraiment — un lecteur d'écran n'a pas la scène sous les yeux. */}
                <span className={`text-sm ${e.installe ? 'font-semibold text-ink' : 'text-dark/70'}`}>
                  {e.label}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
