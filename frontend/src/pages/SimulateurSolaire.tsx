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
 * LE PIVOT EST DESCENDU DE `xl` (1280 px) À `md` (768 px) LE 01/10/2026. Il avait été posé
 * à 1280 parce qu'en dessous, trois colonnes dépliées ramenaient la scène à 400 px de large.
 * Résultat : toute fenêtre plus étroite que 1280 — c'est-à-dire la plupart des portables —
 * retombait sur la mise en page de téléphone, onglets en barre du bas et indicateurs en
 * bandeau. Sur un ordinateur, ce n'est pas ce qu'on veut montrer.
 *
 * CE QUI REND LA CHOSE POSSIBLE : sous `xl`, la colonne de gauche ne contient plus que le
 * RAIL d'icônes (4,75 rem), et le panneau de réglages s'ouvre en CALQUE par-dessus la scène
 * plutôt que de lui prendre une colonne. La scène garde donc sa largeur quoi qu'il arrive.
 * À partir de `xl`, rien ne change : le panneau reprend sa gouttière réservée, parce que
 * la place existe et qu'un panneau posé à côté vaut mieux qu'un panneau posé dessus.
 *
 * L'objection d'origine — « un panneau par-dessus l'illustration masquerait la voiture et le
 * garage, qui sont des emplacements cliquables » — tient toujours, et c'est pour cela que
 * sous `xl` les réglages DÉMARRENT REPLIÉS (voir `reglagesReplies`) : le calque n'apparaît
 * que si on le demande, et se referme d'un clic.
 *
 * Sous 768 px, rien ne change non plus : indicateurs en bandeau, onglets en barre du bas,
 * scène en pleine largeur.
 *
 * La carte des indicateurs, elle, garde sa gouttière réservée à toutes les tailles : elle
 * est à droite, là où l'illustration n'a que du ciel et du potager.
 *
 * AUCUN chiffre n'est écrit ici : tout vient de `/api/simulateur/*`.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity, AlertTriangle, ArrowRight, BatteryCharging, Check, CircleHelp, ClipboardList,
  House, Info, PanelLeftClose, PanelLeftOpen, Plug, Save, Sun, Users, type LucideIcon,
} from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'
import Bandeau from '../components/simulateur/Bandeau'
import SceneMaison, { type EmplacementScene, type FluxScene } from '../components/simulateur/SceneMaison'
import ReglageEquipement, {
  EQUIPEMENTS, estInstalle, resumeDe, titreDe,
} from '../components/simulateur/ReglageEquipement'
import { Bascule, Feuille } from '../components/simulateur/Reglage'
import ReglageJardin from '../components/simulateur/ReglageJardin'
import {
  OngletAide, OngletEnergie, OngletEtude, OngletJournee, OngletMaison, OngletPanneaux,
  OngletStockage,
} from '../components/simulateur/Onglets'
import {
  CONTRAT_INITIAL, OPTIONS_TARIFAIRES, versFicheMaison, type Contrat, type OptionTarifaire,
  type Plage,
} from '../lib/contrat'
import { fournisseurDepuisLibelle, libelleFournisseur } from '../data/fournisseurs'
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

type Onglet = 'maison' | 'energie' | 'panneaux' | 'stockage' | 'journee' | 'etude' | 'aide'

/**
 * Chaque onglet porte une icône : c'est elle qu'on voit dans le rail de gauche et dans la
 * barre du bas. Le mot reste écrit dessous, en petit — une icône seule se devine, elle ne
 * se lit pas, et « Étude » n'a pas de pictogramme évident.
 */
