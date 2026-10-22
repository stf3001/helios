import { CalendarClock, Check, FileText, X } from 'lucide-react'
import { champFiche } from '../../pages/FicheMaison'
import { dateFr } from '../carnet/libelles'

/** Le dossier d'une mise en relation, tel que l'API le fige (`services/dossier_lead.py`). Le même
 *  rendu sert l'aperçu du foyer et la vue du partenaire : ce que l'un voit, l'autre le reçoit. */
export interface Creneau { jour: string; plage: string }
export interface LigneScore { critere: string; libelle: string; points: number; acquis: boolean }
export interface DossierLead {
  constitue_le: string
  minimum: { code_postal: string; type_logement: string | null; metier: string; message: string | null }
  fiche?: Record<string, unknown>
  projet?: Record<string, unknown>
  etude?: Record<string, unknown> & { type: string; date: string }
  documents?: { id: string; type: string; filename: string }[]
}

export const JOURS: [string, string][] = [
  ['lundi', 'Lundi'], ['mardi', 'Mardi'], ['mercredi', 'Mercredi'], ['jeudi', 'Jeudi'], ['vendredi', 'Vendredi'],
  ['samedi', 'Samedi'],
]
export const PLAGES: [string, string][] = [['matin', 'Matin'], ['midi', 'Midi'], ['apres_midi', 'Après-midi'], ['soir', 'Soir']]
const JOUR = Object.fromEntries(JOURS)
const PLAGE = Object.fromEntries(PLAGES)
const ETAPE: Record<string, string> = {
  idee: 'Idée', etude: "À l'étude", devis: 'Devis', decide: 'Décidé', travaux: 'Travaux en cours', termine: 'Terminé',
}
const METIER: Record<string, string> = {
  solaire: 'Panneaux solaires', pac: 'Pompe à chaleur', isolation: 'Isolation', eau: "Machine à eau de l'air",
  eolien: 'Éolienne', inertie: 'Stockage par inertie',
}
const LOGEMENT: Record<string, string> = { maison: 'Maison', appartement: 'Appartement' }
// L'ordre de `CHAMPS_FICHE` (`dossier_lead.py`) : Postgres ne garde pas l'ordre des clés d'un JSONB.
const ORDRE_FICHE = ['surface_habitable', 'annee_construction', 'chauffage_principal', 'chauffage_principal_annee',
  'isolation_combles', 'isolation_murs', 'isolation_plancher', 'menuiseries', 'horizon', 'budget_envisage']
const SOURCE: Record<string, string> = { etude: 'étude', audit: 'pré-audit', devis: 'devis' }

const euros = (v: unknown) => (typeof v === 'number' ? `${Math.round(v).toLocaleString('fr-FR')} €` : null)
function fourchette(v: unknown): string | null {
  if (v && typeof v === 'object') {
    const o = v as Record<string, number>
    if (o.bas != null && o.haut != null) return o.bas === o.haut ? euros(o.bas) : `${euros(o.bas)} à ${euros(o.haut)}`
    return euros(o.central)
  }
  return euros(v)
}

function Ligne({ label, valeur }: { label: string; valeur: React.ReactNode }) {
  if (valeur == null || valeur === '') return null
  return <div className="flex gap-2 text-sm"><dt className="w-44 shrink-0 text-dark/60">{label}</dt><dd className="min-w-0 text-ink">{valeur}</dd></div>
}

function Rubrique({ titre, children }: { titre: string; children: React.ReactNode }) {
  return <div><p className="mb-1 text-sm font-semibold text-ink">{titre}</p><dl className="space-y-0.5">{children}</dl></div>
}

export function Creneaux({ creneaux }: { creneaux: Creneau[] }) {
  return (
    <div className="rounded-xl border border-bord bg-cream/60 p-3">
      <p className="mb-1 flex items-center gap-1.5 text-sm font-semibold text-ink"><CalendarClock className="h-4 w-4" /> Créneaux pour être appelé</p>
      <p className="text-sm text-ink">{creneaux.map((c) => `${JOUR[c.jour]} ${PLAGE[c.plage].toLowerCase()}`).join(' · ') || '—'}</p>
    </div>
  )
}

