/**
 * Les cinq onglets du simulateur, plus l'aide.
 *
 * Aucun chiffre n'est calculé ici : tout vient de `resultat`, produit par le moteur
 * déterministe. Un libellé dit exactement ce qu'il montre — « journée moyenne de
 * printemps » et jamais « sur l'année » pour un cumul de journées.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, Pause, Play } from 'lucide-react'

import {
  ans, chercherAdresses, CHAUFFAGES, ECS_OPTIONS, euros, kwh, OMBRAGES, ORIENTATIONS,
  PRESENCES, SAISONS,
  type Config, type Objectif, type Option, type Options, type Resultat, type Saison,
} from '../../lib/simulateur'
import { Anneau, BarresMensuelles, Courbe25Ans, CourbeJournee, Repartition, Vide } from './Graphiques'
import { Bascule, Champ, Choix, DejaLa, Nombre } from './Reglage'

type MajConfig = (maj: (c: Config) => Config) => void

interface OngletProps {
  config: Config
  resultat: Resultat | null
  majConfig: MajConfig
}

/**
 * Un bloc de réglages, repliable.
 *
 * `<details>` natif plutôt qu'un état React : le clavier, le lecteur d'écran et la recherche
 * dans la page fonctionnent sans qu'on ait à les recoder, et l'ouverture reste fluide.
 *
 * Replié par défaut, SAUF le premier bloc de chaque onglet (`ouvert`) : arriver sur une
 * colonne entièrement fermée ne donne rien à faire. Ce qui est gagné en hauteur ici revient
 * à la scène, qui est ce qu'on veut mettre en avant.
 */
function Bloc({
  titre, children, aide, ouvert = false,
}: { titre: string; children: React.ReactNode; aide?: string; ouvert?: boolean }) {
  return (
    <details open={ouvert} className="group rounded-xl border border-ink/10 bg-white">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-xl
        px-4 py-3 hover:bg-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50">
        <h3 className="font-display text-lg font-bold text-ink">{titre}</h3>
        <ChevronDown size={20}
          className="shrink-0 text-primary transition-transform group-open:rotate-180" />
      </summary>
      <div className="px-4 pb-4">
        {aide && <p className="-mt-1 mb-3 text-sm text-dark/70">{aide}</p>}
        <div className="space-y-4">{children}</div>
      </div>
    </details>
  )
}

function Ligne({ label, valeur }: { label: string; valeur: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-ink/5 py-1.5 last:border-0">
      <span className="text-dark/80">{label}</span>
      <span className="text-right font-semibold text-ink">{valeur}</span>
    </div>
  )
}

/* ------------------------------------------------------------------ Maison */

