/**
 * Le jardin nourricier — le panneau qui s'ouvre quand on clique sur le potager.
 *
 * LE CALCUL EST RETOURNÉ, ET TOUT L'ÉCRAN EN DÉCOULE. On ne demande pas « combien de
 * personnes ? » pour répondre « il vous faut 480 m² et 3 h par jour » : ce chiffre est
 * vrai, mais il fait refermer la page. On demande aussi **combien de temps vous acceptez
 * d'y passer**, et on répond ce que ce temps achète — une surface, des kilos, et la part
 * de vos légumes que ça couvre.
 *
 * Ce que coûterait la totalité est affiché quand même, en dessous et en petit. Ce n'est
 * pas un chiffre qu'on cache : c'est un chiffre qu'on ne met pas en titre.
 *
 * AUCUN chiffre n'est écrit ici : tout vient de `/api/jardin/calcul`.
 */

import { Link } from 'react-router-dom'
import { ArrowRight, Sprout } from 'lucide-react'

import { Choix } from './Reglage'
import type { JardinConfig, JardinResultat } from '../../lib/jardin'

interface Props {
  config: JardinConfig
  resultat: JardinResultat | null
  majConfig: (maj: (c: JardinConfig) => JardinConfig) => void
  erreur: string | null
}

/** « 1 h 48 » plutôt que « 1,8 h » : personne ne compte son jardinage en décimales. */
export function heures(valeur: number): string {
  const total = Math.round(valeur * 60)
  const h = Math.floor(total / 60)
  const m = total % 60
  if (h === 0) return `${m} min`
  return m === 0 ? `${h} h` : `${h} h ${String(m).padStart(2, '0')}`
}

function Curseur({
  label, valeur, min, max, pas, format, onChange,
}: {
  label: string; valeur: number; min: number; max: number; pas: number
  format: (v: number) => string; onChange: (v: number) => void
}) {
  const id = `curseur-${label.replace(/\s+/g, '-').toLowerCase()}`
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="font-semibold text-ink">{label}</label>
        <span className="font-bold text-primary" aria-live="polite">{format(valeur)}</span>
      </div>
      <input id={id} type="range" min={min} max={max} step={pas} value={valeur}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-1.5 w-full accent-primary" />
    </div>
  )
}

export default function ReglageJardin({ config, resultat, majConfig, erreur }: Props) {
  return (
    <>
      {/* « Personnes du foyer », et non « personnes à nourrir » : un potager donne des
          légumes, il ne nourrit pas. 127 kg de légumes par an, ce n'est qu'une part de
          l'alimentation — le mot « nourrir » promettrait ce qu'aucun jardin ne tient. */}
      <Curseur label="Personnes du foyer" valeur={config.personnes}
        min={1} max={10} pas={1} format={(v) => `${v}`}
        onChange={(v) => majConfig((c) => ({ ...c, personnes: v }))} />

      <Curseur label="Temps que j’y passe" valeur={config.heures_jour}
        min={0.25} max={3} pas={0.25} format={(v) => `${heures(v)} / jour`}
        onChange={(v) => majConfig((c) => ({ ...c, heures_jour: v }))} />

      <Choix label="Mon jardinage" valeur={config.conduite}
        options={[
          { value: 'debutant', label: 'Je débute' },
          { value: 'rodee', label: 'J’ai la main' },
        ]}
        aide={config.conduite === 'debutant'
          ? 'Premier potager, on apprend en faisant.'
          : 'Paillage, arrosage automatique, successions de cultures.'}
        onChange={(v) => majConfig((c) => ({ ...c, conduite: v }))} />

      {erreur && <p className="text-sm text-terra">{erreur}</p>}

      {resultat && (
        <div className="space-y-3 border-t border-ink/10 pt-3">
          {/* LE TITRE, c'est la couverture : ce que ce temps-là vous donne vraiment. */}
          <div className="rounded-xl bg-leaf/10 p-3 text-center">
            <div className="font-display text-3xl font-bold text-leaf">
              {resultat.couverture_pct} %
            </div>
            <div className="text-sm text-dark/75">
              de vos légumes, pour {heures(resultat.budget_heures_jour)} par jour
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg border border-ink/10 p-2">
              <div className="font-display text-xl font-bold text-ink">
                {resultat.surface_totale_m2} m²
              </div>
              <div className="text-xs text-dark/60">de terrain</div>
            </div>
            <div className="rounded-lg border border-ink/10 p-2">
              <div className="font-display text-xl font-bold text-ink">
                {resultat.recolte_kg_an} kg
              </div>
              <div className="text-xs text-dark/60">récoltés par an</div>
            </div>
          </div>

          <p className="text-sm text-dark/75">
            Un foyer de {resultat.personnes} {resultat.personnes > 1 ? 'personnes mange' : 'personne mange'}{' '}
            <strong>{resultat.besoin_kg_an} kg</strong> de légumes par an, pommes de terre
            comprises.
          </p>

          {/* LA SAISON. Une moyenne annuelle lissée ferait abandonner en juin — qui est
              exactement le moment où les débutants lâchent. On le dit avant. */}
          <p className="rounded-lg bg-cream p-2.5 text-sm text-dark/80">
            Ce n’est pas régulier : <strong>mars à juin, c’est la moitié du travail</strong>.
            En {resultat.pointe.mois}, comptez plutôt {heures(resultat.pointe.heures_jour)} par
            jour ; en hiver, presque rien.
          </p>

          {!resultat.autonomie.atteinte && (
            <p className="text-sm text-dark/60">
              Pour la totalité de vos légumes, il faudrait{' '}
              <strong>{resultat.autonomie.surface_totale_m2} m²</strong> et{' '}
              <strong>{heures(resultat.autonomie.heures_jour)} par jour</strong> en moyenne.
            </p>
          )}

          <div className="space-y-1.5 border-t border-ink/10 pt-3">
            <Link to="/la-terre"
              className="flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
              <Sprout size={16} /> Comment s’y prendre : extérieur, intérieur, hydroponie
            </Link>
            <Link to="/espace/jardin"
              className="flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
              <ArrowRight size={16} /> Mon programme de cultures, mois par mois
              {resultat.zone && ` (zone ${resultat.zone})`}
            </Link>
          </div>

          <p className="text-xs text-dark/50">{resultat.avertissement}</p>
        </div>
      )}
    </>
  )
}
