/**
 * Graphiques du simulateur — SVG écrit à la main, aucune librairie.
 *
 * Tous respectent la même règle : jamais de graphique vide. Quand il n'y a rien à
 * montrer, c'est une phrase qui prend la place, pas un cadre avec des axes et du blanc.
 */

import { MOIS_COURTS } from '../../lib/simulateur'

export function Vide({ message }: { message: string }) {
  return (
    <p className="rounded-lg border border-dashed border-ink/20 bg-cream px-4 py-8 text-center text-dark/70">
      {message}
    </p>
  )
}

export function Anneau({
  pct, partVirtuelle = 0, classe = 'h-28 w-28',
}: { pct: number; partVirtuelle?: number; classe?: string }) {
  const rayon = 52
  const circonference = 2 * Math.PI * rayon
  const borne = Math.max(0, Math.min(100, pct))
  const borneVirtuelle = Math.max(0, Math.min(borne, partVirtuelle))
  return (
    <svg viewBox="0 0 140 140" className={classe} role="img"
      aria-label={`Autonomie : ${borne} %`}>
      <circle cx="70" cy="70" r={rayon} fill="none" stroke="#E5E0DA" strokeWidth="14" />
      <circle cx="70" cy="70" r={rayon} fill="none" stroke="#B85A08" strokeWidth="14"
        strokeLinecap="round" transform="rotate(-90 70 70)"
        strokeDasharray={`${(borne / 100) * circonference} ${circonference}`} />
      {borneVirtuelle > 0 && (
        <circle cx="70" cy="70" r={rayon} fill="none" stroke="#2E86C1" strokeWidth="14"
          strokeLinecap="round" transform="rotate(-90 70 70)"
          strokeDasharray={`${(borneVirtuelle / 100) * circonference} ${circonference}`} />
      )}
      <text x="70" y="66" textAnchor="middle" fontSize="28" fontWeight="700" fill="#1D3F63">
        {Math.round(borne)}%
      </text>
      <text x="70" y="88" textAnchor="middle" fontSize="12" fill="#1F2937">autonomie</text>
    </svg>
  )
}

interface SerieBarres {
  nom: string
  couleur: string
  valeurs: number[]
}

export function BarresMensuelles({ series, unite = 'kWh' }: { series: SerieBarres[]; unite?: string }) {
  const max = Math.max(1, ...series.flatMap((s) => s.valeurs))
  const largeurGroupe = 100 / 12
  const largeurBarre = largeurGroupe / (series.length + 0.6)

  return (
    <figure>
      <svg viewBox="0 0 100 46" className="w-full" preserveAspectRatio="none"
        role="img" aria-label={`Répartition mois par mois, en ${unite}`}>
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1="0" x2="100" y1={40 - f * 36} y2={40 - f * 36}
            stroke="#E5E0DA" strokeWidth="0.3" vectorEffect="non-scaling-stroke" />
        ))}
        {series.map((serie, is) =>
          serie.valeurs.map((valeur, im) => {
            const hauteur = (Math.max(valeur, 0) / max) * 36
            const x = im * largeurGroupe + 0.3 + is * largeurBarre
            return (
              <rect key={`${serie.nom}-${im}`} x={x} y={40 - hauteur}
                width={largeurBarre * 0.88} height={hauteur} fill={serie.couleur} rx="0.4">
                <title>{`${MOIS_COURTS[im]} — ${serie.nom} : ${Math.round(valeur)} ${unite}`}</title>
              </rect>
            )
          }),
        )}
      </svg>
      <div className="mt-1 flex justify-between px-1 text-xs text-dark/60" aria-hidden="true">
        {MOIS_COURTS.map((m, i) => <span key={i}>{m}</span>)}
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-4 text-sm">
        {series.map((s) => (
          <span key={s.nom} className="inline-flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-sm" style={{ background: s.couleur }} />
            {s.nom}
          </span>
        ))}
      </figcaption>
    </figure>
  )
}

interface SerieCourbe {
  nom: string
  couleur: string
  valeurs: number[]
}

