/**
 * Simulateur « maison + équipements ».
 *
 * On équipe une maison, on voit immédiatement ce que ça change. Un seul appel au moteur
 * par changement, avec anti-rebond ; la recherche d'options, plus coûteuse, n'est lancée
 * qu'à l'ouverture de l'onglet Étude et après un temps d'arrêt.
 *
 * AUCUN chiffre n'est écrit ici : tout vient de `/api/simulateur/*`.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, Check, Info, Save, Users } from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'
import Bandeau from '../components/simulateur/Bandeau'
import SceneMaison, { type EmplacementScene, type FluxScene } from '../components/simulateur/SceneMaison'
import ReglageEquipement, {
  EQUIPEMENTS, estInstalle, resumeDe, titreDe,
} from '../components/simulateur/ReglageEquipement'
import { Feuille } from '../components/simulateur/Reglage'
import {
  OngletAide, OngletEtude, OngletJournee, OngletMaison, OngletPanneaux, OngletStockage,
} from '../components/simulateur/Onglets'
import { Vide } from '../components/simulateur/Graphiques'
import Guide5Questions from '../components/simulateur/Guide5Questions'
import {
  calculer, chercherOptions, CONFIG_INITIALE, depuisUrl, euros, versUrl,
  type Config, type Option, type Options, type Resultat, type Saison,
} from '../lib/simulateur'

type Onglet = 'maison' | 'panneaux' | 'stockage' | 'journee' | 'etude' | 'aide'

const ONGLETS: { id: Onglet; label: string }[] = [
  { id: 'maison', label: 'Maison' },
  { id: 'panneaux', label: 'Panneaux' },
  { id: 'stockage', label: 'Stockage' },
  { id: 'journee', label: 'En direct' },
  { id: 'etude', label: 'Étude' },
  { id: 'aide', label: 'Aide' },
]

const ANTI_REBOND_MS = 200
const INACTIVITE_OPTIONS_MS = 2000

export default function SimulateurSolaire() {
  useTitle('Simulateur solaire — équipez votre maison | HELIOS')
  const { user, authFetch } = useAuth()

  const [config, setConfig] = useState<Config>(() => {
    const code = new URLSearchParams(window.location.search).get('c')
    return (code && depuisUrl(code)) || CONFIG_INITIALE
  })
  const [resultat, setResultat] = useState<Resultat | null>(null)
  const [options, setOptions] = useState<Options | null>(null)
  const [onglet, setOnglet] = useState<Onglet>('maison')
  const [emplacementOuvert, setEmplacementOuvert] = useState<string | null>(null)
  const [saison, setSaison] = useState<Saison>('ete')
  const [heure, setHeure] = useState(13)
  const [premierChargement, setPremierChargement] = useState(true)
  const [calculEnCours, setCalculEnCours] = useState(false)
  const [optionsEnCours, setOptionsEnCours] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [accueil, setAccueil] = useState(() =>
    !new URLSearchParams(window.location.search).get('c'))
  const [guide, setGuide] = useState(false)
  const [messageEtude, setMessageEtude] = useState<string | null>(null)

  const majConfig = useCallback((maj: (c: Config) => Config) => {
    setConfig((precedent) => maj(precedent))
  }, [])

  const localise = config.lat !== null && config.lon !== null

  /* --- Pré-remplissage depuis la fiche Maison, pour un utilisateur connecté --- */
  const prerempli = useRef(false)
  useEffect(() => {
    if (!user || prerempli.current) return
    prerempli.current = true
    authFetch('/api/houses/me')
      .then((r) => (r.ok ? r.json() : null))
      .then((fiche) => {
        if (!fiche) return
        setConfig((c) => ({
          ...c,
          adresse: c.adresse ?? fiche.code_postal ?? null,
          maison: {
            ...c.maison,
            surface_m2: fiche.surface_habitable ?? c.maison.surface_m2,
            nb_occupants: fiche.nb_occupants ?? c.maison.nb_occupants,
            chauffage: fiche.chauffage_principal ?? c.maison.chauffage,
            ecs: fiche.ecs ?? c.maison.ecs,
            conso_connue_kwh_an: fiche.conso_elec_kwh_an ?? c.maison.conso_connue_kwh_an,
            puissance_souscrite_kva: fiche.puissance_souscrite
              ? Number(fiche.puissance_souscrite) : c.maison.puissance_souscrite_kva,
            residence_secondaire: fiche.residence_principale === false,
            clim: { ...c.maison.clim, present: fiche.clim ?? c.maison.clim.present },
          },
          panneaux: {
            ...c.panneaux,
            orientation: fiche.orientation_toiture ?? c.panneaux.orientation,
            inclinaison: fiche.pente ?? c.panneaux.inclinaison,
            ombrage: fiche.ombrage ?? c.panneaux.ombrage,
            surface_toit_m2: fiche.surface_toit_exploitable ?? c.panneaux.surface_toit_m2,
          },
        }))
      })
      .catch(() => { /* la fiche est facultative */ })
  }, [user, authFetch])

  /* --- Le calcul, à chaque changement, avec anti-rebond et annulation --- */
  useEffect(() => {
    if (!localise) return
    const controleur = new AbortController()
    setCalculEnCours(true)
    const minuteur = setTimeout(() => {
      calculer(config, controleur.signal)
        .then((r) => { setResultat(r); setErreur(null) })
        .catch((e) => { if (e.name !== 'AbortError') setErreur(e.message) })
        .finally(() => {
          if (!controleur.signal.aborted) { setCalculEnCours(false); setPremierChargement(false) }
        })
    }, ANTI_REBOND_MS)
    return () => { clearTimeout(minuteur); controleur.abort() }
  }, [config, localise])

  /* --- Les options : à l'ouverture de l'onglet Étude, et après un temps d'arrêt --- */
  useEffect(() => {
    if (!localise) return
    const controleur = new AbortController()
    const attente = onglet === 'etude' ? ANTI_REBOND_MS : INACTIVITE_OPTIONS_MS
    const minuteur = setTimeout(() => {
      setOptionsEnCours(true)
      chercherOptions(config, controleur.signal)
        .then(setOptions)
        .catch(() => { /* silencieux : les options sont un complément, pas le cœur */ })
        .finally(() => { if (!controleur.signal.aborted) setOptionsEnCours(false) })
    }, attente)
    return () => { clearTimeout(minuteur); controleur.abort() }
  }, [config, localise, onglet])

  /* --- L'URL de partage : commune et coordonnées arrondies, jamais l'adresse --- */
  useEffect(() => {
    if (!localise) return
    const minuteur = setTimeout(() => {
      const code = versUrl(config, resultat?.lieu.commune ?? null)
      window.history.replaceState(null, '', `${window.location.pathname}?c=${code}`)
    }, 600)
    return () => clearTimeout(minuteur)
  }, [config, localise, resultat?.lieu.commune])

  /* --- Ce que la scène doit montrer --- */
  const equipements: EmplacementScene[] = useMemo(
    () => EQUIPEMENTS.map((e) => ({
      id: e.id,
      label: e.label,
      installe: estInstalle(e.id, config),
      resume: resumeDe(e.id, config, resultat),
    })),
    [config, resultat],
  )

  const flux: FluxScene = useMemo(() => {
    const point = resultat?.journees[saison]?.[heure]
    if (!point) {
      return { soleilMaison: 0, soleilBatterie: 0, soleilReseau: 0, reseauMaison: 0, batterieMaison: 0 }
    }
    return {
      soleilMaison: point.direct,
      soleilBatterie: point.charge,
      soleilReseau: point.injecte + point.stocke_virtuel,
      reseauMaison: point.achat + point.restitue_virtuel,
      batterieMaison: point.decharge,
    }
  }, [resultat, saison, heure])

  const appliquerOption = (option: Option) => {
    majConfig((c) => ({
      ...c,
      panneaux: {
        ...c.panneaux,
        nb_panneaux: option.configuration.nb_panneaux,
        nb_panneaux_carport: option.configuration.nb_panneaux_carport,
      },
      stockage: {
        ...c.stockage,
        nb_packs: option.configuration.nb_packs,
        batterie_virtuelle: option.configuration.batterie_virtuelle,
        pilotage: option.configuration.pilotage,
      },
    }))
  }

  const appliquerProchaineEtape = () => {
    const etape = options?.prochaine_etape
    if (!etape) return
    majConfig((c) => ({
      ...c,
      panneaux: etape.appliquer.nb_panneaux !== undefined
        ? { ...c.panneaux, nb_panneaux: etape.appliquer.nb_panneaux }
        : c.panneaux,
      stockage: {
        ...c.stockage,
        nb_packs: etape.appliquer.nb_packs ?? c.stockage.nb_packs,
        batterie_virtuelle: etape.appliquer.batterie_virtuelle ?? c.stockage.batterie_virtuelle,
        pilotage: etape.appliquer.pilotage ?? c.stockage.pilotage,
      },
    }))
  }

  const enregistrerEtude = async () => {
    setMessageEtude(null)
    try {
      const reponse = await authFetch('/api/simulateur/etudes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ configuration: config }),
      })
      if (reponse.ok) {
        setMessageEtude('Étude enregistrée. Vous la retrouverez dans votre espace, et Helios s’en sert dans le chat.')
      } else if (reponse.status === 409) {
        setMessageEtude('Créez d’abord votre fiche Maison pour enregistrer une étude.')
      } else {
        setMessageEtude('L’enregistrement n’a pas abouti. Réessayez dans un instant.')
      }
    } catch {
      setMessageEtude('L’enregistrement n’a pas abouti. Réessayez dans un instant.')
    }
  }

  /* --- Accueil : se laisser guider, ou tout régler soi-même --- */
  if (accueil) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="font-display text-3xl font-bold text-ink sm:text-4xl">
          Équipez votre maison, voyez ce que ça change
        </h1>
        <p className="mt-3 text-lg text-dark/80">
          Le soleil de votre adresse, votre consommation réelle, heure par heure sur une année
          entière. Vous ajoutez des panneaux, une batterie, une voiture — les chiffres bougent
          devant vous. Sans compte, sans engagement.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <button type="button" onClick={() => { setAccueil(false); setGuide(true) }}
            className="rounded-xl bg-primary px-5 py-4 text-left text-white transition hover:bg-primary/90">
            <span className="block font-display text-lg font-bold">Me laisser guider</span>
            <span className="block text-sm text-white/90">5 questions simples — recommandé</span>
          </button>
          <button type="button" onClick={() => setAccueil(false)}
            className="rounded-xl border-2 border-primary px-5 py-4 text-left text-primary transition
              hover:bg-primary hover:text-white">
            <span className="block font-display text-lg font-bold">Tout régler moi-même</span>
            <span className="block text-sm opacity-90">J’ai déjà mes informations sous la main</span>
          </button>
        </div>
        <p className="mt-8 text-sm text-dark/60">
          Tous les résultats sont des <strong>estimations</strong>. Les hypothèses sont affichées
          dans l’onglet Étude, et ne remplacent pas l’étude d’un installateur certifié.
        </p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-cream">
      <Bandeau indicateurs={resultat?.indicateurs ?? null} calculEnCours={calculEnCours} />

      {guide && (
        <Guide5Questions config={config} majConfig={majConfig} onTerminer={() => setGuide(false)} />
      )}

      <div className="mx-auto max-w-6xl px-4 py-6">
        {!localise && (
          <div className="mb-3 rounded-lg border border-primary/30 bg-white px-3 py-2">
            <p className="flex items-center gap-2 text-sm text-ink">
              <Info size={16} className="shrink-0 text-primary" />
              <span>
                Commencez par votre adresse, onglet <strong>Maison</strong> — elle donne
                l’ensoleillement réel de votre commune.
              </span>
            </p>
          </div>
        )}

        {erreur && (
          <div className="mb-6 rounded-xl border border-terra/40 bg-terra/10 p-4 text-ink">
            <p className="flex items-start gap-3">
              <AlertTriangle size={20} className="mt-0.5 shrink-0 text-terra" />
              <span>{erreur}</span>
            </p>
          </div>
        )}

        {resultat?.alertes.map((alerte) => (
          <div key={alerte.texte}
            className={`mb-3 rounded-xl border p-4 text-ink ${alerte.niveau === 'attention'
              ? 'border-terra/40 bg-terra/10' : 'border-sky/40 bg-sky/10'}`}>
            <p className="flex items-start gap-3">
              {alerte.niveau === 'attention'
                ? <AlertTriangle size={20} className="mt-0.5 shrink-0 text-terra" />
                : <Info size={20} className="mt-0.5 shrink-0 text-sky" />}
              <span>{alerte.texte}</span>
            </p>
          </div>
        ))}

        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <div className="min-w-0">
            <section className="rounded-xl border border-ink/10 bg-white p-4">
              {premierChargement && localise ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-56 rounded-lg bg-cream" />
                  <div className="h-4 w-2/3 rounded bg-cream" />
                  <div className="h-4 w-1/2 rounded bg-cream" />
                </div>
              ) : (
                <SceneMaison equipements={equipements} heure={heure} saison={saison} flux={flux}
                  onEmplacement={setEmplacementOuvert} />
              )}
            </section>

            {options?.prochaine_etape && (
              <section className="mt-4 rounded-xl border-2 border-primary bg-white p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-primary">Prochaine étape</p>
                <h2 className="mt-1 font-display text-xl font-bold text-ink">
                  {options.prochaine_etape.libelle}
                </h2>
                <p className="mt-1 text-dark/80">
                  {euros(options.prochaine_etape.gain_annuel_eur)} par an sur la facture ·
                  investissement {euros(options.prochaine_etape.investissement_eur)}
                </p>
                <button type="button" onClick={appliquerProchaineEtape}
                  className="mt-3 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2
                    font-semibold text-white hover:bg-primary/90">
                  Appliquer <ArrowRight size={18} />
                </button>
              </section>
            )}

            {/* Le compte est la priorité : cette simulation n'est qu'une porte d'entrée. Ce qui
                vaut vraiment, c'est qu'Helios garde la maison en mémoire et réponde ensuite sur
                CE foyer. D'où un bouton unique et net, et trois promesses concrètes plutôt qu'une
                phrase d'invitation. La mise en relation reste en second : elle ne se déclenche
                qu'à la demande, et le dire est une obligation de la charte. */}
            <section className="mt-4 rounded-xl border border-ink/10 bg-white p-4">
              <h2 className="font-display text-lg font-bold text-ink">Et ensuite ?</h2>

              {user ? (
                <>
                  <button type="button" onClick={enregistrerEtude}
                    className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg
                      bg-primary px-4 py-2.5 font-semibold text-white hover:bg-primary/90">
                    <Save size={18} /> Enregistrer mon étude
                  </button>
                  {messageEtude && <p className="mt-2 text-sm text-dark/80">{messageEtude}</p>}
                  <p className="mt-2 text-sm text-dark/70">
                    Elle rejoint votre maison : Helios s’en servira quand vous lui poserez
                    une question.
                  </p>
                </>
              ) : (
                <>
                  <Link to="/inscription"
                    className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg
                      bg-primary px-4 py-2.5 font-semibold text-white hover:bg-primary/90">
                    Créer mon compte gratuit <ArrowRight size={18} />
                  </Link>
                  <ul className="mt-3 space-y-1.5 text-sm text-dark/80">
                    <li className="flex items-start gap-2">
                      <Check size={16} className="mt-0.5 shrink-0 text-leaf" />
                      Vos études sont conservées, et vous les reprenez quand vous voulez.
                    </li>
                    <li className="flex items-start gap-2">
                      <Check size={16} className="mt-0.5 shrink-0 text-leaf" />
                      Vous complétez votre maison pièce par pièce — plus Helios la connaît,
                      plus ses réponses sont justes.
                    </li>
                    <li className="flex items-start gap-2">
                      <Check size={16} className="mt-0.5 shrink-0 text-leaf" />
                      Vous lui demandez ce que vous voulez, sur votre logement à vous.
                    </li>
                  </ul>
                  <p className="mt-2 text-sm text-dark/60">
                    Rien n’est enregistré pour l’instant.
                  </p>
                </>
              )}

              <p className="mt-4 border-t border-ink/10 pt-3 text-sm text-dark/80">
                Helios peut aussi vous orienter vers des <strong>installateurs</strong>, de votre
                région ou nationaux, retenus parce qu’ils ont accepté la charte Helios.
              </p>
              <p className="mt-2 text-sm text-dark/80">
                Et le moment venu, montrez-lui un devis : il vous dira ce qu’il en pense.
              </p>

              <Link to="/espace/mises-en-relation"
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg
                  border border-ink px-4 py-2 font-semibold text-ink hover:bg-ink hover:text-white">
                <Users size={18} /> Être mis en relation
              </Link>
              <p className="mt-2 text-sm text-dark/60">
                Uniquement si vous le demandez, et avec votre consentement. Helios n’est jamais
                payé par vous, et ne transmet rien sans votre accord.
              </p>
            </section>
          </div>

          <div className="min-w-0">
            <div role="tablist" aria-label="Sections du simulateur"
              className="mb-4 flex gap-1 overflow-x-auto rounded-xl border border-ink/10 bg-white p-1">
              {ONGLETS.map((o) => (
                <button key={o.id} role="tab" type="button" aria-selected={onglet === o.id}
                  onClick={() => setOnglet(o.id)}
                  className={`shrink-0 rounded-lg px-3 py-2 text-sm font-semibold transition
                    ${onglet === o.id ? 'bg-primary text-white' : 'text-ink hover:bg-cream'}`}>
                  {o.label}
                </button>
              ))}
            </div>

            {onglet === 'maison' && (
              <OngletMaison config={config} resultat={resultat} majConfig={majConfig} />
            )}
            {onglet === 'panneaux' && (
              localise
                ? <OngletPanneaux config={config} resultat={resultat} majConfig={majConfig} />
                : <Vide message="Renseignez d’abord votre adresse, dans l’onglet Maison." />
            )}
            {onglet === 'stockage' && (
              <OngletStockage config={config} resultat={resultat} majConfig={majConfig} />
            )}
            {onglet === 'journee' && (
              <OngletJournee resultat={resultat} saison={saison} setSaison={setSaison}
                heure={heure} setHeure={setHeure} />
            )}
            {onglet === 'etude' && (
              <OngletEtude config={config} resultat={resultat} majConfig={majConfig}
                options={options} chargementOptions={optionsEnCours}
                onAppliquerOption={appliquerOption} />
            )}
            {onglet === 'aide' && <OngletAide />}
          </div>
        </div>
      </div>

      <Feuille titre={titreDe(emplacementOuvert ?? '')} ouvert={emplacementOuvert !== null}
        onFermer={() => setEmplacementOuvert(null)}>
        {emplacementOuvert && (
          <ReglageEquipement id={emplacementOuvert} config={config} resultat={resultat}
            majConfig={majConfig} />
        )}
      </Feuille>
    </div>
  )
}
