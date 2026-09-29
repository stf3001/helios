/**
 * Simulateur « maison + équipements ».
 *
 * On équipe une maison, on voit immédiatement ce que ça change. Un seul appel au moteur
 * par changement, avec anti-rebond ; la recherche d'options, plus coûteuse, n'est lancée
 * qu'à l'ouverture de l'onglet Étude et après un temps d'arrêt.
 *
 * MISE EN PAGE (28/09/2026) — celle d'un configurateur, comme chez AD Solar : la scène
 * occupe le centre et prend toute la place disponible, les réglages flottent à sa gauche
 * derrière un rail d'icônes, les indicateurs se posent en carte en haut à droite, et
 * « Et ensuite ? » passe en pleine largeur sous l'ensemble.
 *
 * Le pivot est à `xl` (1280 px) et non à `lg` : en dessous, une troisième colonne ne tient
 * pas sans ramener la scène à 400 px de large, ce qui est exactement ce qu'on cherche à
 * éviter. Sous ce seuil, les indicateurs redeviennent un bandeau en haut, les onglets une
 * barre en bas, et la scène prend toute la largeur — elle y est plus grande encore.
 *
 * Les deux cartes flottantes ont leur gouttière RÉSERVÉE dans la grille : elles ont l'air
 * posées sur la scène, mais elles n'en cachent rien. Un panneau par-dessus l'illustration
 * masquerait la voiture et le garage, qui sont deux emplacements d'équipement cliquables.
 *
 * AUCUN chiffre n'est écrit ici : tout vient de `/api/simulateur/*`.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity, AlertTriangle, ArrowRight, BatteryCharging, Check, CircleHelp, ClipboardList,
  House, Info, Save, Sun, Users, type LucideIcon,
} from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'
import Bandeau from '../components/simulateur/Bandeau'
import SceneMaison, { type EmplacementScene, type FluxScene } from '../components/simulateur/SceneMaison'
import ReglageEquipement, {
  EQUIPEMENTS, estInstalle, resumeDe, titreDe,
} from '../components/simulateur/ReglageEquipement'
import { Feuille } from '../components/simulateur/Reglage'
import ReglageJardin from '../components/simulateur/ReglageJardin'
import {
  OngletAide, OngletEtude, OngletJournee, OngletMaison, OngletPanneaux, OngletStockage,
} from '../components/simulateur/Onglets'
import {
  calculerJardin, JARDIN_INITIAL, type JardinConfig, type JardinResultat,
} from '../lib/jardin'
import { Vide } from '../components/simulateur/Graphiques'
import Guide5Questions from '../components/simulateur/Guide5Questions'
import {
  calculer, CHAUFFAGES, chercherOptions, CONFIG_INITIALE, depuisUrl, ECS_OPTIONS, euros,
  OMBRAGES, ORIENTATIONS, versUrl,
  type Config, type Option, type Options, type Resultat, type Saison,
} from '../lib/simulateur'

type Onglet = 'maison' | 'panneaux' | 'stockage' | 'journee' | 'etude' | 'aide'

/**
 * Chaque onglet porte une icône : c'est elle qu'on voit dans le rail de gauche et dans la
 * barre du bas. Le mot reste écrit dessous, en petit — une icône seule se devine, elle ne
 * se lit pas, et « Étude » n'a pas de pictogramme évident.
 */
const ONGLETS: { id: Onglet; label: string; Icone: LucideIcon }[] = [
  { id: 'maison', label: 'Maison', Icone: House },
  { id: 'panneaux', label: 'Panneaux', Icone: Sun },
  { id: 'stockage', label: 'Stockage', Icone: BatteryCharging },
  { id: 'journee', label: 'En direct', Icone: Activity },
  { id: 'etude', label: 'Étude', Icone: ClipboardList },
  { id: 'aide', label: 'Aide', Icone: CircleHelp },
]

