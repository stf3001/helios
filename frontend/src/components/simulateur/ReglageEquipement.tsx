/**
 * Le contenu du panneau de réglage, selon l'emplacement sur lequel on a cliqué.
 *
 * Un emplacement = un réglage, rien d'autre. On ne mélange pas les onglets : ici on
 * répond à « je clique sur la piscine », pas à « je veux tout régler ».
 */

import {
  CHAUFFAGES, ECS_OPTIONS, euros, kwh, OMBRAGES, ORIENTATIONS,
  type Config, type Resultat,
} from '../../lib/simulateur'
import { Bascule, Champ, Choix, DejaLa, Nombre } from './Reglage'

export const EQUIPEMENTS: { id: string; label: string }[] = [
  { id: 'panneaux', label: 'Panneaux sur le toit' },
  { id: 'carport', label: 'Carport' },
  { id: 'eolienne', label: 'Éolienne' },
  { id: 'batterie', label: 'Batterie physique' },
  { id: 'inertie', label: 'Stockage par inertie' },
  { id: 'batterie_virtuelle', label: 'Batterie virtuelle' },
  { id: 'ballon', label: 'Eau chaude' },
  { id: 'clim', label: 'Climatisation' },
  { id: 'piscine', label: 'Piscine' },
  { id: 'voiture', label: 'Voiture électrique' },
  { id: 'reseau', label: 'Raccordement au réseau' },
]

export function titreDe(id: string): string {
  return EQUIPEMENTS.find((e) => e.id === id)?.label ?? 'Réglage'
}

/** Un emplacement est « installé » dès qu'il pèse sur le calcul. */
export function estInstalle(id: string, config: Config): boolean {
  const { maison, panneaux, stockage } = config
  switch (id) {
    case 'panneaux': return panneaux.nb_panneaux > 0
    case 'carport': return panneaux.nb_panneaux_carport > 0
    case 'eolienne': return config.eolien.kwc > 0
    case 'batterie': return stockage.nb_packs > 0
    case 'inertie': return stockage.inertie
    case 'batterie_virtuelle': return stockage.batterie_virtuelle !== null
    case 'ballon': return maison.ecs === 'ballon_elec' || maison.ecs === 'thermodynamique'
    case 'clim': return maison.clim.present
    case 'piscine': return maison.piscine.present
    case 'voiture': return maison.voiture.present
    case 'reseau': return true
    default: return false
  }
}

export function resumeDe(id: string, config: Config, resultat: Resultat | null): string | null {
  const { maison, panneaux, stockage } = config
  switch (id) {
    case 'panneaux':
      return panneaux.nb_panneaux > 0
        ? `${panneaux.nb_panneaux} panneaux${resultat ? ` · ${resultat.production.kwc_toit} kWc` : ''}`
        : null
    case 'carport':
      return panneaux.nb_panneaux_carport > 0 ? `${panneaux.nb_panneaux_carport} panneaux` : null
    case 'eolienne':
      return config.eolien.kwc > 0 ? `${config.eolien.kwc} kWc` : null
    case 'batterie':
      return stockage.nb_packs > 0
        ? `${stockage.nb_packs} pack(s)${resultat ? ` · ${resultat.stockage.batterie_physique.capacite_kwh} kWh` : ''}`
        : null
    case 'inertie':
      return stockage.inertie
        ? `${resultat?.stockage.inertie.capacite_kwh ?? 10} kWh · garanti ${resultat?.stockage.inertie.garantie_ans ?? 40} ans`
        : null
    case 'batterie_virtuelle':
      return resultat?.stockage.batterie_virtuelle?.label ?? (stockage.batterie_virtuelle ? 'Activée' : null)
    case 'ballon':
      return ECS_OPTIONS.find((o) => o.value === maison.ecs)?.label ?? null
    case 'clim':
      return maison.clim.present ? `${maison.clim.nb_pieces} pièce(s)` : null
    case 'piscine':
      return maison.piscine.present ? `${maison.piscine.volume_m3} m³` : null
    case 'voiture':
      return maison.voiture.present ? `${maison.voiture.km_an.toLocaleString('fr-FR')} km/an` : null
    case 'reseau':
      return maison.raccordement === 'inconnu'
        ? 'Inconnu — traité en monophasé'
        : `${maison.raccordement === 'monophase' ? 'Monophasé' : 'Triphasé'} · ${maison.puissance_souscrite_kva} kVA`
    default:
      return null
  }
}