const ONGLETS: { id: Onglet; label: string; Icone: LucideIcon }[] = [
  { id: 'maison', label: 'Maison', Icone: House },
  { id: 'energie', label: 'Énergie', Icone: Plug },
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

/**
 * Le même garde-fou pour les nombres de la fiche Maison, et pour la même raison :
 * un nombre hors des bornes de l'API fait échouer le calcul dès l'ouverture, alors
 * que l'utilisateur n'a touché à rien et n'a donc aucun champ à corriger.
 *
 * Une fiche peut porter une consommation à 50 kWh ou une puissance en texte
 * (`"9 kVA"` donne NaN) : dans les deux cas on retombe sur le défaut du simulateur,
 * visible et modifiable, plutôt que d'envoyer une valeur que le serveur refusera.
 */
function nombreAdmis(brut: unknown, min: number, max: number, defaut: number): number {
  const n = typeof brut === 'string' ? Number(brut) : brut
  if (typeof n !== 'number' || !Number.isFinite(n)) return defaut
  const entier = Math.round(n)
  return entier >= min && entier <= max ? entier : defaut
}

/** Idem pour un nombre facultatif : hors bornes, on préfère le vide au refus. */
function nombreAdmisOuVide(brut: unknown, min: number, max: number): number | null {
  if (brut === null || brut === undefined) return null
  const n = typeof brut === 'string' ? Number(brut) : brut
  if (typeof n !== 'number' || !Number.isFinite(n)) return null
  const entier = Math.round(n)
  return entier >= min && entier <= max ? entier : null
}

/**
 * Les heures creuses telles que la fiche Maison les garde : une liste de 0, 1 ou 2 plages.
 * L'écran, lui, en montre toujours deux — la seconde peut rester vide. Une forme
 * inattendue est ignorée plutôt que devinée : la fiche peut avoir été remplie ailleurs.
 */
function plagesDeLaFiche(brut: unknown): [Plage, Plage] | null {
  if (!Array.isArray(brut)) return null
  const lues = brut
    .filter((p): p is { debut: string; fin: string } =>
      typeof p?.debut === 'string' && typeof p?.fin === 'string')
    .slice(0, 2)
  if (lues.length === 0) return null
  return [lues[0], lues[1] ?? { debut: '', fin: '' }]
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
  /**
   * Panneau de réglages replié sur son rail d'icônes, pour donner la largeur à la scène.
   *
   * Entre 1024 et 1280 px, il DÉMARRE replié : à cette largeur, les trois colonnes dépliées
   * laissent moins de 600 px à la scène, et c'est elle qu'on vient voir. Au-delà, elles
   * tiennent toutes et le panneau s'ouvre comme avant.
   *
   * Lu une seule fois, à l'ouverture : c'est un point de départ, pas une règle qui reprendrait
   * la main sur l'utilisateur à chaque changement de taille de fenêtre.
   */
  const [reglagesReplies, setReglagesReplies] = useState(() => window.innerWidth < 1280)
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

  /* --- Le contrat d'électricité, et le puits canadien ---
     Même raison que le jardin, en plus impérieuse : le schéma de l'API est en
     `extra="forbid"`, donc un champ de plus dans `config` ferait échouer CHAQUE calcul en
     422 et laisserait l'écran plein de tirets. Ces deux-là vivent donc à côté, ne partent
     jamais au moteur et n'entrent pas dans l'URL de partage. Ils ne changent aucun chiffre
     du panneau de droite : c'est du recueil, pas du calcul. */
  const [contrat, setContrat] = useState<Contrat>(CONTRAT_INITIAL)
  const [puitsCanadien, setPuitsCanadien] = useState(false)

  const majContrat = useCallback(
    (maj: Partial<Contrat>) => setContrat((c) => ({ ...c, ...maj })), [])

  /* Pour amener les réglages sous les yeux quand on choisit un onglet dans la barre du bas. */
  const panneauReglages = useRef<HTMLDivElement>(null)
  /* Le bloc « Votre raccordement », que la vignette sous la scène doit pouvoir déplier. */
  const blocRaccordement = useRef<HTMLDetailsElement>(null)

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
        /* Le contrat vient de la fiche quand elle le porte, et garde ses défauts sinon —
           les colonnes sont récentes, une fiche ancienne n'a rien à y mettre. */
        const fournisseur = fournisseurDepuisLibelle(fiche.fournisseur_actuel)
        setContrat((c) => ({
          ...c,
          option_tarifaire: OPTIONS_TARIFAIRES
            .find((o) => o.value === fiche.option_tarifaire)?.value ?? c.option_tarifaire,
          heures_creuses: plagesDeLaFiche(fiche.heures_creuses) ?? c.heures_creuses,
          fournisseur: fournisseur?.code ?? c.fournisseur,
          fournisseur_autre: fournisseur?.autre ?? c.fournisseur_autre,
          tarif_bloque: fiche.tarif_bloque ?? c.tarif_bloque,
          tarif_bloque_mois: fiche.tarif_bloque_mois_restants ?? c.tarif_bloque_mois,
        }))
        setConfig((c) => ({
          ...c,
          adresse: c.adresse ?? fiche.code_postal ?? null,
          maison: {
            ...c.maison,
            surface_m2: nombreAdmis(fiche.surface_habitable, 10, 2000, c.maison.surface_m2),
            nb_occupants: nombreAdmis(fiche.nb_occupants, 1, 20, c.maison.nb_occupants),
            chauffage: valeurAdmise(fiche.chauffage_principal, CHAUFFAGES, c.maison.chauffage),
            ecs: valeurAdmise(fiche.ecs, ECS_OPTIONS, c.maison.ecs),
            conso_connue_kwh_an: nombreAdmisOuVide(fiche.conso_elec_kwh_an, 100, 100000),
            puissance_souscrite_kva: nombreAdmis(
              fiche.puissance_souscrite, 3, 36, c.maison.puissance_souscrite_kva),
            residence_secondaire: fiche.residence_principale === false,
            clim: { ...c.maison.clim, present: fiche.clim ?? c.maison.clim.present },
          },
          panneaux: {
            ...c.panneaux,
            orientation: valeurAdmise(fiche.orientation_toiture, ORIENTATIONS, c.panneaux.orientation),
            inclinaison: nombreAdmis(fiche.pente, 0, 90, c.panneaux.inclinaison),
            ombrage: valeurAdmise(fiche.ombrage, OMBRAGES, c.panneaux.ombrage),
            surface_toit_m2: nombreAdmisOuVide(fiche.surface_toit_exploitable, 0, 2000),
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

  /* --- Ce que la scène doit montrer ---
     L'ordre est celui d'`EQUIPEMENTS`. Les emplacements marqués `horsMoteur` ne passent pas
     par `estInstalle()` : leur état vit ici, à côté de la configuration. */
  const equipements: EmplacementScene[] = useMemo(
    () => EQUIPEMENTS.map((e) => {
      const commun = { id: e.id, label: e.label, court: e.court }
      switch (e.id) {
        case 'jardin':
          return {
            ...commun,
            installe: jardinOuvert,
            resume: jardinResultat
              ? `${jardinResultat.surface_totale_m2} m² · ${jardinResultat.couverture_pct} % de vos légumes`
              : null,
          }
        case 'puits_canadien':
          return { ...commun, installe: puitsCanadien, resume: puitsCanadien ? 'Prévu' : null }
        case 'energie':
          return {
            ...commun,
            installe: contrat.fournisseur !== null,
            resume: libelleFournisseur(contrat.fournisseur, contrat.fournisseur_autre),
          }
        case 'reseau': {
          /* L'option tarifaire complète le résumé : elle ne vient pas du moteur, donc
             `resumeDe()` ne peut pas la connaître. */
          const option = OPTIONS_TARIFAIRES.find((o) => o.value === contrat.option_tarifaire)
          const base = resumeDe(e.id, config, resultat)
          return {
            ...commun,
            installe: true,
            resume: base && option ? `${base} · ${option.label}` : base,
          }
        }
        default:
          return {
            ...commun,
            installe: estInstalle(e.id, config),
            resume: resumeDe(e.id, config, resultat),
          }
      }
    }),
    [config, resultat, jardinOuvert, jardinResultat, puitsCanadien, contrat],
  )

  /**
   * Ce qui se passe quand on clique un repère sur l'image ou sa vignette en dessous.
   *
   * Deux emplacements ne sont pas des équipements et n'ouvrent donc pas de feuille de
   * réglage : le raccordement et l'achat d'énergie emmènent vers le menu de gauche, là où
   * leurs champs vivent vraiment. Les autres ouvrent leur feuille, comme avant.
   */
  const onEmplacement = useCallback((id: string) => {
    if (id === 'reseau' || id === 'energie') {
      setReglagesReplies(false)
      setOnglet(id === 'reseau' ? 'maison' : 'energie')
      /* Après le rendu, et pas avant : sur un panneau replié ou un autre onglet, le bloc
         n'existe pas encore dans le document au moment du clic. */
      requestAnimationFrame(() => {
        /* Sur petit écran les réglages vivent SOUS la scène : il faut descendre la page
           jusqu'à eux. Dès `md` ils sont à gauche, déjà sous les yeux, et faire défiler la
           page n'aurait qu'un effet : chasser l'en-tête du site hors de l'écran. */
        if (window.innerWidth < 768) {
          panneauReglages.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
        if (id !== 'reseau') return
        const bloc = blocRaccordement.current
        if (!bloc) return
        bloc.open = true
        /* Le panneau a son propre ascenseur : sans ce `block: 'nearest'`, le bloc s'ouvre
           tout en bas de la liste des réglages et reste invisible, alors qu'on vient
           justement de cliquer pour le voir. */
        bloc.scrollIntoView({ block: 'nearest' })
        bloc.querySelector<HTMLElement>('select, input')?.focus({ preventScroll: true })
      })
      return
    }
    if (id === 'jardin') setJardinOuvert(true)
    setEmplacementOuvert(id)
  }, [])

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

  /**
   * Le contrat rejoint la FICHE MAISON, pas l'étude.
   *
   * L'étude part dans `SimulateurIn`, qui est en `extra="forbid"` : y glisser ces champs
   * ferait échouer l'enregistrement en entier. La fiche, elle, porte déjà l'option
   * tarifaire ; les heures creuses, le fournisseur et le tarif bloqué l'ont rejointe
   * (migration 0021). C'est aussi le bon endroit : ces réponses servent l'espace client et
   * une éventuelle étude de courtage, pas un calcul de production.
   *
   * Au pire, ça échoue en silence : l'étude, elle, doit s'enregistrer quand même.
   */
  const enregistrerContrat = async () => {
    try {
      await authFetch('/api/houses/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          versFicheMaison(contrat, libelleFournisseur(contrat.fournisseur, contrat.fournisseur_autre))),
      })
    } catch {
      /* la fiche est facultative : on ne fait pas échouer l'enregistrement de l'étude */
    }
  }

  const enregistrerEtude = async () => {
    setMessageEtude(null)
    void enregistrerContrat()
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
        <OngletMaison config={config} resultat={resultat} majConfig={majConfig}
          contrat={contrat} majContrat={majContrat} refRaccordement={blocRaccordement} />
      )}
      {onglet === 'energie' && (
        <OngletEnergie contrat={contrat} majContrat={majContrat} connecte={user !== null} />
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

      <div className="mx-auto max-w-[110rem] px-3 pb-4 pt-3 sm:px-4 md:pb-10">
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

        {/* Les alertes du moteur restent AU-DESSUS de la scène — c'est là qu'on les lit, et
            la charte ne permet pas de ranger plus bas un avertissement qui change la lecture
            des chiffres (« le calcul suppose du monophasé »). Elles sont en revanche
            resserrées sur grand écran : à `p-4`, une seule alerte prenait 40 px de plus que
            nécessaire, pris directement sur la hauteur de l'illustration. */}
        {resultat?.alertes.map((alerte) => (
          <div key={alerte.texte}
            className={`mb-2 rounded-xl border p-3 text-sm text-ink md:py-2 ${alerte.niveau === 'attention'
              ? 'border-terra/40 bg-terra/10' : 'border-sky/40 bg-sky/10'}`}>
            <p className="flex items-start gap-2.5">
              {alerte.niveau === 'attention'
                ? <AlertTriangle size={17} className="mt-0.5 shrink-0 text-terra" />
                : <Info size={17} className="mt-0.5 shrink-0 text-sky" />}
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
        {/* Replié, il ne reste que le rail. À partir de `xl`, cela rend ~17 rem à la scène,
            puisque le panneau y occupe une vraie colonne. En dessous, la colonne vaut déjà
            4,75 rem quoi qu'il arrive — le panneau s'ouvre en calque par-dessus la scène —
            et le repli ne fait que découvrir l'illustration. Sous `md`, les réglages
            s'empilent sous la scène et les onglets vivent dans la barre du bas. */}
        <div className={`grid items-start gap-3 2xl:gap-4 md:grid-cols-[4.75rem_minmax(0,1fr)_11rem]
          ${reglagesReplies
            ? '2xl:grid-cols-[4.75rem_minmax(0,1fr)_12rem]'
            : 'xl:grid-cols-[22rem_minmax(0,1fr)_11rem] 2xl:grid-cols-[24rem_minmax(0,1fr)_12rem]'}`}>

          {/* ---------- LES RÉGLAGES, flottants à gauche ---------- */}
          <aside ref={panneauReglages}
            /* `md:z-20` N'EST PAS DÉCORATIF : dans une grille, l'ordre de peinture suit
               l'ordre MODIFIÉ PAR `order`, et les réglages portent `md:order-1` contre
               `md:order-2` pour la scène. Sans profondeur explicite, l'illustration se
               peint donc PAR-DESSUS le calque des réglages, qui disparaît à moitié. Resté
               sous le `z-50` de l'en-tête du site et sous le `z-40` du calque d'accueil. */
            className="relative order-2 min-w-0 scroll-mt-36 md:sticky md:top-20 md:z-20
              md:order-1 md:self-start md:scroll-mt-0 xl:overflow-hidden xl:rounded-2xl
              xl:border xl:border-ink/10 xl:bg-cream/80 xl:shadow-question xl:backdrop-blur">
            <div className="md:flex">
              {/* Le rail : les onglets en icônes, à demeure le long du panneau.
                  Sous `xl` il porte sa propre bordure, puisqu'il n'est plus dans la même
                  boîte que le panneau. */}
              <div role="tablist" aria-orientation="vertical" aria-label="Sections du simulateur"
                className="hidden shrink-0 flex-col gap-1 rounded-2xl border border-ink/10
                  bg-cream/80 p-1.5 shadow-question backdrop-blur md:flex xl:rounded-none
                  xl:border-0 xl:border-r xl:bg-transparent xl:shadow-none xl:backdrop-blur-none">
                {ONGLETS.map(({ id, label, Icone }) => (
                  <button key={id} role="tab" type="button"
                    aria-selected={!reglagesReplies && onglet === id}
                    aria-controls="panneau-reglages"
                    /* Replié, le rail sert de raccourci : choisir un onglet le déplie,
                       sinon le clic n'aurait aucun effet visible. */
                    onClick={() => { setOnglet(id); setReglagesReplies(false) }}
                    className={`flex w-[3.75rem] flex-col items-center gap-1 rounded-xl px-1 py-2
                      text-[10px] font-semibold leading-none transition
                      ${!reglagesReplies && onglet === id
                        ? 'bg-primary text-white shadow' : 'text-ink hover:bg-white'}`}>
                    <Icone size={20} strokeWidth={onglet === id ? 2.4 : 2} aria-hidden="true" />
                    <span className="w-full truncate text-center">{label}</span>
                  </button>
                ))}

                <button type="button" onClick={() => setReglagesReplies((r) => !r)}
                  aria-expanded={!reglagesReplies} aria-controls="panneau-reglages"
                  title={reglagesReplies ? 'Déplier les réglages' : 'Replier les réglages'}
                  className="mt-1 flex w-[3.75rem] flex-col items-center gap-1 rounded-xl border-t
                    border-ink/10 px-1 pb-2 pt-3 text-[10px] font-semibold leading-none text-ink
                    transition hover:bg-white hover:text-primary">
                  {reglagesReplies
                    ? <PanelLeftOpen size={20} strokeWidth={2} aria-hidden="true" />
                    : <PanelLeftClose size={20} strokeWidth={2} aria-hidden="true" />}
                  <span className="w-full truncate text-center">
                    {reglagesReplies ? 'Déplier' : 'Replier'}
                  </span>
                </button>
              </div>

              <div id="panneau-reglages" role="tabpanel" aria-label={ongletActif?.label}
                className={`min-w-0 flex-1
                  md:absolute md:left-[5.25rem] md:top-0 md:z-30 md:w-[22rem]
                  md:max-h-[calc(100dvh-7rem)] md:overflow-y-auto md:rounded-2xl md:border
                  md:border-ink/10 md:bg-cream/95 md:p-2 md:shadow-question md:backdrop-blur
                  xl:static xl:z-auto xl:w-auto xl:max-h-[calc(100vh-7rem)] xl:rounded-none
                  xl:border-0 xl:bg-transparent xl:shadow-none
                  ${reglagesReplies ? 'md:hidden' : ''}`}>
                {/* Le titre rend le rail lisible : une icône allumée ne dit pas son nom. */}
                <h2 className="hidden px-2 py-1 font-display text-lg font-bold text-ink md:block">
                  {ongletActif?.label}
                </h2>
                {contenuOnglet}
              </div>
            </div>
          </aside>

          {/* ---------- LA SCÈNE, au centre et en grand ----------
              La scène et sa rangée de vignettes doivent tenir sous l'en-tête SANS que la
              page défile. L'illustration étant en 21:9, c'est presque toujours la largeur
              de la colonne qui commande — mais sur un écran bas (1280 × 720, ou un zoom
              navigateur à 125 %), c'est la hauteur. D'où une largeur maximale DÉDUITE DE LA
              HAUTEUR DISPONIBLE : la scène rétrécit alors et reste centrée, au lieu de
              pousser les vignettes hors de l'écran.

              Les 13rem retranchés : l'en-tête du site (5rem, le même décalage que le
              `md:top-20` des deux cartes flottantes), les marges de la page, et la place
              des deux rangées de vignettes.

              En dessous de `md`, aucune contrainte : sur un téléphone le défilement est
              normal, et brider la largeur ne ferait que rapetisser l'image. */}
          <div className="order-1 min-w-0 md:order-2">
            {premierChargement && localise ? (
              <div className="mx-auto w-full animate-pulse md:max-w-[calc((100dvh-13rem)*1584/672)]">
                <div className="aspect-[1584/672] w-full rounded-xl bg-white/70" />
                <div className="mx-auto mt-3 h-4 w-2/3 rounded bg-white/70" />
              </div>
            ) : (
              <div className="mx-auto w-full md:max-w-[calc((100dvh-13rem)*1584/672)]">
                <SceneMaison equipements={equipements} eolienne={config.eolien.kwc > 0}
                  heure={heure} saison={saison} flux={flux} onEmplacement={onEmplacement} />
              </div>
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
          <div className="order-3 hidden md:sticky md:top-20 md:block md:self-start">
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
                  border border-ink px-4 py-2 font-semibold text-ink hover:bg-ink hover:text-sable
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
          pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
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
            bg-ink/50 px-4 py-8 backdrop-blur-[3px]">
          <div className="animate-slide-up w-full max-w-2xl rounded-2xl border border-bord
            bg-white p-6 shadow-question sm:p-8">
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
                  hover:bg-terra">
                <span className="block font-display text-lg">Me laisser guider</span>
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
        ) : emplacementOuvert === 'puits_canadien' ? (
          /* Un puits canadien tempère l'air neuf avant qu'il n'entre : frais l'été, préchauffé
             l'hiver. Il ne produit pas d'électricité et n'entre dans aucun bilan du moteur
             horaire — l'écran le DIT, plutôt que de laisser croire à un effet sur les
             chiffres de droite. Lui en inventer un demanderait d'abord une entrée au moteur. */
          <div className="space-y-3">
            <p className="text-dark/80">
              Un conduit enterré fait passer l’air neuf par le sol avant qu’il n’entre dans la
              maison : rafraîchi l’été, préchauffé l’hiver, sans rien consommer de plus que
              le ventilateur de la ventilation.
            </p>
            <Bascule label="J’ai (ou je veux) un puits canadien" actif={puitsCanadien}
              onChange={setPuitsCanadien} />
            <p className="text-sm text-dark/60">
              Il apparaît dans votre maison, mais ne change aucun chiffre de cette page : son
              effet porte sur le confort et sur le chauffage, que ce simulateur ne modélise
              pas. Nous préférons le dire plutôt que d’afficher un gain inventé.
            </p>
            <Link to="/la-terre?sujet=puits-canadien"
              className="inline-flex items-center gap-1.5 font-semibold text-primary
                hover:gap-2.5 transition-all">
              Comment ça marche <ArrowRight size={16} />
            </Link>
          </div>
        ) : emplacementOuvert && (
          <ReglageEquipement id={emplacementOuvert} config={config} resultat={resultat}
            majConfig={majConfig} />
        )}
      </Feuille>
    </div>
  )
}
