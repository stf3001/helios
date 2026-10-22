import { dateCourte } from './libelles'

/** Un relevé mensuel (mises en relation, lot 4), tel que l'API le calcule (`services/releves.py`)
 *  ou le relit figé. Le même rendu sert l'espace partenaire et l'administration. Pas une facture. */
export interface LigneReleve {
  lead_id: string; date: string; heure: string; metier: string | null; code_postal: string | null
  prix_ht: number; etat: string; contestation_refusee: boolean
}
export interface ReleveMois {
  mois: string; statut?: string; cloture_le?: string
  partenaire: { id: string; raison_sociale: string; siret: string | null; demo?: boolean }
  lignes: LigneReleve[]; nb_lignes: number; nb_facturables: number; nb_contestees: number
  en_attente: LigneReleve[]; total_ht: number; tva_taux: number; tva: number; ttc: number
}

export const MENTION_RELEVE = "Relevé de mises en relation — ce document n'est pas une facture."
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
  'novembre', 'décembre']
export const nomDuMois = (mois: string) => { const [a, m] = mois.split('-').map(Number); return `${MOIS[m - 1]} ${a}` }
export const euros = (x: number) => x.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

const ETAT: Record<string, { label: string; style: string }> = {
  facturable: { label: 'Facturable', style: 'text-ink' },
  contestation_en_cours: { label: 'Contestation en cours', style: 'text-terra' },
  contestation_acceptee: { label: 'Contestation acceptée', style: 'text-dark/50 line-through' },
}
const METIER: Record<string, string> = {
  solaire: 'Panneaux solaires', pac: 'Pompe à chaleur', isolation: 'Isolation', eau: "Machine à eau de l'air",
  eolien: 'Éolienne', inertie: 'Stockage par inertie',
}

export function StatutReleve({ statut }: { statut: string }) {
  return statut === 'clos'
    ? <span className="rounded-full border border-leaf/40 bg-leaf/10 px-2 py-0.5 text-xs text-leaf">clos</span>
    : <span className="rounded-full border border-sun/50 bg-sun/10 px-2 py-0.5 text-xs text-dark/80">provisoire</span>
}

export default function Releve({ r }: { r: ReleveMois }) {
  return (
    <div className="space-y-3 text-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-left">
          <thead className="text-xs text-dark/60">
            <tr><th className="py-1 pr-2 font-normal">Transmise le</th><th className="pr-2 font-normal">Travaux</th>
              <th className="pr-2 font-normal">Code postal</th><th className="pr-2 font-normal">État</th>
              <th className="text-right font-normal">Prix HT</th></tr>
          </thead>
          <tbody>
            {r.lignes.map((x) => (
              <tr key={x.lead_id} className="border-t border-bord">
                <td className="py-1 pr-2">{dateCourte(x.date)} {x.heure}</td>
                <td className="pr-2">{METIER[x.metier ?? ''] ?? x.metier}</td>
                <td className="pr-2">{x.code_postal ?? '—'}</td>
                <td className={'pr-2 ' + ETAT[x.etat].style}>{ETAT[x.etat].label}{x.contestation_refusee && <span className="text-dark/50"> (contestation refusée)</span>}</td>
                <td className={'text-right ' + ETAT[x.etat].style}>{euros(x.prix_ht)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <dl className="ml-auto max-w-xs space-y-0.5">
        <div className="flex justify-between font-semibold text-ink"><dt>Total HT ({r.nb_facturables} facturable(s))</dt><dd>{euros(r.total_ht)}</dd></div>
        <div className="flex justify-between text-dark/70"><dt>TVA {Math.round(r.tva_taux * 100)} % (indicative)</dt><dd>{euros(r.tva)}</dd></div>
        <div className="flex justify-between text-dark/70"><dt>TTC (indicatif)</dt><dd>{euros(r.ttc)}</dd></div>
      </dl>
      {r.en_attente.length > 0 && (
        <p className="text-xs text-terra">{r.en_attente.length} contestation(s) en cours, exclue(s) du total tant qu'elle(s) n'est (ne sont) pas tranchée(s).</p>
      )}
    </div>
  )
}
