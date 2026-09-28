/**
 * « Me laisser guider » — cinq questions, pas une de plus.
 *
 * À la fin, on arrive sur la maison SANS panneaux : c'est la prochaine étape qui propose
 * le premier geste. On ne pose rien sur le toit à la place de l'habitant.
 */

import { useState } from 'react'

import {
  chercherAdresses, CHAUFFAGES, ECS_OPTIONS, PRESENCES, type Config,
} from '../../lib/simulateur'
import { Bascule, Champ, Choix, Nombre } from './Reglage'

interface Props {
  config: Config
  majConfig: (maj: (c: Config) => Config) => void
  onTerminer: () => void
}

const TITRES = [
  'Où habitez-vous ?',
  'Votre logement',
  'Êtes-vous là en journée ?',
  'Chauffage et eau chaude',
  'Vos équipements',
]

export default function Guide5Questions({ config, majConfig, onTerminer }: Props) {
  const [etape, setEtape] = useState(0)
  const [texte, setTexte] = useState(config.adresse ?? '')
  const [suggestions, setSuggestions] = useState<Awaited<ReturnType<typeof chercherAdresses>>>([])
  const [recherche, setRecherche] = useState(false)

  const m = config.maison
  const majMaison = (maj: Partial<Config['maison']>) =>
    majConfig((c) => ({ ...c, maison: { ...c.maison, ...maj } }))

  const adresseChoisie = config.lat !== null && config.lon !== null
  const peutAvancer = etape !== 0 || adresseChoisie

  async function lancerRecherche() {
    setRecherche(true)
    try {
      setSuggestions(await chercherAdresses(texte))
    } finally {
      setRecherche(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4">
      <div role="dialog" aria-modal="true" aria-label={TITRES[etape]}
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-5 sm:rounded-2xl">
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm font-semibold text-primary">Question {etape + 1} sur 5</p>
          <button type="button" onClick={onTerminer}
            className="text-sm text-dark/60 underline hover:text-ink">
            Passer et tout régler moi-même
          </button>
        </div>
        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-cream" aria-hidden="true">
          <div className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${((etape + 1) / 5) * 100}%` }} />
        </div>

        <h2 className="mt-4 font-display text-2xl font-bold text-ink">{TITRES[etape]}</h2>

        <div className="mt-4 space-y-4">
          {etape === 0 && (
            <>
              <p className="text-dark/80">
                Elle sert uniquement à récupérer l’ensoleillement réel de votre commune. Elle
                n’est ni enregistrée, ni mise dans le lien de partage.
              </p>
              <div className="flex gap-2">
                <input type="text" value={texte} autoComplete="off"
                  placeholder="12 rue des Lilas, Marseille"
                  onChange={(e) => setTexte(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); lancerRecherche() } }}
                  aria-label="Votre adresse"
                  className="w-full rounded-lg border border-ink/20 px-3 py-2 text-ink
                    focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
                <button type="button" onClick={lancerRecherche} disabled={texte.trim().length < 3}
                  className="shrink-0 rounded-lg bg-ink px-4 py-2 font-semibold text-white disabled:opacity-40">
                  {recherche ? '…' : 'Chercher'}
                </button>
              </div>
              {suggestions.length > 0 && (
                <ul className="overflow-hidden rounded-lg border border-ink/20">
                  {suggestions.map((s) => (
                    <li key={s.label}>
                      <button type="button"
                        onClick={() => {
                          setTexte(s.label); setSuggestions([])
                          majConfig((c) => ({ ...c, adresse: s.label, lat: s.lat, lon: s.lon }))
                        }}
                        className="block w-full px-3 py-2 text-left hover:bg-cream">
                        {s.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {adresseChoisie && (
                <p className="rounded-lg bg-leaf/10 px-3 py-2 text-sm font-semibold text-leaf">
                  Adresse retenue — vous pouvez continuer.
                </p>
              )}
            </>
          )}

          {etape === 1 && (
            <>
              <Champ label="Surface habitable" valeur={m.surface_m2} suffixe="m²"
                onChange={(v) => majMaison({ surface_m2: v ?? 100 })} />
              <Nombre label="Occupants" valeur={m.nb_occupants} min={1} max={20}
                onChange={(v) => majMaison({ nb_occupants: v })} />
              <Champ label="Consommation annuelle d’électricité" valeur={m.conso_connue_kwh_an}
                suffixe="kWh" placeholder="je ne sais pas"
                aide="Sur votre facture. Si vous ne l’avez pas, nous l’estimerons — et nous vous le dirons."
                onChange={(v) => majMaison({ conso_connue_kwh_an: v })} />
              <Bascule label="C’est une résidence secondaire" actif={m.residence_secondaire}
                onChange={(v) => majMaison({ residence_secondaire: v })} />
            </>
          )}

          {etape === 2 && (
            <>
              <p className="text-dark/80">
                C’est la question qui change le plus de choses : le solaire se consomme quand
                il se produit.
              </p>
              <Choix label="En semaine, en journée" valeur={m.presence_journee} options={PRESENCES}
                onChange={(v) => majMaison({ presence_journee: v })} />
            </>
          )}

          {etape === 3 && (
            <>
              <Choix label="Chauffage" valeur={m.chauffage} options={CHAUFFAGES}
                onChange={(v) => majMaison({ chauffage: v })} />
              <Choix label="Eau chaude" valeur={m.ecs} options={ECS_OPTIONS}
                onChange={(v) => majMaison({ ecs: v })} />
            </>
          )}

          {etape === 4 && (
            <>
              <p className="text-dark/80">
                Cochez ce que vous avez <strong>déjà</strong>. Vous pourrez ajouter les
                équipements envisagés juste après, sur la scène.
              </p>
              <Bascule label="Climatisation" actif={m.clim.present}
                onChange={(v) => majMaison({ clim: { ...m.clim, present: v, deja_installe: true } })} />
              <Bascule label="Piscine" actif={m.piscine.present}
                onChange={(v) => majMaison({ piscine: { ...m.piscine, present: v, deja_installe: true } })} />
              <Bascule label="Voiture électrique" actif={m.voiture.present}
                onChange={(v) => majMaison({ voiture: { ...m.voiture, present: v, deja_installe: true } })} />
              <Bascule label="Je veux tenir en cas de coupure de courant" actif={m.besoin_secours}
                onChange={(v) => majMaison({ besoin_secours: v })}
                aide="Seule une batterie physique le permet — nous vous dirons ce qu’elle coûte vraiment." />
            </>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between gap-3">
          <button type="button" onClick={() => setEtape(Math.max(0, etape - 1))}
            disabled={etape === 0}
            className="rounded-lg border border-ink/20 px-4 py-2 font-semibold text-ink disabled:opacity-30">
            Retour
          </button>
          <button type="button" disabled={!peutAvancer}
            onClick={() => (etape === 4 ? onTerminer() : setEtape(etape + 1))}
            className="rounded-lg bg-primary px-5 py-2 font-semibold text-white disabled:opacity-40">
            {etape === 4 ? 'Voir ma maison' : 'Continuer'}
          </button>
        </div>
      </div>
    </div>
  )
}
