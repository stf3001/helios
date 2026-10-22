import { useCallback, useEffect, useState } from 'react'
import { CalendarCheck, Check, PhoneCall, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { type ApresEpisode, LigneVigilance, type Vigilance, noterUnDegat } from './VigilanceMeteo'
import { useAuth } from '../../context/AuthContext'
import type { Doc } from './Formulaires'
import FormFait from './FormFait'
import {
  type Echeance, type EquipementNom, QUI, dateLongue, echeanceRelative, nomEquipement, useMaj,
} from './commun'

/**
 * « À faire ce mois-ci » (carnet, lot 4), en tête de l'espace, au-dessus des onglets.
 *
 * Le contenu est choisi côté serveur (`services/a_faire.py`) : tâches en retard et du mois,
 * jusqu'à 3 « bientôt », garanties qui expirent ; 6 lignes au plus. Replié en UNE ligne
 * quand il n'y a rien à faire — un bloc vide en tête de page ferait du bruit tous les jours.
 */

type Ligne = (Echeance & { kind: 'tache' }) | {
  kind: 'garantie'; libelle: string; fin: string; statut: string; provenance: string; mention: string | null
}
type Bloc = {
  lignes: Ligne[]; masquees: number; table_vide: boolean; rien_d_urgent: boolean; sans_equipement: boolean
  prochaine: { libelle: string; echeance: string; equipement_id: string | null } | null
  // Mises en relation, lot 5 : « L'entreprise vous a-t-elle contacté ? », tant que sans réponse.
  questions_contact?: { lead_id: string; partenaire: string | null; metier: string | null; transmis_le: string }[]
  // Phase 2 : feux de forêt dans la commune et débroussaillement « je ne sais pas ».
  debroussaillement?: { libelle: string; lien: string | null } | null
  // Vigilance météo (phase 2) : discrète, une ligne ; puis « Noter un dégât » après vent ou orages.
  vigilances?: Vigilance[]
  apres_episode?: ApresEpisode[]
}

function Pastille({ nature }: { nature: string }) {
  return nature === 'obligation'
    ? <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">Obligation</span>
    : <span className="shrink-0 rounded-full bg-leaf/10 px-2 py-0.5 text-xs font-semibold text-leaf">Conseil</span>
}

export default function AFaire({ onVoirMaison, onToutVoir }: { onVoirMaison: () => void; onToutVoir: () => void }) {
  const { authFetch } = useAuth()
  const [bloc, setBloc] = useState<Bloc | null>(null)
  const [equipements, setEquipements] = useState<EquipementNom[]>([])
  const [documents, setDocuments] = useState<Doc[]>([])
  const [ouvert, setOuvert] = useState<string | null>(null)
  const [signale, setSignale] = useState(false)

  const charger = useCallback(() => {
    const json = (url: string) => authFetch(url).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
    Promise.all([json('/api/houses/me/a-faire'), json('/api/houses/me/equipements'), json('/api/houses/me/documents')])
      .then(([b, eq, docs]) => { setBloc(b); setEquipements(eq); setDocuments(docs) })
      .catch(() => setBloc(null))  // le bloc se tait plutôt que d'encombrer l'espace d'une erreur
  }, [authFetch])
  useEffect(charger, [charger])
  useMaj(charger)

  if (!bloc) return null

  async function repondre(leadId: string, reponse: 'oui' | 'non') {
    const r = await authFetch(`/api/leads/${leadId}/contact`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reponse }),
    })
    if (r.ok) { if (reponse === 'non') setSignale(true); charger() }
  }
  const parId = Object.fromEntries(equipements.map((e) => [e.id, e]))

  const entete = (
    <span className="flex items-center gap-2 font-display text-lg text-ink">
      <CalendarCheck className="h-5 w-5 text-primary" /> À faire ce mois-ci
    </span>
  )

  // Rien à faire : une seule ligne, discrète.
  if (bloc.rien_d_urgent) {
    let message: React.ReactNode
    if (bloc.sans_equipement) {
      message = <>Ajoutez vos équipements pour recevoir votre calendrier d'entretien.{' '}
        <button onClick={onVoirMaison} className="font-semibold text-primary hover:underline">Ma maison</button></>
    } else if (bloc.table_vide) {
      message = "Le calendrier d'entretien est en préparation : il sera relu avant d'être publié."
    } else {
      message = <>Rien à faire ce mois-ci.{bloc.prochaine && ` Prochaine échéance : ${bloc.prochaine.libelle.toLowerCase()}, ${dateLongue(bloc.prochaine.echeance)}.`}{' '}
        <button onClick={onToutVoir} className="font-semibold text-primary hover:underline">Tout voir</button></>
    }
    return (
      <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-bord bg-white px-4 py-2.5">
        <CalendarCheck className="h-4 w-4 shrink-0 text-primary" />
        <p className="min-w-0 flex-1 text-sm text-dark/70">{message}</p>
      </div>
    )
  }

  return (
    <section className="mb-4 rounded-xl border border-bord bg-white p-4" aria-label="À faire ce mois-ci">
      <div className="mb-2 flex items-center justify-between gap-2">
        {entete}
        <button onClick={onToutVoir} className="text-sm font-semibold text-primary hover:underline">Tout voir</button>
      </div>
      {bloc.table_vide && (
        <p className="mb-2 text-sm text-dark/60">Le calendrier d'entretien est en préparation : il sera relu avant d'être publié.</p>
      )}
      {bloc.sans_equipement && !bloc.table_vide && (
        <p className="mb-2 text-sm text-dark/60">
          Ajoutez vos équipements pour recevoir votre calendrier d'entretien.{' '}
          <button onClick={onVoirMaison} className="font-semibold text-primary hover:underline">Ma maison</button>
        </p>
      )}
      {signale && (
        <p className="mb-2 text-sm text-dark/70">C'est noté. Vous pouvez demander une autre entreprise dans{' '}
          <Link to="/espace/mises-en-relation" className="font-semibold text-primary hover:underline">vos mises en relation</Link>.</p>
      )}
      <ul className="divide-y divide-bord">
        {(bloc.questions_contact ?? []).map((q) => (
          <li key={q.lead_id} className="flex flex-wrap items-center gap-3 py-2.5">
            <PhoneCall className="h-4 w-4 shrink-0 text-primary" />
            <span className="min-w-0 flex-1 text-sm text-ink">
              {q.partenaire ?? "L'entreprise"} vous a-t-elle contacté ?
              <span className="block text-xs text-dark/60">demande transmise le {new Date(q.transmis_le).toLocaleDateString('fr-FR')}</span>
            </span>
            <span className="flex gap-2">
              <button onClick={() => repondre(q.lead_id, 'oui')} className="rounded-lg border border-bord px-3 py-1 text-xs hover:bg-cream">Oui</button>
              <button onClick={() => repondre(q.lead_id, 'non')} className="rounded-lg border border-bord px-3 py-1 text-xs hover:bg-cream">Non</button>
            </span>
          </li>
        ))}
        {(bloc.vigilances ?? []).map((v) => (
          <li key={`v-${v.phenomene}-${v.debut}`} className="py-2.5"><LigneVigilance v={v} /></li>
        ))}
        {(bloc.apres_episode ?? []).map((a) => (
          <li key={`d-${a.phenomene}`} className="flex flex-wrap items-center gap-3 py-2.5">
            <span className="min-w-0 flex-1 text-sm text-ink">
              Après l'épisode de {a.libelle.toLowerCase()} : un dégât à noter ?
              <span className="block text-xs text-dark/60">utile pour l'assurance, avec une photo</span>
            </span>
            <button onClick={() => noterUnDegat(a, onVoirMaison)}
              className="rounded-lg border border-bord px-3 py-1 text-xs hover:bg-cream">Noter un dégât</button>
          </li>
        ))}
        {bloc.debroussaillement && (
          <li className="flex flex-wrap items-center gap-3 py-2.5">
            <ShieldCheck className="h-4 w-4 shrink-0 text-terra" />
            <span className="min-w-0 flex-1 text-sm text-ink">
              Feux de forêt dans votre commune : {bloc.debroussaillement.libelle.toLowerCase()} par le débroussaillement obligatoire.
              <span className="block text-xs text-dark/60">
                <Link to="/mon-espace" className="text-primary hover:underline">Répondre dans ma fiche</Link>
                {bloc.debroussaillement.lien && <>{' · '}<a href={bloc.debroussaillement.lien} target="_blank" rel="noreferrer" className="text-primary hover:underline">vérifier</a></>}
              </span>
            </span>
          </li>
        )}
        {bloc.lignes.map((l, i) => {
          if (l.kind === 'garantie') {
            return (
              <li key={`g${i}`} className="flex items-start gap-3 py-2.5">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-terra" />
                <span className="min-w-0 flex-1 text-sm">
                  <span className="block text-ink">{l.libelle}</span>
                  <span className="block text-xs text-dark/60">se termine le {dateLongue(l.fin)}{l.mention ? ' · à vérifier sur votre contrat' : ''}</span>
                </span>
              </li>
            )
          }
          const cle = `${l.tache_id}|${l.equipement_id ?? ''}`
          return (
            <li key={cle} className="py-2.5">
              <div className="flex items-start gap-3">
                <span className="min-w-0 flex-1 text-sm">
                  <span className="block text-ink">{l.libelle}</span>
                  <span className="block text-xs text-dark/60">
                    {nomEquipement(l.equipement_id ? parId[l.equipement_id] : undefined)} ·{' '}
                    <span className={l.statut === 'en_retard' ? 'font-semibold text-terra' : ''}>{echeanceRelative(l.echeance)}</span>
                    {' '}· {QUI[l.qui] ?? l.qui}
                  </span>
                  {l.mention_puissance && <span className="block text-xs text-dark/50">{l.mention_puissance}</span>}
                </span>
                <span className="flex shrink-0 flex-col items-end gap-1.5 sm:flex-row sm:items-center">
                  <Pastille nature={l.nature} />
                  {ouvert !== cle && (
                    <button onClick={() => setOuvert(cle)}
                      className="inline-flex items-center gap-1 rounded-lg border border-primary px-2.5 py-1 text-xs font-semibold text-primary hover:bg-primary/5">
                      <Check className="h-3.5 w-3.5" /> C'est fait
                    </button>
                  )}
                </span>
              </div>
              {ouvert === cle && (
                <FormFait tacheId={l.tache_id} equipementId={l.equipement_id} documents={documents}
                  onFini={() => setOuvert(null)} />
              )}
            </li>
          )
        })}
      </ul>
      {bloc.masquees > 0 && (
        <button onClick={onToutVoir} className="mt-1 text-xs text-dark/60 hover:text-primary hover:underline">
          Et {bloc.masquees} autre{bloc.masquees > 1 ? 's' : ''} : tout voir
        </button>
      )}
    </section>
  )
}
