import { useCallback, useEffect, useState } from 'react'
import { CalendarDays, Check, ExternalLink, HelpCircle } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Depliant from '../Depliant'
import type { Doc } from './Formulaires'
import FormFait from './FormFait'
import { type Echeance, type EquipementNom, QUI, echeanceRelative, nomEquipement, useMaj } from './commun'

/**
 * Le calendrier complet (« Tout voir » du bloc), dans « Ma maison » : toutes les échéances,
 * groupées par statut. « Plus tard » est replié : c'est la liste la plus longue et la moins
 * pressante. Chaque tâche porte sa source — une obligation cite son texte.
 */

type Verification = { tache_id: string; libelle: string; tache_libelle: string; lien: string | null }
type Reponse = {
  version: string; avertissement: string; table_vide: boolean; echeances: Echeance[]; verifications: Verification[]
}

const GROUPES: [Echeance['statut'], string][] = [
  ['en_retard', 'En retard'], ['ce_mois', 'Ce mois-ci'], ['bientot', 'Dans les trois mois'],
  ['a_planifier', 'À planifier'], ['plus_tard', 'Plus tard'],
]

function Ligne({ e, parId, documents }: { e: Echeance; parId: Record<string, EquipementNom>; documents: Doc[] }) {
  const [ouvert, setOuvert] = useState(false)
  return (
    <li className="py-2.5">
      <div className="flex items-start gap-3">
        <span className="min-w-0 flex-1 text-sm">
          <span className="block text-ink">{e.libelle}</span>
          <span className="block text-xs text-dark/60">
            {nomEquipement(e.equipement_id ? parId[e.equipement_id] : undefined)} ·{' '}
            <span className={e.statut === 'en_retard' ? 'font-semibold text-terra' : ''}>{echeanceRelative(e.echeance)}</span>
            {' '}· {QUI[e.qui] ?? e.qui} · {e.nature === 'obligation' ? 'obligation' : 'conseil'}
          </span>
          {e.statut === 'a_planifier' && (
            <span className="block text-xs text-dark/50">
              {e.equipement_id ? 'Date de pose inconnue : indiquez-la, ou dites quand c’était fait.' : 'Dites quand c’était fait pour la dernière fois.'}
            </span>
          )}
          {e.reference_supposee && <span className="block text-xs text-dark/50">Calculé depuis l’année de pose (date supposée au 1er juillet).</span>}
          {e.mention_puissance && <span className="block text-xs text-dark/50">{e.mention_puissance}</span>}
          {e.note && <span className="block text-xs text-dark/50">{e.note}</span>}
          {e.source && (
            <span className="block text-xs text-dark/45">
              {e.source.url
                ? <a href={e.source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 hover:text-primary hover:underline">{e.source.titre} <ExternalLink className="h-3 w-3" /></a>
                : e.source.titre}
            </span>
          )}
        </span>
        {!ouvert && (
          <button onClick={() => setOuvert(true)}
            className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-primary px-2.5 py-1 text-xs font-semibold text-primary hover:bg-primary/5">
            <Check className="h-3.5 w-3.5" /> C'est fait
          </button>
        )}
      </div>
      {ouvert && <FormFait tacheId={e.tache_id} equipementId={e.equipement_id} documents={documents} onFini={() => setOuvert(false)} />}
    </li>
  )
}

export default function Calendrier({ equipements, documents }: { equipements: EquipementNom[]; documents: Doc[] }) {
  const { authFetch } = useAuth()
  const [r, setR] = useState<Reponse | null>(null)
  const charger = useCallback(() => {
    authFetch('/api/houses/me/entretien').then((res) => (res.ok ? res.json() : null)).then(setR)
  }, [authFetch])
  useEffect(charger, [charger])
  useMaj(charger)

  if (!r) return null
  const parId = Object.fromEntries(equipements.map((e) => [e.id, e]))

  return (
    <section id="calendrier-entretien" className="scroll-mt-20 rounded-xl border border-ink/10 bg-white p-4">
      <h2 className="mb-3 flex items-center gap-2 font-display text-xl text-ink">
        <CalendarDays className="h-5 w-5 text-primary" /> Calendrier d'entretien
      </h2>
      {r.table_vide ? (
        <p className="text-sm text-dark/70">Le calendrier d'entretien est en préparation : il sera relu avant d'être publié.</p>
      ) : (
        <div className="space-y-4">
          {r.verifications.map((v) => (
            <p key={v.tache_id} className="flex items-start gap-2 rounded-lg bg-cream px-3 py-2 text-sm text-dark/80">
              <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <span>{v.libelle} par : {v.tache_libelle.toLowerCase()}.{' '}
                {v.lien && <a href={v.lien} target="_blank" rel="noreferrer" className="font-semibold text-primary hover:underline">Vérifier sur Service Public</a>}
              </span>
            </p>
          ))}
          {r.echeances.length === 0 && (
            <p className="text-sm text-dark/70">Aucune tâche pour vos équipements actuels. Ajoutez-en dans « Mes équipements ».</p>
          )}
          {GROUPES.map(([statut, titre]) => {
            const lignes = r.echeances.filter((e) => e.statut === statut)
            if (!lignes.length) return null
            const liste = (
              <ul className="divide-y divide-bord">
                {lignes.map((e) => <Ligne key={`${e.tache_id}|${e.equipement_id ?? ''}`} e={e} parId={parId} documents={documents} />)}
              </ul>
            )
            return statut === 'plus_tard'
              ? <Depliant key={statut} titre={titre} resume={`${lignes.length}`}>{liste}</Depliant>
              : (
                <div key={statut}>
                  <h3 className={'mb-1 text-xs font-semibold uppercase tracking-wide ' + (statut === 'en_retard' ? 'text-terra' : 'text-dark/50')}>
                    {titre} · {lignes.length}
                  </h3>
                  {liste}
                </div>
              )
          })}
          <p className="text-xs text-dark/50">{r.avertissement}</p>
        </div>
      )}
    </section>
  )
}