/**
 * Une valeur venue de la fiche Maison n'entre dans la configuration QUE si le simulateur
 * la connaît. Sinon on garde le défaut.
 *
 * Trouvé en production le 29/09/2026 : la fiche de Stéphane porte
 * `orientation_toiture: "SUD"`, en capitales, et le simulateur la recopiait telle quelle
 * dans un champ qui n'accepte que « sud ». L'API refusait alors CHAQUE calcul avec un 422,
 * et l'écran restait muet — des tirets partout, aucun message. Un utilisateur connecté
 * dans ce cas n'avait tout simplement pas de simulateur, sans comprendre pourquoi.
 *
 * La comparaison ignore la casse et les espaces : c'est la seule souplesse qu'on
 * s'autorise. Une valeur vraiment inconnue est ignorée, jamais devinée — mieux vaut un
 * défaut visible et modifiable qu'un champ rempli de travers.
 */
function valeurAdmise<T extends string>(
  brut: unknown, admises: readonly { value: T }[], defaut: T,
): T {
  if (typeof brut !== 'string') return defaut
  const nettoye = brut.trim().toLowerCase()
  return admises.find((o) => o.value.toLowerCase() === nettoye)?.value ?? defaut
}

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

  /* --- Le jardin ---
     Il vit À CÔTÉ de `config`, et c'est voulu : un potager ne produit pas d'électricité,
     il n'entre dans aucun bilan du moteur horaire, et il n'a rien à faire dans l'URL de
     partage d'une étude solaire. La scène le montre, le calcul est ailleurs.

     `jardinOuvert` ne devient vrai qu'une fois le potager cliqué : avant, son repère
     affiche un « + », comme tout emplacement non équipé. On ne calcule donc rien pour
     un visiteur qui ne s'y intéresse pas. */
  const [jardinOuvert, setJardinOuvert] = useState(false)
  const [jardinConfig, setJardinConfig] = useState<JardinConfig>(JARDIN_INITIAL)
  const [jardinResultat, setJardinResultat] = useState<JardinResultat | null>(null)
  const [jardinErreur, setJardinErreur] = useState<string | null>(null)

  /* Pour amener les réglages sous les yeux quand on choisit un onglet dans la barre du bas. */
  const panneauReglages = useRef<HTMLDivElement>(null)

  /* Le calque d'accueil bloque le défilement de la page derrière lui, et Échap le ferme —
     ce qui revient à choisir « tout régler moi-même », le choix qui n'engage à rien. */
  useEffect(() => {
    if (!accueil) return
    const echap = (e: KeyboardEvent) => { if (e.key === 'Escape') setAccueil(false) }
    window.addEventListener('keydown', echap)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', echap)
      document.body.style.overflow = ''
    }
  }, [accueil])

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
            chauffage: valeurAdmise(fiche.chauffage_principal, CHAUFFAGES, c.maison.chauffage),
            ecs: valeurAdmise(fiche.ecs, ECS_OPTIONS, c.maison.ecs),
            conso_connue_kwh_an: fiche.conso_elec_kwh_an ?? c.maison.conso_connue_kwh_an,
            puissance_souscrite_kva: fiche.puissance_souscrite
              ? Number(fiche.puissance_souscrite) : c.maison.puissance_souscrite_kva,
            residence_secondaire: fiche.residence_principale === false,
            clim: { ...c.maison.clim, present: fiche.clim ?? c.maison.clim.present },
          },
          panneaux: {
            ...c.panneaux,
            orientation: valeurAdmise(fiche.orientation_toiture, ORIENTATIONS, c.panneaux.orientation),
            inclinaison: fiche.pente ?? c.panneaux.inclinaison,
            ombrage: valeurAdmise(fiche.ombrage, OMBRAGES, c.panneaux.ombrage),
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

  /* --- Le calcul du jardin, une fois le potager ouvert --- */
  useEffect(() => {
    if (!jardinOuvert) return
    const controleur = new AbortController()
    const minuteur = setTimeout(() => {
      calculerJardin(jardinConfig, controleur.signal)
        .then((r) => { setJardinResultat(r); setJardinErreur(null) })
        .catch((e) => { if (e.name !== 'AbortError') setJardinErreur(e.message) })
    }, ANTI_REBOND_MS)
    return () => { clearTimeout(minuteur); controleur.abort() }
  }, [jardinConfig, jardinOuvert])

  /* Le code postal de l'adresse sert la zone de jardinage (nord ou sud), rien d'autre. */
  useEffect(() => {
    const code = config.adresse?.match(/\b(\d{5})\b/)?.[1] ?? null
    setJardinConfig((c) => (c.code_postal === code ? c : { ...c, code_postal: code }))
  }, [config.adresse])

  /* --- Ce que la scène doit montrer --- */
  const equipements: EmplacementScene[] = useMemo(
    () => [
      ...EQUIPEMENTS.map((e) => ({
        id: e.id,
        label: e.label,
        installe: estInstalle(e.id, config),
        resume: resumeDe(e.id, config, resultat),
      })),
      {
        id: 'jardin',
        label: 'Jardin',
        installe: jardinOuvert,
        resume: jardinResultat
          ? `${jardinResultat.surface_totale_m2} m² · ${jardinResultat.couverture_pct} % de vos légumes`
          : null,
      },
    ],
    [config, resultat, jardinOuvert, jardinResultat],
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

  const ongletActif = ONGLETS.find((o) => o.id === onglet)

  /* Le contenu de l'onglet courant, rendu UNE SEULE FOIS : il passe de la colonne de gauche
     (grand écran) au flux de la page (petit écran) par l'ordre de la grille, jamais par un
     second rendu — deux instances montées, ce sont deux recherches d'adresse. */
  const contenuOnglet = (
    <>
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
    </>
  )

  return (
    <div className="min-h-screen bg-cream">
      {/* Petit écran : les indicateurs en bandeau, collés sous l'en-tête du site. */}
      <Bandeau indicateurs={resultat?.indicateurs ?? null} calculEnCours={calculEnCours}
        variante="bandeau" />

      {guide && (
        <Guide5Questions config={config} majConfig={majConfig} onTerminer={() => setGuide(false)} />
      )}

      <div className="mx-auto max-w-[110rem] px-3 pb-4 pt-3 sm:px-4 xl:pb-10">
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
          <div className="mb-3 rounded-xl border border-terra/40 bg-terra/10 p-4 text-ink">
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

        {/* Largeur de la colonne de gauche : elle est calée sur la rangée de commandes de
            l'onglet « En direct », la plus exigeante — bouton de lecture (44 px) et heure
            (64 px) sont de taille fixe, et tout ce qui reste va au curseur des 24 heures.
            À 19rem il tombait à 49 px, deux pixels par heure ; à 22rem il en fait 100. Les
            quatre saisons, elles, restent sur deux rangées : les mettre sur une seule
            demande 312 px de rangée contre 181 auparavant, soit 130 px pris sur la scène —
            un mauvais échange pour un repli qui se lit très bien. */}
        <div className="grid items-start gap-3 xl:grid-cols-[22rem_minmax(0,1fr)_15rem]
          2xl:gap-4 2xl:grid-cols-[24rem_minmax(0,1fr)_17rem]">

          {/* ---------- LES RÉGLAGES, flottants à gauche ---------- */}
          <aside ref={panneauReglages}
            className="order-2 min-w-0 scroll-mt-36 xl:sticky xl:top-20 xl:order-1 xl:self-start
              xl:scroll-mt-0 xl:overflow-hidden xl:rounded-2xl xl:border xl:border-ink/10
              xl:bg-cream/80 xl:shadow-xl xl:backdrop-blur">
            <div className="xl:flex">
              {/* Le rail : les onglets en icônes, à demeure le long du panneau. */}
              <div role="tablist" aria-orientation="vertical" aria-label="Sections du simulateur"
                className="hidden shrink-0 flex-col gap-1 border-r border-ink/10 p-1.5 xl:flex">
                {ONGLETS.map(({ id, label, Icone }) => (
                  <button key={id} role="tab" type="button" aria-selected={onglet === id}
                    aria-controls="panneau-reglages" onClick={() => setOnglet(id)}
                    className={`flex w-[3.75rem] flex-col items-center gap-1 rounded-xl px-1 py-2
                      text-[10px] font-semibold leading-none transition
                      ${onglet === id ? 'bg-primary text-white shadow' : 'text-ink hover:bg-white'}`}>
                    <Icone size={20} strokeWidth={onglet === id ? 2.4 : 2} aria-hidden="true" />
                    <span className="w-full truncate text-center">{label}</span>
                  </button>
                ))}
              </div>

              <div id="panneau-reglages" role="tabpanel" aria-label={ongletActif?.label}
                className="min-w-0 flex-1 xl:max-h-[calc(100vh-7rem)] xl:overflow-y-auto xl:p-2">
                {/* Le titre rend le rail lisible : une icône allumée ne dit pas son nom. */}
                <h2 className="hidden px-2 py-1 font-display text-lg font-bold text-ink xl:block">
                  {ongletActif?.label}
                </h2>
                {contenuOnglet}
              </div>
            </div>
          </aside>

          {/* ---------- LA SCÈNE, au centre et en grand ---------- */}
          <div className="order-1 min-w-0 xl:order-2">
            {premierChargement && localise ? (
              <div className="animate-pulse">
                <div className="aspect-[1105/638] w-full rounded-xl bg-white/70" />
                <div className="mx-auto mt-3 h-4 w-2/3 rounded bg-white/70" />
              </div>
            ) : (
              <SceneMaison equipements={equipements} eolienne={config.eolien.kwc > 0}
                heure={heure} saison={saison} flux={flux}
                onEmplacement={(id) => {
                  if (id === 'jardin') setJardinOuvert(true)
                  setEmplacementOuvert(id)
                }} />
            )}

            {options?.prochaine_etape && (
              <section className="mt-3 rounded-xl border-2 border-primary bg-white p-4">
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
          </div>

          {/* ---------- LES INDICATEURS, en carte en haut à droite ---------- */}
          <div className="order-3 hidden xl:sticky xl:top-20 xl:block xl:self-start">
            <Bandeau indicateurs={resultat?.indicateurs ?? null} calculEnCours={calculEnCours}
              variante="carte" />
          </div>
        </div>

        {/* ---------- ET ENSUITE ? en pleine largeur ----------
            Le compte est la priorité : cette simulation n'est qu'une porte d'entrée. Ce qui
            vaut vraiment, c'est qu'Helios garde la maison en mémoire et réponde ensuite sur
            CE foyer. D'où un bouton unique et net, et trois promesses concrètes plutôt qu'une
            phrase d'invitation. La mise en relation reste en second : elle ne se déclenche
            qu'à la demande, et le dire est une obligation de la charte.
            En pleine largeur, les deux propos se rangent côte à côte au lieu de s'empiler,
            et les boutons cessent d'être étirés d'un bord à l'autre de la page. */}
        <section className="mt-4 rounded-2xl border border-ink/10 bg-white p-4 sm:p-6">
          <h2 className="font-display text-xl font-bold text-ink">Et ensuite ?</h2>

          <div className="mt-3 grid gap-5 md:grid-cols-2 md:gap-8">
            <div>
              {user ? (
                <>
                  <button type="button" onClick={enregistrerEtude}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg
                      bg-primary px-4 py-2.5 font-semibold text-white hover:bg-primary/90 sm:w-auto">
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
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg
                      bg-primary px-4 py-2.5 font-semibold text-white hover:bg-primary/90 sm:w-auto">
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
            </div>

            <div className="border-t border-ink/10 pt-4 md:border-l md:border-t-0 md:pl-8 md:pt-0">
              <p className="text-sm text-dark/80">
                Helios peut aussi vous orienter vers des <strong>installateurs</strong>, de votre
                région ou nationaux, retenus parce qu’ils ont accepté la charte Helios.
              </p>
              <p className="mt-2 text-sm text-dark/80">
                Et le moment venu, montrez-lui un devis : il vous dira ce qu’il en pense.
              </p>

              <Link to="/espace/mises-en-relation"
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg
                  border border-ink px-4 py-2 font-semibold text-ink hover:bg-ink hover:text-white
                  sm:w-auto">
                <Users size={18} /> Être mis en relation
              </Link>
              <p className="mt-2 text-sm text-dark/60">
                Uniquement si vous le demandez, et avec votre consentement. Helios n’est jamais
                payé par vous, et ne transmet rien sans votre accord.
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* ---------- PETIT ÉCRAN : la barre d'onglets en bas ----------
          Le pouce l'atteint sans quitter la scène. Choisir un onglet amène les réglages sous
          les yeux : sans ce défilement, on toucherait « Panneaux » sans rien voir changer,
          puisque le panneau vit plus bas dans la page. Le bandeau d'indicateurs, lui, reste
          collé en haut pendant ce trajet.

          `sticky` et non `fixed` : la barre garde sa place dans le flux, tout en bas du
          simulateur. Elle flotte donc au bord de l'écran tant qu'on règle, puis s'arrête
          d'elle-même et rend le pied de page entier — une barre fixée en masquait la
          dernière ligne, sans qu'aucun rembourrage de cette page ne puisse y remédier,
          le pied de page appartenant à la mise en page du site. */}
      <nav role="tablist" aria-label="Sections du simulateur"
        className="sticky bottom-0 z-20 border-t border-ink/10 bg-cream/95
          pb-[env(safe-area-inset-bottom)] backdrop-blur xl:hidden">
        <div className="mx-auto flex max-w-2xl">
          {ONGLETS.map(({ id, label, Icone }) => (
            <button key={id} role="tab" type="button" aria-selected={onglet === id}
              aria-controls="panneau-reglages"
              onClick={() => {
                setOnglet(id)
                panneauReglages.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
              }}
              className={`flex flex-1 flex-col items-center gap-1 px-0.5 py-1.5 text-[10px]
                font-semibold leading-none transition
                ${onglet === id ? 'text-primary' : 'text-dark/60'}`}>
              <span className={`flex h-7 w-10 items-center justify-center rounded-full
                ${onglet === id ? 'bg-primary text-white' : ''}`}>
                <Icone size={18} strokeWidth={onglet === id ? 2.4 : 2} aria-hidden="true" />
              </span>
              <span className="w-full truncate text-center">{label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* ---------- LE CALQUE D'ACCUEIL ----------
          La maison est DERRIÈRE, visible et déjà dessinée. Avant, ce choix occupait une
          page à lui seul, sans la moindre image : on demandait au visiteur de se décider
          sur un simulateur qu'il n'avait pas encore vu. Ici il voit ce qu'il vient
          chercher, et le calque ne fait que lui demander par quel bout le prendre. */}
      {accueil && (
        <div role="dialog" aria-modal="true" aria-labelledby="accueil-titre"
          className="fixed inset-0 z-40 flex items-center justify-center overflow-y-auto
            bg-ink/40 px-4 py-8 backdrop-blur-[3px]">
          <div className="animate-slide-up w-full max-w-2xl rounded-2xl border border-white/60
            bg-white/95 p-6 shadow-2xl sm:p-8">
            <h1 id="accueil-titre" className="font-display text-2xl font-bold text-ink sm:text-3xl">
              Équipez votre maison, voyez ce que ça change
            </h1>
            <p className="mt-3 text-dark/80">
              Le soleil de votre adresse, votre consommation réelle, heure par heure sur une
              année entière. Vous ajoutez des panneaux, une batterie, une voiture — les
              chiffres bougent devant vous. Sans compte, sans engagement.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <button type="button" onClick={() => { setAccueil(false); setGuide(true) }}
                className="rounded-xl bg-primary px-5 py-4 text-left text-white transition
                  hover:bg-primary/90">
                <span className="block font-display text-lg font-bold">Me laisser guider</span>
                <span className="block text-sm text-white/90">5 questions simples — recommandé</span>
              </button>
              <button type="button" onClick={() => setAccueil(false)}
                className="rounded-xl border-2 border-primary px-5 py-4 text-left text-primary
                  transition hover:bg-primary hover:text-white">
                <span className="block font-display text-lg font-bold">Tout régler moi-même</span>
                <span className="block text-sm opacity-90">J’ai déjà mes informations sous la main</span>
              </button>
            </div>
            <p className="mt-5 text-sm text-dark/60">
              Tous les résultats sont des <strong>estimations</strong>. Les hypothèses sont
              affichées dans l’onglet Étude, et ne remplacent pas l’étude d’un installateur
              certifié.
            </p>
          </div>
        </div>
      )}

      <Feuille
        titre={emplacementOuvert === 'jardin' ? 'Le jardin' : titreDe(emplacementOuvert ?? '')}
        ouvert={emplacementOuvert !== null}
        onFermer={() => setEmplacementOuvert(null)}>
        {emplacementOuvert === 'jardin' ? (
          <ReglageJardin config={jardinConfig} resultat={jardinResultat}
            majConfig={(maj) => setJardinConfig(maj)} erreur={jardinErreur} />
        ) : emplacementOuvert && (
          <ReglageEquipement id={emplacementOuvert} config={config} resultat={resultat}
            majConfig={majConfig} />
        )}
      </Feuille>
    </div>
  )
}