export function CourbeJournee({
  series, heureActive,
}: { series: SerieCourbe[]; heureActive?: number }) {
  const max = Math.max(0.1, ...series.flatMap((s) => s.valeurs))
  const points = (valeurs: number[]) =>
    valeurs.map((v, i) => `${(i / 23) * 100},${40 - (Math.max(v, 0) / max) * 36}`).join(' ')

  return (
    <figure>
      <svg viewBox="0 0 100 46" className="w-full" preserveAspectRatio="none"
        role="img" aria-label="Journée moyenne, heure par heure">
        {[0.5, 1].map((f) => (
          <line key={f} x1="0" x2="100" y1={40 - f * 36} y2={40 - f * 36}
            stroke="#E5E0DA" strokeWidth="0.3" vectorEffect="non-scaling-stroke" />
        ))}
        {heureActive !== undefined && (
          <line x1={(heureActive / 23) * 100} x2={(heureActive / 23) * 100} y1="2" y2="40"
            stroke="#1D3F63" strokeWidth="0.6" strokeDasharray="1.5 1.5"
            vectorEffect="non-scaling-stroke" />
        )}
        {series.map((s) => (
          <polyline key={s.nom} points={points(s.valeurs)} fill="none" stroke={s.couleur}
            strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round"
            vectorEffect="non-scaling-stroke" />
        ))}
      </svg>
      <div className="mt-1 flex justify-between px-1 text-xs text-dark/60" aria-hidden="true">
        {[0, 6, 12, 18, 23].map((h) => <span key={h}>{h} h</span>)}
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-4 text-sm">
        {series.map((s) => (
          <span key={s.nom} className="inline-flex items-center gap-2">
            <span className="inline-block h-1 w-5 rounded" style={{ background: s.couleur }} />
            {s.nom}
          </span>
        ))}
      </figcaption>
    </figure>
  )
}

/** Trésorerie cumulée : la ligne passe du rouge au vert au moment où le projet est remboursé. */
export function Courbe25Ans({ tresorerie }: { tresorerie: { annee: number; cumul_eur: number }[] }) {
  if (!tresorerie.length) return <Vide message="Ajoutez des panneaux pour voir la projection." />

  const valeurs = tresorerie.map((t) => t.cumul_eur)
  const min = Math.min(0, ...valeurs)
  const max = Math.max(0, ...valeurs)
  const etendue = max - min || 1
  const y = (v: number) => 42 - ((v - min) / etendue) * 38
  const x = (i: number) => (i / Math.max(tresorerie.length - 1, 1)) * 100
  const points = valeurs.map((v, i) => `${x(i)},${y(v)}`).join(' ')

  return (
    <figure>
      <svg viewBox="0 0 100 48" className="w-full" preserveAspectRatio="none"
        role="img" aria-label="Trésorerie cumulée sur 25 ans">
        <line x1="0" x2="100" y1={y(0)} y2={y(0)} stroke="#1D3F63" strokeWidth="0.5"
          vectorEffect="non-scaling-stroke" />
        <polyline points={`0,${y(min)} ${points} 100,${y(min)}`} fill="#B85A08" fillOpacity="0.10"
          stroke="none" />
        <polyline points={points} fill="none" stroke="#B85A08" strokeWidth="1.8"
          strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="mt-1 flex justify-between px-1 text-xs text-dark/60" aria-hidden="true">
        <span>aujourd’hui</span><span>10 ans</span><span>25 ans</span>
      </div>
    </figure>
  )
}

/** Répartition en barre unique — « le soleil part vers… », « la maison est alimentée par… ». */
export function Repartition({ parts }: { parts: { nom: string; valeur: number; couleur: string }[] }) {
  const total = parts.reduce((s, p) => s + Math.max(p.valeur, 0), 0)
  if (total <= 0.001) return null
  let curseur = 0
  return (
    <div>
      <svg viewBox="0 0 100 8" className="w-full" preserveAspectRatio="none" role="presentation">
        {parts.map((p) => {
          const largeur = (Math.max(p.valeur, 0) / total) * 100
          const x = curseur
          curseur += largeur
          return largeur > 0
            ? <rect key={p.nom} x={x} y="0" width={largeur} height="8" fill={p.couleur} />
            : null
        })}
      </svg>
      <ul className="mt-2 space-y-1 text-sm">
        {parts.filter((p) => p.valeur > 0.001).map((p) => (
          <li key={p.nom} className="flex items-center justify-between gap-3">
            <span className="inline-flex items-center gap-2">
              <span className="inline-block h-3 w-3 rounded-sm" style={{ background: p.couleur }} />
              {p.nom}
            </span>
            <span className="font-semibold text-ink">{p.valeur.toFixed(2)} kW</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