export function Score({ score, detail }: { score: number; detail: LigneScore[] }) {
  return (
    <div>
      <p className="mb-1 text-sm font-semibold text-ink">Score de qualification : {score}/100</p>
      <ul className="space-y-0.5">
        {detail.map((d) => (
          <li key={d.critere} className={'flex items-center gap-2 text-sm ' + (d.acquis ? 'text-ink' : 'text-dark/50')}>
            {d.acquis ? <Check className="h-4 w-4 text-leaf" /> : <X className="h-4 w-4" />}
            <span className="min-w-0 flex-1">{d.libelle}</span>
            <span className="tabular-nums">{d.acquis ? `+${d.points}` : `0/${d.points}`}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Dossier({ dossier, lienDocument }: { dossier: DossierLead; lienDocument?: (id: string) => void }) {
  const { minimum, fiche, projet, etude, documents } = dossier
  return (
    <div className="space-y-4">
      <Rubrique titre={`Dossier constitué le ${dateFr(dossier.constitue_le)}`}>
        <Ligne label="Code postal" valeur={minimum.code_postal} />
        <Ligne label="Logement" valeur={minimum.type_logement ? LOGEMENT[minimum.type_logement] ?? minimum.type_logement : null} />
        <Ligne label="Travaux" valeur={METIER[minimum.metier] ?? minimum.metier} />
        <Ligne label="Message" valeur={minimum.message ?? <span className="text-dark/50">Aucun message</span>} />
      </Rubrique>
      {fiche && (
        <Rubrique titre="Résumé de la fiche maison">
          {ORDRE_FICHE.filter((k) => fiche[k] != null).map((k) => {
            const c = champFiche(k, fiche[k])
            return <Ligne key={k} label={c.label} valeur={c.valeur} />
          })}
          <Ligne label="Fiche remplie à" valeur={typeof fiche.completeness_score === 'number' ? `${Math.round(fiche.completeness_score)} %` : null} />
        </Rubrique>
      )}
      {projet && (
        <Rubrique titre="Projet du carnet">
          <Ligne label="Projet" valeur={projet.titre as string} />
          <Ligne label="Étape" valeur={ETAPE[projet.etape as string] ?? (projet.etape as string)} />
          <Ligne label="Budget" valeur={projet.budget_bas_eur != null
            ? `${fourchette({ bas: projet.budget_bas_eur, haut: projet.budget_haut_eur ?? projet.budget_bas_eur })}`
              + (projet.budget_source ? ` (source : ${SOURCE[projet.budget_source as string] ?? projet.budget_source}${projet.budget_date ? `, ${dateFr(projet.budget_date as string)}` : ''})` : '')
            : null} />
          <Ligne label="Économie estimée" valeur={projet.economie_annuelle_eur != null ? `${euros(projet.economie_annuelle_eur)} par an` : null} />
        </Rubrique>
      )}
      {etude && (
        <Rubrique titre={`${etude.type === 'audit' ? 'Pré-audit' : 'Étude du simulateur'} du ${dateFr(etude.date)}`}>
          {etude.type === 'audit'
            ? ((etude.actions as { label: string; cout_eur: unknown; economie_annuelle_eur: unknown }[]) ?? []).map((a) => (
              <Ligne key={a.label} label={a.label} valeur={[fourchette(a.cout_eur), a.economie_annuelle_eur ? `${fourchette(a.economie_annuelle_eur)} d'économie par an` : null].filter(Boolean).join(' · ')} />
            ))
            : <>
              <Ligne label="Puissance" valeur={etude.puissance_kwc != null ? `${etude.puissance_kwc} kWc` : null} />
              <Ligne label="Investissement" valeur={euros(etude.investissement_eur)} />
              <Ligne label="Économie 1re année" valeur={euros(etude.economie_1re_annee_eur)} />
              <Ligne label="Temps de retour" valeur={etude.temps_retour_ans != null ? `${etude.temps_retour_ans} ans` : null} />
            </>}
        </Rubrique>
      )}
      {documents && documents.length > 0 && (
        <Rubrique titre="Documents joints">
          {documents.map((d) => (
            <div key={d.id} className="flex items-center gap-2 text-sm text-ink">
              <FileText className="h-4 w-4 text-dark/50" />
              {lienDocument
                ? <button type="button" onClick={() => lienDocument(d.id)} className="underline">{d.filename}</button>
                : d.filename}
            </div>
          ))}
        </Rubrique>
      )}
    </div>
  )
}
