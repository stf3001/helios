/**
 * La scène : la maison Helios, ses emplacements d'équipement, et l'énergie qui circule.
 *
 * DÉCOR = `/maison-demain-v2.webp`, l'illustration 21:9 fournie le 01/10/2026. Elle
 * REMPLACE, pour la scène seulement, l'ancienne `/maison-demain.webp` — qui reste en place
 * sur `/helios`, où ses légendes gravées sont justement le propos de la page.
 *
 * CE QUE LA NOUVELLE IMAGE A FAIT DISPARAÎTRE, et qu'il ne faut pas réintroduire : le
 * recadrage (`CADRE`) et les quatre voiles en dégradé qui masquaient les légendes gravées
 * tombant dans le champ. La nouvelle illustration ne porte AUCUN texte et est déjà cadrée
 * sur la maison et son terrain : le viewBox montre l'image entière, et rien n'a plus besoin
 * d'être caché. Le fond de l'image (#F5F1E8) est la couleur crème du site, elle se fond
 * dans la page sans bordure ni habillage.
 *
 * Conséquence inchangée : les équipements sont TOUJOURS visibles dans le décor, installés
 * ou non. C'est l'état des repères et des flux qui dit la configuration du foyer.
 *
 * Toutes les coordonnées sont dans `reperes.ts`, EN PIXELS DE L'IMAGE SOURCE (1584 × 672).
 */

import { useEffect, useMemo, useRef, useState } from 'react'

import type { Saison } from '../../lib/simulateur'
import { COULEURS } from '../../data/couleurs'
import { ANCRE, FENETRES, IMAGE, POSITIONS, RAYON_REPERE, ROTORS } from './reperes'

const DECOR = '/maison-demain-v2.webp'