interface Props {
  id: string
  config: Config
  resultat: Resultat | null
  majConfig: (maj: (c: Config) => Config) => void
}

export default function ReglageEquipement({ id, config, resultat, majConfig }: Props) {
  const majMaison = (maj: Partial<Config['maison']>) =>
    majConfig((c) => ({ ...c, maison: { ...c.maison, ...maj } }))
  const majPanneaux = (maj: Partial<Config['panneaux']>) =>
    majConfig((c) => ({ ...c, panneaux: { ...c.panneaux, ...maj } }))
  const majEolien = (maj: Partial<Config['eolien']>) =>
    majConfig((c) => ({ ...c, eolien: { ...c.eolien, ...maj } }))
  const majStockage = (maj: Partial<Config['stockage']>) =>
    majConfig((c) => ({ ...c, stockage: { ...c.stockage, ...maj } }))

  const { maison, panneaux, stockage } = config
  const maxToit = resultat?.panneaux_max_toit ?? null

  switch (id) {
    case 'panneaux':
      return (
        <>
          <Nombre label="Panneaux" valeur={panneaux.nb_panneaux} min={0} max={40}
            onChange={(v) => majPanneaux({ nb_panneaux: v })}
            aide={resultat ? `${resultat.production.kwc_toit} kWc · ${kwh(resultat.production.annuel_kwh)}/an` : undefined} />
          {maxToit !== null && maxToit > 0 && (
            <button type="button" onClick={() => majPanneaux({ nb_panneaux: Math.min(maxToit, 40) })}
              className="w-full rounded-lg border border-primary px-3 py-2 font-semibold text-primary
                hover:bg-primary hover:text-white">
              Remplir le toit ({Math.min(maxToit, 40)})
            </button>
          )}
          <Choix label="Orientation" valeur={panneaux.orientation} options={ORIENTATIONS}
            onChange={(v) => majPanneaux({ orientation: v })} />
          <Nombre label="Inclinaison" valeur={panneaux.inclinaison} min={0} max={90} pas={5} suffixe="°"
            onChange={(v) => majPanneaux({ inclinaison: v })} />
          <Choix label="Ombrage" valeur={panneaux.ombrage} options={OMBRAGES}
            onChange={(v) => majPanneaux({ ombrage: v })} />
          <Champ label="Surface de toit exploitable" valeur={panneaux.surface_toit_m2} suffixe="m²"
            placeholder="je ne sais pas" onChange={(v) => majPanneaux({ surface_toit_m2: v })} />
        </>
      )

    case 'carport':
      return (
        <>
          <p className="text-sm text-dark/70">
            Un abri de voiture couvert de panneaux, plein sud et peu incliné. Sa structure
            a un coût qui s’ajoute à celui des panneaux.
          </p>
          <Nombre label="Panneaux sur le carport" valeur={panneaux.nb_panneaux_carport} min={0} max={40}
            onChange={(v) => majPanneaux({ nb_panneaux_carport: v })} />
        </>
      )

    case 'eolienne':
      return (
        <>
          <Nombre label="Puissance" valeur={config.eolien.kwc} min={0} max={9} pas={1} suffixe="kWc"
            onChange={(v) => majEolien({ kwc: v === 1 || v === 2 ? 3 : v })}
            aide="0 pour aucune éolienne, sinon de 3 à 9 kWc — c’est la puissance TOTALE." />
          {config.eolien.kwc > 0 && (
            <p className="text-sm text-dark/70">
              Une grande ou plusieurs petites, au choix : 9 kWc, ce sont trois éoliennes de
              3 kW ou six de 1,5 kW — même prix, même production. Groupées, elles
              s’accélèrent mutuellement le vent.
            </p>
          )}
          {resultat && config.eolien.kwc > 0 && (
            <>
              <div className="space-y-1">
                <p className="flex items-baseline justify-between gap-4">
                  <span className="text-dark/70">Production estimée</span>
                  <strong className="text-ink">{kwh(resultat.stockage.eolien.production_kwh)} / an</strong>
                </p>
                <p className="flex items-baseline justify-between gap-4">
                  <span className="text-dark/70">Investissement</span>
                  <strong className="text-ink">{euros(resultat.investissement.eolien_eur)}</strong>
                </p>
              </div>
              {/* D'où vient le chiffre. Douze stations pour la France entière : un visiteur
                  de la Creuse doit savoir que son estimation vient de Lyon, sinon il la
                  prend pour une mesure chez lui. */}
              {resultat.production.vent?.station && (
                <p className="rounded-lg border border-sky/40 bg-sky/10 px-3 py-2 text-sm text-ink">
                  Estimation d’après les vents de <strong>{resultat.production.vent.station}</strong>
                  {resultat.production.vent.distance_km !== undefined
                    && ` — la station la plus proche, à ${resultat.production.vent.distance_km} km`}
                  . Vent moyen {resultat.production.vent.vent_moyen_ms} m/s.
                </p>
              )}
              <p className="text-sm text-dark/80">
                <strong>EOLIA prête un anémomètre.</strong> Vous le plantez un mois à
                l’endroit prévu, vous envoyez les relevés, et la production est recalée sur
                VOTRE terrain. C’est la seule façon de savoir vraiment — le vent change
                d’une parcelle à l’autre, bien plus que le soleil.
              </p>
              <p className="text-sm text-dark/60">
                Tarif indicatif, pose et démarches comprises, pour moins de 50 m entre le
                tableau et l’éolienne. Au-delà, EOLIA chiffre des options que le simulateur
                ne connaît pas.
              </p>
            </>
          )}
        </>
      )

    case 'batterie':
      return (
        <>
          <p className="rounded-lg border border-terra/40 bg-terra/10 px-3 py-2 text-sm text-ink">
            Ajouter une batterie fait passer <strong>tout le projet</strong> de 5,5 % à 20 % de TVA.
            C’est la règle fiscale, pas un réglage : elle pèse lourd dans la comparaison.
          </p>
          <Nombre label="Packs" valeur={stockage.nb_packs} min={0} max={6}
            onChange={(v) => majStockage({ nb_packs: v })}
            aide={resultat && resultat.stockage.batterie_physique.capacite_kwh > 0
              ? `${resultat.stockage.batterie_physique.capacite_kwh} kWh utiles` : undefined} />
          <Bascule label="Je veux tenir en cas de coupure" actif={maison.besoin_secours}
            onChange={(v) => majMaison({ besoin_secours: v })}
            aide="C’est le seul avantage qu’aucune autre solution ne donne." />
        </>
      )

    case 'inertie':
      return (
        <>
          <p className="rounded-lg border border-terra/40 bg-terra/10 px-3 py-2 text-sm text-ink">
            Comme toute batterie, elle fait passer <strong>tout le projet</strong> de 5,5 % à
            20 % de TVA. Point à confirmer auprès de votre installateur.
          </p>
          <Bascule label="J’enterre un stockage par inertie" actif={stockage.inertie}
            onChange={(v) => majStockage({ inertie: v })}
            aide={resultat
              ? `${resultat.stockage.inertie.capacite_kwh || 10} kWh, jusqu’à ${resultat.stockage.inertie.puissance_kw || 6} kW en sortie`
              : '10 kWh, jusqu’à 6 kW en sortie'} />
          {/* Ce qui la distingue d'un pack lithium, et qui justifie son prix : elle ne se
              remplace pas dans la durée de l'étude. Le dire ici, c'est éviter la question
              « pourquoi est-ce plus cher pour la même capacité ». */}
          <ul className="space-y-1.5 text-sm text-dark/80">
            <li>· Enterrée, garantie 40 ans — aucun remplacement sur les 25 ans de l’étude,
              là où un pack lithium se change une fois.</li>
            <li>· Sans lithium : rien à extraire, rien à recycler au bout du compte.</li>
            <li>· Une seule unité possible. Ce n’est pas un pack qu’on empile, c’est un
              ouvrage.</li>
            <li>· Démarches d’urbanisme simples — une déclaration suffit.</li>
          </ul>
          <p className="text-sm text-dark/60">
            {resultat ? `${resultat.stockage.inertie.cout_ttc_eur.toLocaleString('fr-FR')} € TTC` : '8 500 € TTC'},
            pose comprise, TVA 20 % incluse.
          </p>
        </>
      )

    case 'batterie_virtuelle':
      return (
        <>
          {/* Le sur-mesure en premier : c'est celui qu'on conseille, et l'ordre d'une liste
              est lu comme un classement. Noms commerciaux de MyLight — ce sont ceux que
              l'utilisateur retrouvera sur leur site. */}
          <Choix label="Offre" valeur={stockage.batterie_virtuelle ?? 'aucune'}
            options={[
              { value: 'aucune', label: 'Aucune' },
              { value: 'mysmartbattery', label: 'MyLight — Stockage sur-mesure' },
              { value: 'mybattery', label: 'MyLight — Stockage illimité' },
            ]}
            onChange={(v) => majStockage({ batterie_virtuelle: v === 'aucune' ? null : v })} />
          {resultat?.stockage.batterie_virtuelle && (
            <p className="rounded-lg border border-sky/40 bg-sky/10 px-3 py-2 text-sm text-ink">
              {resultat.stockage.batterie_virtuelle.note}
            </p>
          )}
          {/* Le conseil est distingué du fait : encadré de la couleur de la marque, et
              annoncé comme un avis. Un visiteur doit pouvoir faire la part des deux. */}
          {resultat?.stockage.batterie_virtuelle?.conseil && (
            <p className="rounded-lg border border-primary/40 bg-primary/5 px-3 py-2 text-sm text-ink">
              <strong>Notre avis — </strong>
              {resultat.stockage.batterie_virtuelle.conseil}
            </p>
          )}
          {resultat?.stockage.batterie_virtuelle?.fournisseur_impose && (
            <p className="text-sm text-dark/70">
              Impose de souscrire l’électricité chez{' '}
              <strong>{resultat.stockage.batterie_virtuelle.fournisseur_impose}</strong>.
              Beaucoup de foyers refusent d’en changer : c’est un vrai critère.
            </p>
          )}
        </>
      )

    case 'ballon':
      return (
        <>
          <Choix label="Type d’eau chaude" valeur={maison.ecs} options={ECS_OPTIONS}
            onChange={(v) => majMaison({ ecs: v })} />
          <Choix label="Chauffage du logement" valeur={maison.chauffage} options={CHAUFFAGES}
            onChange={(v) => majMaison({ chauffage: v })} />
          <Bascule label="Piloter mes usages" actif={stockage.pilotage}
            onChange={(v) => majStockage({ pilotage: v })}
            aide="Décale le ballon, la filtration et la recharge vers les heures de soleil." />
        </>
      )

    case 'clim':
      return (
        <>
          <Bascule label="J’ai (ou je veux) une climatisation" actif={maison.clim.present}
            onChange={(v) => majMaison({ clim: { ...maison.clim, present: v } })} />
          {maison.clim.present && (
            <>
              <DejaLa deja={maison.clim.deja_installe}
                onChange={(v) => majMaison({ clim: { ...maison.clim, deja_installe: v } })} />
              <Nombre label="Pièces climatisées" valeur={maison.clim.nb_pieces} min={1} max={20}
                onChange={(v) => majMaison({ clim: { ...maison.clim, nb_pieces: v } })} />
              <Choix label="Surtout utilisée" valeur={maison.clim.plage}
                options={[
                  { value: 'apres_midi', label: 'L’après-midi' },
                  { value: 'soiree', label: 'En soirée' },
                  { value: 'nuit', label: 'La nuit' },
                ]}
                onChange={(v) => majMaison({ clim: { ...maison.clim, plage: v } })}
                aide="L’après-midi tombe en plein soleil : c’est le meilleur des cas." />
            </>
          )}
        </>
      )

    case 'piscine':
      return (
        <>
          <Bascule label="J’ai (ou je veux) une piscine" actif={maison.piscine.present}
            onChange={(v) => majMaison({ piscine: { ...maison.piscine, present: v } })} />
          {maison.piscine.present && (
            <>
              <DejaLa deja={maison.piscine.deja_installe}
                onChange={(v) => majMaison({ piscine: { ...maison.piscine, deja_installe: v } })} />
              <Champ label="Volume du bassin" valeur={maison.piscine.volume_m3} suffixe="m³"
                onChange={(v) => majMaison({ piscine: { ...maison.piscine, volume_m3: v ?? 40 } })} />
              <Champ label="Puissance de la pompe (si connue)" valeur={maison.piscine.pompe_kw}
                suffixe="kW" placeholder="je ne sais pas"
                onChange={(v) => majMaison({ piscine: { ...maison.piscine, pompe_kw: v } })} />
            </>
          )}
        </>
      )

    case 'voiture':
      return (
        <>
          <Bascule label="J’ai (ou je veux) une voiture électrique" actif={maison.voiture.present}
            onChange={(v) => majMaison({ voiture: { ...maison.voiture, present: v } })} />
          {maison.voiture.present && (
            <>
              <DejaLa deja={maison.voiture.deja_installe}
                onChange={(v) => majMaison({ voiture: { ...maison.voiture, deja_installe: v } })} />
              <Champ label="Kilomètres par an" valeur={maison.voiture.km_an} suffixe="km"
                onChange={(v) => majMaison({ voiture: { ...maison.voiture, km_an: v ?? 12000 } })} />
              <Choix label="Recharge" valeur={maison.voiture.recharge}
                options={[{ value: 'soir', label: 'Le soir' }, { value: 'nuit', label: 'La nuit' }]}
                onChange={(v) => majMaison({ voiture: { ...maison.voiture, recharge: v } })} />
              <Bascule label="La voiture est là en journée"
                actif={maison.voiture.presente_en_journee}
                onChange={(v) => majMaison({ voiture: { ...maison.voiture, presente_en_journee: v } })}
                aide="Si oui, le pilotage peut la recharger au soleil plutôt que la nuit." />
            </>
          )}
        </>
      )

    case 'reseau':
      return (
        <>
          <Choix label="Raccordement" valeur={maison.raccordement}
            options={[
              { value: 'monophase', label: 'Monophasé' },
              { value: 'triphase', label: 'Triphasé' },
              { value: 'inconnu', label: 'Je ne sais pas' },
            ]}
            onChange={(v) => majMaison({ raccordement: v })}
            aide="En monophasé, on ne peut injecter que 6 kVA. Au-delà, l’énergie produite est perdue." />
          <Champ label="Puissance souscrite" valeur={maison.puissance_souscrite_kva} suffixe="kVA"
            onChange={(v) => majMaison({ puissance_souscrite_kva: v ?? 9 })}
            aide="Sur votre facture. Elle fixe le prix du kWh et le montant de l’abonnement." />
        </>
      )

    default:
      return <p className="text-dark/70">Rien à régler ici.</p>
  }
}