function ChampAdresse({ config, majConfig }: { config: Config; majConfig: MajConfig }) {
  const [texte, setTexte] = useState(config.adresse ?? '')
  const [suggestions, setSuggestions] = useState<Awaited<ReturnType<typeof chercherAdresses>>>([])
  const [ouvert, setOuvert] = useState(false)

  useEffect(() => {
    if (!ouvert || texte.trim().length < 3) { setSuggestions([]); return }
    const controleur = new AbortController()
    const minuteur = setTimeout(() => {
      chercherAdresses(texte, controleur.signal).then(setSuggestions).catch(() => { /* annulé */ })
    }, 250)
    return () => { clearTimeout(minuteur); controleur.abort() }
  }, [texte, ouvert])

  return (
    <div className="relative">
      <label htmlFor="adresse" className="block font-semibold text-ink">Adresse</label>
      <input id="adresse" type="text" autoComplete="off" value={texte}
        placeholder="12 rue des Lilas, Marseille"
        onChange={(e) => { setTexte(e.target.value); setOuvert(true) }}
        className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2 text-ink
          focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
      <p className="mt-1 text-sm text-dark/60">
        Elle sert à récupérer l’ensoleillement réel de votre commune. Elle n’est jamais
        enregistrée ni mise dans le lien de partage — seule la commune l’est.
      </p>
      {ouvert && suggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-ink/20 bg-white shadow-lg">
          {suggestions.map((s) => (
            <li key={s.label}>
              <button type="button"
                onClick={() => {
                  setTexte(s.label); setOuvert(false); setSuggestions([])
                  majConfig((c) => ({ ...c, adresse: s.label, lat: s.lat, lon: s.lon }))
                }}
                className="block w-full px-3 py-2 text-left hover:bg-cream">
                {s.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function OngletMaison({ config, resultat, majConfig }: OngletProps) {
  const m = config.maison
  const majMaison = (maj: Partial<Config['maison']>) =>
    majConfig((c) => ({ ...c, maison: { ...c.maison, ...maj } }))

  return (
    <div className="space-y-4">
      <Bloc titre="Où ?" ouvert>
        <ChampAdresse config={config} majConfig={majConfig} />
      </Bloc>

      <Bloc titre="Votre logement">
        <Champ label="Surface habitable" valeur={m.surface_m2} suffixe="m²"
          onChange={(v) => majMaison({ surface_m2: v ?? 100 })} />
        <Nombre label="Occupants" valeur={m.nb_occupants} min={1} max={20}
          onChange={(v) => majMaison({ nb_occupants: v })} />
        <Champ label="Consommation annuelle d’électricité" valeur={m.conso_connue_kwh_an}
          suffixe="kWh" placeholder="je ne sais pas"
          aide={resultat?.consommation.estimee
            ? `Laissée vide : nous l’estimons à ${kwh(resultat.consommation.annuel_kwh)} par an. C’est une estimation.`
            : 'Reprise de votre facture : la courbe est recalée dessus.'}
          onChange={(v) => majMaison({ conso_connue_kwh_an: v })} />
        <Choix label="Présence en journée" valeur={m.presence_journee} options={PRESENCES}
          onChange={(v) => majMaison({ presence_journee: v })}
          aide="Consommer pendant que le soleil brille change tout." />
        <Bascule label="Résidence secondaire" actif={m.residence_secondaire}
          onChange={(v) => majMaison({ residence_secondaire: v })}
          aide="Hors des mois d’occupation, seule la veille consomme." />
        {m.residence_secondaire && (
          <div>
            <span className="block font-semibold text-ink">Mois d’occupation</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'].map((lettre, i) => {
                const mois = i + 1
                const actif = m.mois_occupation.includes(mois)
                return (
                  <button key={i} type="button" aria-pressed={actif}
                    aria-label={`Mois ${mois}`}
                    onClick={() => majMaison({
                      mois_occupation: actif
                        ? m.mois_occupation.filter((x) => x !== mois)
                        : [...m.mois_occupation, mois].sort((a, b) => a - b),
                    })}
                    className={`h-9 w-9 rounded-lg border text-sm font-bold transition
                      ${actif ? 'border-primary bg-primary text-white' : 'border-ink/20 text-ink'}`}>
                    {lettre}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </Bloc>

      <Bloc titre="Chauffage et eau chaude">
        <Choix label="Chauffage" valeur={m.chauffage} options={CHAUFFAGES}
          onChange={(v) => majMaison({ chauffage: v })}
          aide="Seul un chauffage électrique pèse sur votre facture d’électricité." />
        <Choix label="Eau chaude" valeur={m.ecs} options={ECS_OPTIONS}
          onChange={(v) => majMaison({ ecs: v })} />
      </Bloc>

      <Bloc titre="Votre raccordement">
        <Choix label="Type de raccordement" valeur={m.raccordement}
          options={[
            { value: 'monophase', label: 'Monophasé' },
            { value: 'triphase', label: 'Triphasé' },
            { value: 'inconnu', label: 'Je ne sais pas' },
          ]}
          onChange={(v) => majMaison({ raccordement: v })}
          aide="En monophasé, on ne peut injecter que 6 kVA : au-delà, l’énergie est perdue." />
        <Champ label="Puissance souscrite" valeur={m.puissance_souscrite_kva} suffixe="kVA"
          onChange={(v) => majMaison({ puissance_souscrite_kva: v ?? 9 })}
          aide="Indiquée sur votre facture. Elle fixe le prix du kWh et l’abonnement." />
        <Bascule label="Je veux tenir en cas de coupure" actif={m.besoin_secours}
          onChange={(v) => majMaison({ besoin_secours: v })}
          aide="Seule une batterie physique le permet. Nous vous le dirons franchement, sans arranger sa rentabilité." />
      </Bloc>
    </div>
  )
}

/* --------------------------------------------------------------- Panneaux */

export function OngletPanneaux({ config, resultat, majConfig }: OngletProps) {
  const p = config.panneaux
  const majPanneaux = (maj: Partial<Config['panneaux']>) =>
    majConfig((c) => ({ ...c, panneaux: { ...c.panneaux, ...maj } }))
  const maxToit = resultat?.panneaux_max_toit ?? null

  return (
    <div className="space-y-4">
      <Bloc titre="Sur le toit" ouvert>
        <Nombre label="Panneaux" valeur={p.nb_panneaux} min={0} max={40}
          onChange={(v) => majPanneaux({ nb_panneaux: v })}
          aide={resultat ? `${resultat.production.kwc_toit} kWc en toiture` : undefined} />
        <Champ label="Surface de toit exploitable" valeur={p.surface_toit_m2} suffixe="m²"
          placeholder="je ne sais pas"
          onChange={(v) => majPanneaux({ surface_toit_m2: v })} />
        {maxToit !== null && maxToit > 0 && (
          <button type="button" onClick={() => majPanneaux({ nb_panneaux: Math.min(maxToit, 40) })}
            className="w-full rounded-lg border border-primary px-3 py-2 font-semibold text-primary
              hover:bg-primary hover:text-white">
            Remplir le toit ({Math.min(maxToit, 40)} panneaux)
          </button>
        )}
        <Choix label="Orientation" valeur={p.orientation} options={ORIENTATIONS}
          onChange={(v) => majPanneaux({ orientation: v })} />
        <Nombre label="Inclinaison" valeur={p.inclinaison} min={0} max={90} pas={5} suffixe="°"
          onChange={(v) => majPanneaux({ inclinaison: v })} />
        <Choix label="Ombrage" valeur={p.ombrage} options={OMBRAGES}
          onChange={(v) => majPanneaux({ ombrage: v })} />
      </Bloc>

      <Bloc titre="Carport"
        aide="Une structure couverte de panneaux, plein sud et peu inclinée. Sa structure a un coût à part.">
        <Nombre label="Panneaux sur le carport" valeur={p.nb_panneaux_carport} min={0} max={40}
          onChange={(v) => majPanneaux({ nb_panneaux_carport: v })}
          aide={resultat && resultat.production.kwc_carport > 0
            ? `${resultat.production.kwc_carport} kWc sur le carport` : undefined} />
      </Bloc>

      <Bloc titre="Ce que vous produisez">
        {!resultat || resultat.production.annuel_kwh <= 0 ? (
          <Vide message="Ajoutez des panneaux pour voir votre production mois par mois." />
        ) : (
          <>
            <BarresMensuelles series={[
              { nom: 'Production', couleur: '#F5B700', valeurs: resultat.bilan_mensuel.map((m) => m.production) },
              { nom: 'Consommation', couleur: '#2E86C1', valeurs: resultat.bilan_mensuel.map((m) => m.consommation) },
            ]} />
            <div className="pt-2">
              <Ligne label="Production sur l’année" valeur={kwh(resultat.production.annuel_kwh)} />
              <Ligne label="Par kWc installé" valeur={`${kwh(resultat.production.par_kwc_kwh)} / an`} />
              <Ligne label="Pertes prises en compte" valeur={`${resultat.production.pertes_pct} %`} />
              <Ligne label="Production valorisée"
                valeur={`${resultat.indicateurs.production_valorisee_pct} %`} />
            </div>
            {/* L'écrêtage se dit EN PETIT tant qu'il ne pèse rien. Il a longtemps déclenché
                un bandeau rouge, y compris quand rien n'était écrêté du tout : un 9 kWc
                plein sud culmine vers 7,8 kW à midi en juin, dont le talon de la maison et
                les usages du moment mangent une bonne part — il ne sort quasiment jamais
                plus de 6 kVA. Au-delà du seuil, c'est l'alerte en haut de page qui parle,
                et cette ligne se tait pour ne pas dire deux fois la même chose. */}
            {resultat.production.ecrete_kwh > 0
              && (100 * resultat.production.ecrete_kwh / resultat.production.annuel_kwh)
                 < resultat.production.ecrete_seuil_pct && (
              <p className="pt-2 text-xs text-dark/60">
                Aux heures de plus forte production, une petite part ne peut pas sortir sur
                le réseau — {kwh(resultat.production.ecrete_kwh)} sur l’année, soit{' '}
                {(100 * resultat.production.ecrete_kwh / resultat.production.annuel_kwh)
                  .toFixed(1).replace('.', ',')} %
                de votre production. C’est négligeable à ce niveau.
              </p>
            )}
          </>
        )}
      </Bloc>
    </div>
  )
}

/* --------------------------------------------------------------- Stockage */

export function OngletStockage({ config, resultat, majConfig }: OngletProps) {
  const s = config.stockage
  const majStockage = (maj: Partial<Config['stockage']>) =>
    majConfig((c) => ({ ...c, stockage: { ...c.stockage, ...maj } }))
  const virtuelle = resultat?.stockage.batterie_virtuelle ?? null

  return (
    <div className="space-y-4">
      <Bloc titre="Pilotage des usages" ouvert
        aide="Décaler le ballon, la filtration et la recharge vers les heures de soleil. Cela ne coûte presque rien.">
        <Bascule label="Piloter mes usages" actif={s.pilotage}
          onChange={(v) => majStockage({ pilotage: v })} />
        {resultat && (
          <p className="text-sm text-dark/70">
            {resultat.stockage.pilotage.actif
              ? `${resultat.stockage.pilotage.nb_usages} usage(s) piloté(s).`
              : 'Aucun usage piloté pour l’instant.'}
          </p>
        )}
      </Bloc>

      <Bloc titre="Batterie physique"
        aide="Attention : ajouter une batterie fait passer TOUT le projet de 5,5 % à 20 % de TVA.">
        <Nombre label="Packs" valeur={s.nb_packs} min={0} max={6}
          onChange={(v) => majStockage({ nb_packs: v })}
          aide={resultat && resultat.stockage.batterie_physique.capacite_kwh > 0
            ? `${resultat.stockage.batterie_physique.capacite_kwh} kWh utiles`
            : undefined} />
        {!resultat || resultat.stockage.batterie_physique.nb_packs === 0 ? (
          <Vide message="Pas de batterie physique : rien à afficher ici pour l’instant." />
        ) : (
          <div>
            <Ligne label="Stocké dans l’année" valeur={kwh(resultat.stockage.batterie_physique.charge_kwh)} />
            <Ligne label="Restitué à la maison" valeur={kwh(resultat.stockage.batterie_physique.restitue_kwh)} />
          </div>
        )}
      </Bloc>

      <Bloc titre="Stockage par inertie"
        aide="Une batterie enterrée, sans lithium, garantie 40 ans. Une seule unité — ce n’est pas un pack qu’on empile.">
        <Bascule label="J’enterre un stockage par inertie" actif={s.inertie}
          onChange={(v) => majStockage({ inertie: v })}
          aide={resultat
            ? `${resultat.stockage.inertie.capacite_kwh || 10} kWh, jusqu’à ${resultat.stockage.inertie.puissance_kw || 6} kW en sortie`
            : '10 kWh, jusqu’à 6 kW en sortie'} />
        {resultat?.stockage.inertie.presente && (
          <div>
            <Ligne label="Capacité" valeur={kwh(resultat.stockage.inertie.capacite_kwh)} />
            <Ligne label="Puissance de sortie" valeur={`${resultat.stockage.inertie.puissance_kw} kW`} />
            <Ligne label="Garantie" valeur={`${resultat.stockage.inertie.garantie_ans} ans`} />
            <Ligne label="Investissement"
              valeur={euros(resultat.investissement.inertie_eur)} />
            {/* Le point qui explique tout l'écart de prix avec le lithium. */}
            <p className="pt-2 text-xs text-dark/60">
              Garantie plus longue que l’étude : aucun remplacement n’est compté sur
              25 ans, là où un pack lithium se change une fois en cours de route.
            </p>
          </div>
        )}
      </Bloc>

      <Bloc titre="Batterie virtuelle"
        aide="Votre surplus est mis de côté chez un fournisseur au lieu d’être vendu. Cela impose de changer de fournisseur d’électricité.">
        {/* Le sur-mesure en premier : c'est celui qu'on conseille, et l'ordre d'une liste
            se lit comme un classement. Noms commerciaux de MyLight — ce sont ceux que
            l'utilisateur retrouvera sur leur site. */}
        <Choix label="Offre" valeur={s.batterie_virtuelle ?? 'aucune'}
          options={[
            { value: 'aucune', label: 'Aucune' },
            { value: 'mysmartbattery', label: 'MyLight — Stockage sur-mesure' },
            { value: 'mybattery', label: 'MyLight — Stockage illimité' },
          ]}
          onChange={(v) => majStockage({ batterie_virtuelle: v === 'aucune' ? null : v })} />
        {!virtuelle ? (
          <Vide message="Pas de batterie virtuelle : rien à afficher ici pour l’instant." />
        ) : (
          <>
            {/* La note DÉCRIT l'offre : elle s'affiche toujours. Elle ne passe en rouge que
                si la grille est incomplète, auquel cas elle porte un avertissement. */}
            <p className={`rounded-lg border px-3 py-2 text-sm text-ink ${virtuelle.grille_complete
              ? 'border-sky/40 bg-sky/10' : 'border-terra/40 bg-terra/10'}`}>
              {virtuelle.note}
            </p>
            {/* Le conseil se distingue du fait : encadré aux couleurs de la marque, et
                annoncé comme un avis. Un visiteur doit pouvoir faire la part des deux. */}
            {virtuelle.conseil && (
              <p className="rounded-lg border border-primary/40 bg-primary/5 px-3 py-2 text-sm text-ink">
                <strong>Notre avis — </strong>{virtuelle.conseil}
              </p>
            )}
            <div>
              <Ligne label="Mis de côté dans l’année" valeur={kwh(virtuelle.stocke_kwh)} />
              <Ligne label="Récupéré" valeur={kwh(virtuelle.restitue_kwh)} />
              <Ligne label="Abonnement" valeur={`${euros(virtuelle.abonnement_annuel_eur)} / an`} />
              <Ligne label="Coût de restitution" valeur={`${euros(virtuelle.cout_restitution_annuel_eur)} / an`} />
              {virtuelle.palier_kwh !== null && (
                <>
                  <Ligne label="Réserve louée" valeur={kwh(virtuelle.palier_kwh)} />
                  {/* La pointe explique le palier : sans elle, « réserve louée : 20 kWh »
                      sur 2 000 kWh mis de côté dans l'année a l'air d'une erreur. */}
                  <Ligne label="Réserve détenue au plus haut"
                    valeur={kwh(virtuelle.credit_maxi_kwh)} />
                </>
              )}
              <Ligne label="Fournisseur imposé" valeur={virtuelle.fournisseur_impose ?? '—'} />
            </div>
            {resultat && (
              <BarresMensuelles series={[
                { nom: 'Mis de côté', couleur: '#57A64A', valeurs: resultat.bilan_mensuel.map((m) => m.stocke_virtuel) },
                { nom: 'Récupéré', couleur: '#2E86C1', valeurs: resultat.bilan_mensuel.map((m) => m.restitue_virtuel) },
              ]} />
            )}
          </>
        )}
      </Bloc>
    </div>
  )
}

/* ----------------------------------------------------------- Journée type */

const LIBELLE_SAISON: Record<Saison, string> = {
  printemps: 'journée moyenne de printemps',
  ete: 'journée moyenne d’été',
  automne: 'journée moyenne d’automne',
  hiver: 'journée moyenne d’hiver',
}

export function OngletJournee({
  resultat, saison, setSaison, heure, setHeure,
}: {
  resultat: Resultat | null
  saison: Saison; setSaison: (s: Saison) => void
  heure: number; setHeure: (h: number) => void
}) {
  const [lecture, setLecture] = useState(false)
  const [vitesse, setVitesse] = useState(1)
  const [enchainer, setEnchainer] = useState(false)
  const refHeure = useRef(heure)
  refHeure.current = heure

  useEffect(() => {
    if (!lecture) return
    const minuteur = setInterval(() => {
      const suivante = (refHeure.current + 1) % 24
      setHeure(suivante)
      if (suivante === 0 && enchainer) {
        const ordre: Saison[] = ['printemps', 'ete', 'automne', 'hiver']
        setSaison(ordre[(ordre.indexOf(saison) + 1) % 4])
      }
    }, 700 / vitesse)
    return () => clearInterval(minuteur)
  }, [lecture, vitesse, enchainer, saison, setHeure, setSaison])

  const points = resultat?.journees[saison] ?? null
  const point = points?.[heure] ?? null
  const cumul = useMemo(() => {
    if (!points) return null
    const somme = (cle: keyof (typeof points)[0]) =>
      points.reduce((total, p) => total + (p[cle] as number), 0)
    return {
      production: somme('production'), consommation: somme('consommation'),
      direct: somme('direct'), injecte: somme('injecte'), achat: somme('achat'),
      decharge: somme('decharge'), restitue: somme('restitue_virtuel'),
    }
  }, [points])

  if (!resultat || !points || !point || !cumul) {
    return <Vide message="Renseignez votre adresse pour voir votre journée type." />
  }

  const autonomieJour = cumul.consommation > 0
    ? Math.round(100 * (cumul.direct + cumul.decharge + cumul.restitue) / cumul.consommation)
    : 0

  return (
    <div className="space-y-4">
      <Bloc titre="La journée en direct" ouvert>
        <div className="flex flex-wrap items-center gap-2">
          {SAISONS.map((s) => (
            <button key={s.value} type="button" aria-pressed={saison === s.value}
              onClick={() => setSaison(s.value)}
              className={`rounded-full border px-3 py-1.5 text-sm font-semibold transition
                ${saison === s.value ? 'border-primary bg-primary text-white' : 'border-ink/20 text-ink'}`}>
              {s.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button type="button" onClick={() => setLecture(!lecture)}
            aria-label={lecture ? 'Mettre en pause' : 'Lancer la journée'}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary text-white">
            {lecture ? <Pause size={20} /> : <Play size={20} />}
          </button>
          <input type="range" min={0} max={23} value={heure} aria-label="Heure de la journée"
            onChange={(e) => setHeure(Number(e.target.value))} className="w-full accent-primary" />
          <span className="w-16 shrink-0 text-right font-bold text-ink tabular-nums">
            {String(heure).padStart(2, '0')} h
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {[1, 2, 4].map((v) => (
            <button key={v} type="button" aria-pressed={vitesse === v} onClick={() => setVitesse(v)}
              className={`rounded-full border px-3 py-1 text-sm font-semibold
                ${vitesse === v ? 'border-primary bg-primary text-white' : 'border-ink/20 text-ink'}`}>
              ×{v}
            </button>
          ))}
          <Bascule label="Enchaîner les saisons" actif={enchainer} onChange={setEnchainer} />
        </div>
      </Bloc>

      <Bloc titre={`À ${String(heure).padStart(2, '0')} h`}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm uppercase tracking-wide text-dark/60">Production</p>
            <p className="font-display text-2xl font-bold text-ink">{point.production.toFixed(1)} kW</p>
          </div>
          <div>
            <p className="text-sm uppercase tracking-wide text-dark/60">Consommation</p>
            <p className="font-display text-2xl font-bold text-ink">{point.consommation.toFixed(1)} kW</p>
          </div>
        </div>

        <div>
          <p className="font-semibold text-ink">Le soleil part vers…</p>
          {point.production <= 0.001 ? (
            <p className="mt-1 text-sm text-dark/70">Il fait nuit : rien ne sort des panneaux.</p>
          ) : (
            <Repartition parts={[
              { nom: 'La maison, directement', valeur: point.direct, couleur: '#F5B700' },
              { nom: 'La batterie', valeur: point.charge, couleur: '#57A64A' },
              { nom: 'Mis de côté (virtuelle)', valeur: point.stocke_virtuel, couleur: '#1D3F63' },
              { nom: 'Le réseau', valeur: point.injecte, couleur: '#2E86C1' },
              { nom: 'Perdu (écrêtage)', valeur: point.ecrete, couleur: '#C05621' },
            ]} />
          )}
        </div>

        <div>
          <p className="font-semibold text-ink">La maison est alimentée par…</p>
          <Repartition parts={[
            { nom: 'Le soleil, directement', valeur: point.direct, couleur: '#F5B700' },
            { nom: 'La batterie', valeur: point.decharge, couleur: '#57A64A' },
            { nom: 'La batterie virtuelle', valeur: point.restitue_virtuel, couleur: '#1D3F63' },
            { nom: 'Le réseau', valeur: point.achat, couleur: '#2E86C1' },
          ]} />
        </div>
      </Bloc>

      <Bloc titre={`Cumul sur une ${LIBELLE_SAISON[saison]}`}>
        <CourbeJournee heureActive={heure} series={[
          { nom: 'Production', couleur: '#F5B700', valeurs: points.map((p) => p.production) },
          { nom: 'Consommation', couleur: '#2E86C1', valeurs: points.map((p) => p.consommation) },
        ]} />
        <div className="pt-2">
          <Ligne label="Produit" valeur={`${cumul.production.toFixed(1)} kWh`} />
          <Ligne label="Autoconsommé" valeur={`${cumul.direct.toFixed(1)} kWh`} />
          <Ligne label="Injecté" valeur={`${cumul.injecte.toFixed(1)} kWh`} />
          <Ligne label="Acheté" valeur={`${cumul.achat.toFixed(1)} kWh`} />
          <Ligne label="Autonomie" valeur={`${autonomieJour} %`} />
        </div>
        <p className="text-sm text-dark/60">
          Ces chiffres sont ceux d’une seule {LIBELLE_SAISON[saison]} — pas d’un total annuel.
          Le total de l’année est dans l’onglet Étude.
        </p>
      </Bloc>
    </div>
  )
}

/* ------------------------------------------------------------------ Étude */

function CarteOption({
  option, recommandee, onChoisir,
}: { option: Option; recommandee: boolean; onChoisir: () => void }) {
  return (
    <article className={`rounded-xl border p-4 ${recommandee
      ? 'border-primary bg-primary/5 ring-2 ring-primary/30' : 'border-ink/10 bg-white'}`}>
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-display text-lg font-bold text-ink">{option.label}</h4>
        {recommandee && (
          <span className="shrink-0 rounded-full bg-primary px-2.5 py-0.5 text-xs font-bold text-white">
            Recommandée
          </span>
        )}
      </div>
      <div className="mt-3">
        <Ligne label="Panneaux" valeur={`${option.nb_panneaux} (${option.puissance_kwc} kWc)`} />
        <Ligne label="Investissement" valeur={`${euros(option.investissement_eur)} · TVA ${option.tva_pct} %`} />
        <Ligne label="Autonomie" valeur={`${option.autonomie_pct} %`} />
        <Ligne label="Facture" valeur={`${euros(option.facture_mois_eur)} / mois`} />
        <Ligne label="Économies 1re année" valeur={euros(option.economie_1re_annee_eur)} />
        <Ligne label="Gain net sur 25 ans" valeur={euros(option.gain_net_25_ans_eur)} />
        <Ligne label="Temps de retour" valeur={ans(option.temps_retour_ans)} />
        <Ligne label="Rendement annuel"
          valeur={option.rendement_annuel_pct === null ? '—' : `${option.rendement_annuel_pct} %`} />
      </div>
      {option.note_secours && (
        <p className="mt-3 rounded-lg border border-sky/40 bg-sky/10 px-3 py-2 text-sm text-ink">
          {option.note_secours}
        </p>
      )}
      <button type="button" onClick={onChoisir}
        className="mt-3 w-full rounded-lg bg-ink px-3 py-2 font-semibold text-white hover:bg-ink/90">
        Choisir cette option
      </button>
    </article>
  )
}

function Objectifs({ objectifs }: { objectifs: Objectif[] }) {
  return (
    <ul className="space-y-2">
      {objectifs.map((o) => (
        <li key={o.code} className="flex items-start gap-3">
          <span aria-hidden="true"
            className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-sm font-bold
              ${o.atteint ? 'bg-leaf text-white' : 'bg-ink/10 text-ink/50'}`}>
            {o.atteint ? '✓' : '·'}
          </span>
          <span>
            <span className="block font-semibold text-ink">{o.libelle}</span>
            <span className="block text-sm text-dark/70">
              {o.valeur} — {o.atteint ? 'atteint' : 'pas encore'}
            </span>
          </span>
        </li>
      ))}
    </ul>
  )
}

export function OngletEtude({
  config, resultat, options, chargementOptions, majConfig, onAppliquerOption,
}: OngletProps & {
  options: Options | null
  chargementOptions: boolean
  onAppliquerOption: (o: Option) => void
}) {
  const [hypothesesOuvertes, setHypothesesOuvertes] = useState(false)

  return (
    <div className="space-y-4">
      <Bloc titre="Trois chemins possibles" ouvert
        aide="Chacun est chiffré à sa taille la plus rentable. La recommandation est celle qui rapporte le plus net sur 25 ans.">
        {chargementOptions && !options && <Vide message="Calcul des options en cours…" />}
        {!chargementOptions && !options && <Vide message="Renseignez votre adresse pour voir les options." />}
        {options && (
          <div className="grid gap-4 lg:grid-cols-3">
            {options.options.map((o) => (
              <CarteOption key={o.code} option={o} recommandee={o.code === options.recommandee}
                onChoisir={() => onAppliquerOption(o)} />
            ))}
          </div>
        )}
      </Bloc>

      {resultat && (
        <Bloc titre="Votre configuration actuelle">
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <Ligne label="Investissement" valeur={euros(resultat.investissement.total_eur)} />
              <Ligne label="dont panneaux" valeur={euros(resultat.investissement.panneaux_eur)} />
              {resultat.investissement.carport_eur > 0 && (
                <Ligne label="dont carport" valeur={euros(resultat.investissement.carport_eur)} />
              )}
              {resultat.investissement.batterie_eur > 0 && (
                <Ligne label="dont batterie" valeur={euros(resultat.investissement.batterie_eur)} />
              )}
              <Ligne label="TVA appliquée" valeur={`${resultat.investissement.tva_pct} %`} />
              <p className="pt-2 text-sm text-dark/70">{resultat.investissement.tva_raison}</p>
            </div>
            <div>
              <Ligne label="Facture" valeur={`${euros(resultat.economie.facture_mois_eur)} / mois`} />
              <Ligne label="dont abonnement électrique"
                valeur={`${euros(resultat.economie.abonnement_elec_mois_eur)} / mois`} />
              {resultat.economie.abonnement_virtuel_mois_eur > 0 && (
                <Ligne label="dont abonnement batterie virtuelle"
                  valeur={`${euros(resultat.economie.abonnement_virtuel_mois_eur)} / mois`} />
              )}
              <Ligne label="Sans solaire, ce serait"
                valeur={`${euros(resultat.economie.facture_mois_reference_eur)} / mois`} />
              <Ligne label="Gain net sur 25 ans" valeur={euros(resultat.economie.gain_net_25_ans_eur)} />
              <Ligne label="Temps de retour" valeur={ans(resultat.economie.temps_retour_ans)} />
            </div>
          </div>
        </Bloc>
      )}

      {resultat && (
        <Bloc titre="Votre trésorerie, année après année"
          aide="Ce que le projet vous a coûté, puis rapporté, cumulé depuis le premier jour.">
          <Courbe25Ans tresorerie={resultat.economie.tresorerie} />
          <Choix label="Hausse du prix de l’électricité"
            valeur={String(config.hausse_prix_pct_an ?? 2)}
            options={[
              { value: '2', label: '2 %/an (prudent)' },
              { value: '4', label: '4 %/an' },
              { value: '6', label: '6 %/an' },
            ]}
            onChange={(v) => majConfig((c) => ({ ...c, hausse_prix_pct_an: Number(v) }))}
            aide="Personne ne connaît l’avenir du prix de l’électricité. Essayez les trois." />
        </Bloc>
      )}

      {options && (
        <Bloc titre="Vos objectifs">
          <Objectifs objectifs={options.objectifs} />
        </Bloc>
      )}

      {resultat && (
        <section className="rounded-xl border border-ink/10 bg-white">
          <button type="button" onClick={() => setHypothesesOuvertes(!hypothesesOuvertes)}
            aria-expanded={hypothesesOuvertes}
            className="flex w-full items-center justify-between gap-3 p-4 text-left">
            <span className="font-display text-lg font-bold text-ink">Hypothèses et méthode</span>
            <ChevronDown size={20}
              className={`shrink-0 transition ${hypothesesOuvertes ? 'rotate-180' : ''}`} />
          </button>
          {hypothesesOuvertes && (
            <div className="border-t border-ink/10 p-4">
              <p className="mb-3 text-sm text-dark/70">
                Tous ces chiffres sont des <strong>estimations</strong>, produites par un calcul
                heure par heure sur une année entière. Ils ne remplacent pas l’étude d’un
                installateur. Voici exactement ce sur quoi ils reposent.
              </p>
              <ul className="space-y-2">
                {resultat.hypotheses.map((h) => (
                  <li key={h.libelle} className="border-b border-ink/5 pb-2 last:border-0">
                    <span className="block font-semibold text-ink">{h.libelle}</span>
                    <span className="block text-sm text-dark/80">{h.valeur}</span>
                    <span className="mt-0.5 inline-block rounded-full bg-cream px-2 py-0.5 text-xs text-dark/70">
                      {h.statut}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-sm text-dark/60">Moteur {resultat.version_moteur}.</p>
            </div>
          )}
        </section>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------- Aide */

export function OngletAide() {
  return (
    <div className="space-y-4">
      <Bloc titre="Comment ça marche" ouvert>
        <ol className="list-decimal space-y-3 pl-5 text-dark/85">
          <li>
            Nous récupérons <strong>l’ensoleillement réel de votre commune</strong> auprès de
            PVGIS, le service de la Commission européenne, heure par heure sur une année entière.
          </li>
          <li>
            Nous reconstituons <strong>votre courbe de consommation</strong> à partir de ce que
            vous nous dites : chauffage, eau chaude, climatisation, piscine, voiture. Si vous
            connaissez votre consommation annuelle, tout est recalé dessus.
          </li>
          <li>
            Nous faisons <strong>se rencontrer les deux, heure par heure</strong> — 8 760 heures.
            C’est ce qui dit ce que vous consommez vraiment de votre propre soleil.
          </li>
          <li>
            Nous en déduisons votre facture, vos économies et votre temps de retour, sur 25 ans.
          </li>
        </ol>
      </Bloc>

      <Bloc titre="Ce que ce simulateur ne fait pas">
        <ul className="list-disc space-y-2 pl-5 text-dark/85">
          <li>Il ne lit pas votre vraie courbe Linky : il la reconstitue.</li>
          <li>Il ne regarde pas votre toiture réelle ni les règles d’urbanisme de votre commune.</li>
          <li>Il ne remplace pas le devis d’un installateur certifié RGE.</li>
          <li>Il n’est vendeur de rien. Si une option n’est pas rentable, il le dit.</li>
        </ul>
        <p className="text-sm text-dark/70">
          Un mot ne vous parle pas ? Le <Link to="/glossaire" className="font-semibold text-primary underline">
          glossaire</Link> les explique tous.
        </p>
      </Bloc>
    </div>
  )
}