export interface EmplacementScene {
  id: string
  label: string
  /** Le libellé de la vignette, quand le libellé entier est trop long. Voir `EQUIPEMENTS`. */
  court?: string
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
      <path d={d} fill="none" stroke={COULEURS.blanc} strokeWidth={largeur + 6} strokeOpacity={0.55}
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
  // Un emplacement sans position n'a pas de repère sur l'image, et c'est voulu pour le
  // raccordement au réseau : sa vignette ouvre les réglages, rien n'est posé sur le décor.
  if (!pos) return null
  const installe = emplacement.installe
  const r = RAYON_REPERE
  return (
    <g
      role="button"
      tabIndex={0}
      aria-pressed={installe}
      aria-label={`${emplacement.label} — ${installe ? emplacement.resume ?? 'installé' : 'non installé, ajouter'}`}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } }}
      style={{ cursor: 'pointer' }}
    >
      {/* Halo : ce qui est installé s'allume sur le décor. */}
      {installe && <circle cx={pos.x} cy={pos.y} r={r + 14} fill={COULEURS.accent} opacity={0.16} />}
      <circle cx={pos.x} cy={pos.y + 3} r={r} fill={COULEURS.ink} opacity={0.2} />
      <circle cx={pos.x} cy={pos.y} r={r}
        fill={installe ? COULEURS.accent : COULEURS.sable}
        stroke={installe ? COULEURS.sable : COULEURS.accent}
        strokeWidth={3}
        strokeDasharray={installe ? undefined : '7 5'} />
      <text x={pos.x} y={pos.y + 12} textAnchor="middle" fontSize={34} fontWeight={700}
        fill={installe ? COULEURS.blanc : COULEURS.accent} style={{ pointerEvents: 'none' }}>
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

  /* --- Mode calibrage (`?calibrage=1`) ---
     Un clic sur la scène donne les coordonnées du point DANS LE REPÈRE DE L'IMAGE, par la
     matrice du SVG — et non en pourcentage de `clientX`, qui dépendrait de la taille
     affichée et ne se recopierait pas dans `reperes.ts`. Un calque transparent capte les
     clics pendant le calibrage : on relève des positions, on ne règle pas des équipements. */
  const calibrage = useMemo(
    () => new URLSearchParams(window.location.search).get('calibrage') === '1', [])
  const svg = useRef<SVGSVGElement>(null)
  const [releve, setReleve] = useState<{ x: number; y: number } | null>(null)

  const relever = (e: React.MouseEvent<SVGRectElement>) => {
    const element = svg.current
    if (!element) return
    const matrice = element.getScreenCTM()
    if (!matrice) return
    const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(matrice.inverse())
    const releveArrondi = { x: Math.round(point.x), y: Math.round(point.y) }
    setReleve(releveArrondi)
    navigator.clipboard
      ?.writeText(`{ x: ${releveArrondi.x}, y: ${releveArrondi.y} }`)
      .catch(() => { /* presse-papiers refusé : les chiffres restent lisibles à l'écran */ })
  }

  return (
    <div>
      <div className="relative">
        <svg
          ref={svg}
          viewBox={`0 0 ${IMAGE.w} ${IMAGE.h}`}
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-auto rounded-xl"
          role="img"
          aria-label={`Votre maison à ${String(heure).padStart(2, '0')} h, en ${saison}`}
        >
          <defs>
            <radialGradient id="sc-halo-soleil" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={COULEURS.or} stopOpacity="0.55" />
              <stop offset="100%" stopColor={COULEURS.or} stopOpacity="0" />
            </radialGradient>
            <linearGradient id="sc-nuit" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COULEURS.nuit} stopOpacity="0.72" />
              <stop offset="100%" stopColor={COULEURS.ink} stopOpacity="0.5" />
            </linearGradient>
            <filter id="sc-lueur" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="26" />
            </filter>
          </defs>

          {/* LE DÉCOR : l'illustration entière, le viewBox lui est calé dessus. */}
          <image href={DECOR} x="0" y="0" width={IMAGE.w} height={IMAGE.h} />

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
              <image href={DECOR} x="0" y="0" width={IMAGE.w} height={IMAGE.h}
                clipPath={`url(#sc-rotor-${i})`} />
            </g>
          ))}

          {/* La nuit : un voile bleu par-dessus, et les fenêtres qui s'allument. */}
          {nuit && (
            <>
              <rect x="0" y="0" width={IMAGE.w} height={IMAGE.h} fill="url(#sc-nuit)" />
              <g filter="url(#sc-lueur)" opacity="0.85">
                {FENETRES.map((f, i) => (
                  <ellipse key={i} cx={f.cx} cy={f.cy} rx={f.rx} ry={f.ry} fill={COULEURS.or} />
                ))}
              </g>
            </>
          )}

          {/* Le soleil : son halo se renforce quand la production est forte. */}
          {!nuit && (
            <circle cx={soleil.x} cy={soleil.y}
              r={120 + Math.min(80, flux.soleilMaison * 14 + flux.soleilReseau * 10)}
              fill="url(#sc-halo-soleil)" />
          )}

          {/* ---------- LES FLUX ----------
              Le réseau est à GAUCHE depuis la nouvelle illustration : les deux flux qui le
              concernent longent le bord gauche, par-dessus la pelouse, et non plus la droite. */}
          <Flux d={`M ${soleil.x + 40} ${soleil.y + 60} Q ${maison.x - 220} ${maison.y - 230} ${maison.x - 30} ${maison.y - 20}`}
            kw={flux.soleilMaison} couleur={COULEURS.or} />
          <Flux d={`M ${soleil.x - 10} ${soleil.y + 70} Q ${batterie.x + 30} ${batterie.y - 220} ${batterie.x + 10} ${batterie.y - 50}`}
            kw={flux.soleilBatterie} couleur={COULEURS.vert} />
          <Flux d={`M ${soleil.x - 60} ${soleil.y + 30} Q ${reseau.x + 110} ${reseau.y - 110} ${reseau.x + 20} ${reseau.y - 10}`}
            kw={flux.soleilReseau} couleur={COULEURS.bleu} />
          <Flux d={`M ${reseau.x + 30} ${reseau.y + 40} Q ${maison.x - 420} ${maison.y + 240} ${maison.x - 110} ${maison.y + 60}`}
            kw={flux.reseauMaison} couleur={COULEURS.bleu} />
          <Flux d={`M ${batterie.x + 40} ${batterie.y - 20} Q ${maison.x - 230} ${maison.y + 130} ${maison.x - 60} ${maison.y + 50}`}
            kw={flux.batterieMaison} couleur={COULEURS.vert} />

          {/* ---------- LES REPÈRES ---------- */}
          {equipements.map((e) => (
            <Repere key={e.id} numero={numeroDe.get(e.id) ?? 0} emplacement={e}
              onClick={() => onEmplacement(e.id)} />
          ))}

          {/* Pendant le calibrage, ce calque passe devant tout et capte les clics. */}
          {calibrage && (
            <>
              <rect x="0" y="0" width={IMAGE.w} height={IMAGE.h} fill="transparent"
                onClick={relever} style={{ cursor: 'crosshair' }} />
              {releve && (
                <circle cx={releve.x} cy={releve.y} r={10} fill="none"
                  stroke={COULEURS.accent} strokeWidth={4} />
              )}
            </>
          )}
        </svg>

        {calibrage && (
          <p className="absolute left-2 top-2 rounded-lg bg-ink/85 px-3 py-1.5 font-mono text-sm
            text-sable">
            {releve
              ? `{ x: ${releve.x}, y: ${releve.y} } — copié`
              : 'Calibrage : cliquez pour relever un point'}
          </p>
        )}
      </div>

      {/* Les mots vivent ici, le dessin ne porte que des numéros — rien ne peut se chevaucher.
          Pastilles SANS fond ni cadre : seuls le rond et le mot sont visibles, et ils entourent
          la scène au lieu de la concurrencer.

          DEUX RANGÉES AU PLUS SUR UN ÉCRAN D'ORDINATEUR, et c'est une contrainte dure : à la
          troisième, la quinzième vignette passe sous le pli et on ne la voit pas sans faire
          défiler la page — autant dire qu'elle n'existe pas. C'est ce qui commande les
          libellés courts (`EQUIPEMENTS.court`), la police à 12 px et l'espacement serré. */}
      <ul className="mt-2 flex flex-wrap justify-center gap-x-0.5 gap-y-0">
        {equipements.map((e) => {
          const numero = numeroDe.get(e.id)
          return (
            <li key={e.id}>
              <button type="button" onClick={() => onEmplacement(e.id)}
                aria-pressed={e.installe}
                /* L'étiquette porte le libellé ENTIER, pas l'abrégé : un lecteur d'écran n'a
                   pas la scène sous les yeux pour deviner ce qu'« Inertie » désigne. */
                aria-label={`${e.label} — ${e.installe ? e.resume ?? 'installé' : 'non installé, ajouter'}`}
                title={e.court ? e.label : undefined}
                className="flex items-center gap-1 rounded-full px-0.5 py-0.5 text-left transition
                  hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-primary/50">
                <span className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full
                  text-[10px] font-bold
                  ${e.installe
                    ? 'bg-primary text-white'
                    : 'border border-dashed border-primary text-primary'}`}>
                  {e.installe ? numero : '+'}
                </span>
                <span className={`whitespace-nowrap text-xs leading-tight
                  ${e.installe ? 'font-semibold text-ink' : 'text-dark/70'}`}>
                  {e.court ?? e.label}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
