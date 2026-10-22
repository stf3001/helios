import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Calculator, FolderKanban, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import Depliant from '../Depliant'
import { faqSlug } from '../../lib/faqSlug'
import { type Doc, type Equipement, messageErreur } from './Formulaires'
import { aujourdhui, signalerMaj, useMaj } from './commun'
import { dateFr, libelleType } from './libelles'

/**
 * « Mes projets » (carnet, lot 9) : de l'idée à la réception des travaux.
 *
 * L'écran n'affiche AUCUN chiffre qu'il aurait calculé : budget et économie viennent d'un
 * calcul déjà fait (simulateur, pré-audit — « Reprendre le dernier calcul ») ou d'un devis
 * déclaré par le foyer, et chacun dit sa source, son statut et sa date. Sans calcul, on
 * renvoie vers l'outil. Aucune explication non plus : « Avant de signer » renvoie aux fiches.
 * « Les travaux sont terminés » remplit le carnet en une fois (chantier, garanties,
 * équipements cochés, journal) : tout le carnet se recharge ensuite.
 */

type Modele = {
  id: string; titre: string; famille: string; outil: string; outil_lien: string | null
  calcul: { type: string; date: string } | null
}
type EquipementPropose = { categorie: string; type: string; origine_fiche?: string }
type Projet = {
  id: string; modele_id: string; titre: string; etape: string
  etude_ref: { type: string; date: string; perimetre_economie?: string; autres_postes?: string[] } | null
  budget_bas_eur: number | null; budget_haut_eur: number | null; budget_source: string | null
  budget_statut: string | null; budget_date: string | null
  economie_annuelle_eur: number | null; economie_source: string | null; economie_statut: string | null
  economie_date: string | null; devis_document_ids: string[] | null; note: string | null; travaux_id: string | null
  modele: { titre: string; famille: string; outil: string; outil_lien: string | null; equipements_crees: EquipementPropose[] } | null
  fiches?: { source: string; questions: string[] }[]
}

const ETAPES: Record<string, string> = {
  idee: 'Idée', etude: "À l'étude", devis: 'Devis', decide: 'Décidé', travaux: 'Travaux en cours',
  termine: 'Terminé', abandonne: 'Abandonné',
}
const EN_COURS = ['idee', 'etude', 'devis', 'decide', 'travaux']
const FAMILLES: Record<string, string> = {
  solaire_stockage: 'Solaire et stockage', sortie_fossile: 'Chauffage et eau chaude', ecosysteme: 'Autour de la maison',
}
const SOURCES: Record<string, string> = { etude: 'étude du simulateur', audit: 'pré-audit', devis: 'devis' }
const STATUTS: Record<string, string> = { calcule: 'calculé', suppose: 'supposé', declare: 'déclaré' }
const CALCULS: Record<string, string> = { simulateur: 'Une étude du simulateur', audit: 'Un pré-audit' }
const POSTES: Record<string, string> = {
  panneaux_eur: 'panneaux', carport_eur: 'carport', batterie_eur: 'batterie', inertie_eur: 'stockage par inertie',
  eolien_eur: 'éolienne',
}

// Le nom de rayon de chaque fiche `kb/` qu'un modèle cite (identifiants de `modeles.json`).
const FICHES: Record<string, string> = {
  dimensionnement_pv: 'Bien dimensionner ses panneaux', stockage_contrats: 'Stockage et contrats',
  action_pac_remplacement: 'Passer à la pompe à chaleur', pac_air_eau: 'La PAC air/eau', pac_air_air: 'La PAC air/air',
  action_ballon_thermodynamique: 'Le ballon thermodynamique', supports_securite: 'Supports et carport',
  eau: "L'eau de l'air", eolien: "L'éolien", jardin_hiver: "Le jardin d'hiver", baremes_aides: 'Les aides', urbanisme_assurance: 'Urbanisme et assurance',
  financement_projet: 'Financer son projet', choisir_installateur: "Choisir l'entreprise",
  garanties_travaux: 'Les garanties après travaux',
}

const euros = (n: number) => `${Math.round(n).toLocaleString('fr-FR')} €`

function Provenance({ source, statut, date }: { source: string | null; statut: string | null; date: string | null }) {
  if (!source) return null
  return (
    <span className="block text-xs text-dark/60">
      {SOURCES[source] ?? source}{date ? ` du ${dateFr(date)}` : ''}{statut ? ` · ${STATUTS[statut] ?? statut}` : ''}
    </span>
  )
}

function Chiffres({ p }: { p: Projet }) {
  const budget = p.budget_bas_eur === null ? null
    : p.budget_bas_eur === p.budget_haut_eur ? euros(p.budget_bas_eur)
      : `${euros(p.budget_bas_eur)} à ${euros(p.budget_haut_eur ?? p.budget_bas_eur)}`
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      <div className="rounded-lg bg-sable/60 px-3 py-2">
        <span className="block text-xs uppercase tracking-wide text-dark/50">Budget</span>
        <span className="block text-sm font-semibold text-ink">{budget ?? 'pas encore chiffré'}</span>
        <Provenance source={p.budget_source} statut={p.budget_statut} date={p.budget_date} />
      </div>
      <div className="rounded-lg bg-sable/60 px-3 py-2">
        <span className="block text-xs uppercase tracking-wide text-dark/50">Économie par an</span>
        <span className="block text-sm font-semibold text-ink">
          {p.economie_annuelle_eur === null ? 'pas encore chiffrée' : euros(p.economie_annuelle_eur)}
        </span>
        <Provenance source={p.economie_source} statut={p.economie_statut} date={p.economie_date} />
        {p.etude_ref?.perimetre_economie === 'ensemble' && (
          <span className="block text-xs text-terra">
            Pour toute l'étude, {(p.etude_ref.autres_postes ?? []).map((x) => POSTES[x] ?? x).join(' et ')} compris.
          </span>
        )}
      </div>
    </div>
  )
}

function FormTerminer({ p, documents, equipements, onFini }: {
  p: Projet; documents: Doc[]; equipements: Equipement[]; onFini: () => void
}) {
  const { authFetch } = useAuth()
  const proposes = p.modele?.equipements_crees ?? []
  const [d, setD] = useState({ date_reception: aujourdhui(), entreprise: '', montant_ttc: '', facture: '', attestation: '' })
  const [coches, setCoches] = useState<number[]>(proposes.map((_, i) => i))
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  async function envoyer(e: React.FormEvent) {
    e.preventDefault()
    setEnvoi(true)
    setErreur(null)
    const res = await authFetch(`/api/houses/me/projets/${p.id}/terminer`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date_reception: d.date_reception, entreprise: d.entreprise || null,
        montant_ttc: d.montant_ttc === '' ? null : Number(d.montant_ttc),
        facture_document_id: d.facture || null, attestation_assurance_document_id: d.attestation || null,
        equipements: coches,
      }),
    })
    setEnvoi(false)
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    signalerMaj()
    onFini()
  }

  const champ = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm'
  const remplace = (e: EquipementPropose) =>
    e.origine_fiche ? equipements.find((x) => x.en_service && x.origine_fiche === e.origine_fiche) : undefined
  return (
    <form onSubmit={envoyer} className="space-y-3 rounded-lg border border-primary/30 bg-cream/60 p-3">
      <p className="text-sm font-semibold text-ink">Les travaux sont terminés</p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="text-sm">Date de réception
          <input type="date" required max={aujourdhui()} value={d.date_reception}
            onChange={(e) => setD({ ...d, date_reception: e.target.value })} className={champ} />
        </label>
        <label className="text-sm">Entreprise
          <input value={d.entreprise} maxLength={120} onChange={(e) => setD({ ...d, entreprise: e.target.value })} className={champ} />
        </label>
        <label className="text-sm">Montant TTC (€)
          <input type="number" min={0} step="any" value={d.montant_ttc}
            onChange={(e) => setD({ ...d, montant_ttc: e.target.value })} className={champ} />
        </label>
        <label className="text-sm">Facture
          <select value={d.facture} onChange={(e) => setD({ ...d, facture: e.target.value })} className={champ}>
            <option value="">— aucune —</option>
            {documents.map((x) => <option key={x.id} value={x.id}>{x.filename}</option>)}
          </select>
        </label>
        <label className="text-sm sm:col-span-2">Attestation d'assurance décennale
          <select value={d.attestation} onChange={(e) => setD({ ...d, attestation: e.target.value })} className={champ}>
            <option value="">— aucune —</option>
            {documents.map((x) => <option key={x.id} value={x.id}>{x.filename}</option>)}
          </select>
        </label>
      </div>
      {proposes.length > 0 && (
        <fieldset>
          <legend className="mb-1 text-sm">À ajouter à vos équipements</legend>
          {proposes.map((e, i) => {
            const ancien = remplace(e)
            return (
              <label key={i} className="flex items-start gap-2 py-1 text-sm">
                <input type="checkbox" checked={coches.includes(i)} className="mt-0.5 h-4 w-4 accent-primary"
                  onChange={(ev) => setCoches(ev.target.checked ? [...coches, i] : coches.filter((x) => x !== i))} />
                <span>
                  {libelleType(e.categorie, e.type)}, posé le {dateFr(d.date_reception)}
                  {ancien && <span className="block text-xs text-dark/60">
                    remplace : {libelleType(ancien.categorie, ancien.type)}, qui passera dans vos anciens équipements
                  </span>}
                </span>
              </label>
            )
          })}
        </fieldset>
      )}
      <p className="text-xs text-dark/60">Le chantier, ses garanties et une entrée de journal seront créés en même temps.</p>
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={envoi}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50">
          {envoi ? 'Enregistrement…' : 'Enregistrer la réception'}
        </button>
        <button type="button" onClick={onFini}
          className="rounded-lg border border-bord px-4 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">Annuler</button>
      </div>
    </form>
  )
}

function FicheProjet({ id, documents, equipements, onFermer }: {
  id: string; documents: Doc[]; equipements: Equipement[]; onFermer: () => void
}) {
  const { authFetch } = useAuth()
  const [p, setP] = useState<Projet | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [montant, setMontant] = useState('')
  const [terminer, setTerminer] = useState(false)

  const charger = useCallback(() => {
    authFetch(`/api/houses/me/projets/${id}`).then((r) => (r.ok ? r.json() : null)).then(setP)
  }, [authFetch, id])
  useEffect(charger, [charger])

  async function ecrire(url: string, method: string, corps?: object) {
    setErreur(null)
    const res = await authFetch(url, {
      method, headers: { 'Content-Type': 'application/json' }, body: corps ? JSON.stringify(corps) : undefined,
    })
    if (!res.ok) { setErreur(await messageErreur(res)); return false }
    signalerMaj()
    charger()
    return true
  }

  if (!p) return null
  const clos = p.etape === 'termine' || p.etape === 'abandonne'
  const devis = documents.filter((x) => x.type === 'devis')
  const joints = p.devis_document_ids ?? []

  return (
    <div className="space-y-4 rounded-lg border border-bord bg-white p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-display text-lg text-ink">{p.titre}</p>
        <button onClick={onFermer} className="text-sm text-dark/60 hover:underline">Fermer</button>
      </div>

      {p.etape === 'termine' ? (
        <p className="text-sm text-leaf">Terminé : le chantier, ses garanties et les équipements sont dans votre carnet.</p>
      ) : (
        <label className="block text-sm">Étape
          <select value={p.etape} onChange={(e) => ecrire(`/api/houses/me/projets/${p.id}`, 'PATCH', { etape: e.target.value })}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm sm:w-64">
            {Object.entries(ETAPES).filter(([k]) => k !== 'termine').map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
      )}

      <Chiffres p={p} />

      {/* `outil: "aucun"` (jardin d'hiver ; machine à eau tant que le calculateur d'Hydrolia
          est en panne) : ni calcul à reprendre, ni outil vers lequel renvoyer. */}
      {!clos && p.modele?.outil === 'aucun' && (
        <p className="text-sm text-dark/70">Pas de calculateur pour ce projet : les fiches ci-dessous.</p>
      )}
      {!clos && p.modele?.outil !== 'aucun' && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <button onClick={() => ecrire(`/api/houses/me/projets/${p.id}/lier-etude`, 'POST')}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
            <RefreshCw className="h-4 w-4" /> Reprendre le dernier calcul
          </button>
          {p.modele?.outil_lien && (
            <Link to={p.modele.outil_lien} className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
              <Calculator className="h-4 w-4" /> Faire le calcul
            </Link>
          )}
        </div>
      )}

      {!clos && (
        <form className="flex flex-wrap items-end gap-2"
          onSubmit={async (e) => { e.preventDefault(); if (await ecrire(`/api/houses/me/projets/${p.id}`, 'PATCH', { devis_montant_eur: Number(montant) })) setMontant('') }}>
          <label className="text-sm">Montant d'un devis reçu (€)
            <input type="number" min={0} step="any" required value={montant} onChange={(e) => setMontant(e.target.value)}
              className="mt-1 w-40 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </label>
          <button type="submit" className="rounded-lg border border-primary px-3 py-2 text-sm font-semibold text-primary hover:bg-primary/5">
            Retenir ce montant
          </button>
        </form>
      )}

      <div>
        <p className="mb-1 text-sm font-semibold text-ink">Devis joints</p>
        {devis.length === 0 ? (
          <p className="text-xs text-dark/60">Déposez vos devis dans « Papiers » (type devis) pour les joindre ici.</p>
        ) : devis.map((x) => (
          <label key={x.id} className="flex items-center gap-2 py-0.5 text-sm">
            <input type="checkbox" disabled={p.etape === 'termine'} checked={joints.includes(x.id)} className="h-4 w-4 accent-primary"
              onChange={(e) => ecrire(`/api/houses/me/projets/${p.id}`, 'PATCH', {
                devis_document_ids: e.target.checked ? [...joints, x.id] : joints.filter((j) => j !== x.id),
              })} />
            {x.filename}
          </label>
        ))}
      </div>

      {(p.fiches ?? []).length > 0 && (
        <div>
          <p className="mb-1 text-sm font-semibold text-ink">Avant de signer</p>
          {/* Une fiche par sujet, repliée : ses questions dedans. Le nom est un titre de
              rayon, pas une explication — celles-ci sont dans les fiches. */}
          <ul className="divide-y divide-bord rounded-lg border border-bord">
            {(p.fiches ?? []).filter((f) => f.questions.length).map((f) => (
              <li key={f.source}>
                <details className="group px-3 py-2">
                  <summary className="cursor-pointer list-none text-sm text-ink marker:hidden">
                    {FICHES[f.source] ?? f.source} <span className="text-xs text-dark/50">· {f.questions.length}</span>
                  </summary>
                  <ul className="mt-1.5 space-y-1">
                    {f.questions.map((q) => (
                      <li key={q}><Link to={`/faq/${faqSlug(q)}`} className="text-sm text-primary hover:underline">{q}</Link></li>
                    ))}
                  </ul>
                </details>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!clos && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <Link to="/espace/mises-en-relation" className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
            Être mis en relation <ArrowRight className="h-4 w-4" />
          </Link>
          {!terminer && (
            <button onClick={() => setTerminer(true)}
              className="rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90">
              Les travaux sont terminés
            </button>
          )}
        </div>
      )}
      {terminer && <FormTerminer p={p} documents={documents} equipements={equipements} onFini={() => { setTerminer(false); charger() }} />}

      <label className="block text-sm">Note
        <textarea defaultValue={p.note ?? ''} rows={2} maxLength={2000}
          onBlur={(e) => { if (e.target.value !== (p.note ?? '')) ecrire(`/api/houses/me/projets/${p.id}`, 'PATCH', { note: e.target.value || null }) }}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
      </label>

      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <button onClick={() => { if (confirm(`Supprimer le projet « ${p.titre} » ? Ce qu'il a déjà ajouté au carnet y reste.`)) ecrire(`/api/houses/me/projets/${p.id}`, 'DELETE').then((ok) => ok && onFermer()) }}
        className="inline-flex items-center gap-1 text-xs text-dark/50 hover:text-terra">
        <Trash2 className="h-3.5 w-3.5" /> Supprimer le projet
      </button>
    </div>
  )
}

export default function MesProjets() {
  const { authFetch } = useAuth()
  const [projets, setProjets] = useState<Projet[]>([])
  const [modeles, setModeles] = useState<{ familles: string[]; modeles: Modele[] } | null>(null)
  const [documents, setDocuments] = useState<Doc[]>([])
  const [equipements, setEquipements] = useState<Equipement[]>([])
  const [ouvert, setOuvert] = useState<string | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  const charger = useCallback(() => {
    const json = (url: string) => authFetch(url).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
    Promise.all([json('/api/houses/me/projets'), json('/api/houses/me/projets/modeles'),
      json('/api/houses/me/documents'), json('/api/houses/me/equipements')])
      .then(([p, m, d, e]) => { setProjets(p); setModeles(m); setDocuments(d); setEquipements(e) })
      .catch(() => setModeles(null))
  }, [authFetch])
  useEffect(charger, [charger])
  useMaj(charger)

  async function envisager(modele_id: string) {
    setErreur(null)
    const res = await authFetch('/api/houses/me/projets', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ modele_id }),
    })
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    const p = await res.json()
    charger()
    setOuvert(p.id)
  }

  if (!modeles) return null
  const enCours = projets.filter((p) => EN_COURS.includes(p.etape))
  const clos = projets.filter((p) => !EN_COURS.includes(p.etape))

  const ligne = (p: Projet) => (
    <li key={p.id}>
      {ouvert === p.id ? (
        <FicheProjet id={p.id} documents={documents} equipements={equipements} onFermer={() => setOuvert(null)} />
      ) : (
        <button onClick={() => setOuvert(p.id)}
          className="flex w-full items-center justify-between gap-2 rounded-lg border border-bord px-3 py-2.5 text-left hover:border-primary">
          <span className="min-w-0">
            <span className="block text-sm font-semibold text-ink">{p.titre}</span>
            <span className="block text-xs text-dark/60">
              {p.budget_bas_eur === null ? 'pas encore chiffré'
                : `${euros(p.budget_bas_eur)}${p.budget_haut_eur !== p.budget_bas_eur && p.budget_haut_eur !== null ? ` à ${euros(p.budget_haut_eur)}` : ''} · ${SOURCES[p.budget_source ?? ''] ?? ''}`}
            </span>
          </span>
          <span className="shrink-0 rounded-full bg-cream px-2 py-0.5 text-xs font-semibold text-dark/70">{ETAPES[p.etape]}</span>
        </button>
      )}
    </li>
  )

  return (
    <section id="mes-projets" className="scroll-mt-20 rounded-xl border border-ink/10 bg-white p-4">
      <h2 className="mb-3 flex items-center gap-2 font-display text-xl text-ink">
        <FolderKanban className="h-5 w-5 text-primary" /> Mes projets
      </h2>
      {enCours.length === 0 && (
        <p className="mb-3 text-sm text-dark/70">
          Un projet suit une idée jusqu'à la réception des travaux, avec des chiffres qui disent toujours d'où ils viennent.
        </p>
      )}
      {enCours.length > 0 && <ul className="mb-3 space-y-2">{enCours.map(ligne)}</ul>}

      <Depliant titre="Envisager un projet" icone={<Plus className="h-4 w-4 text-primary" />} ouvert={projets.length === 0}
        resume={`${modeles.modeles.length}`}>
        {modeles.modeles.length === 0 ? (
          <p className="text-sm text-dark/70">Aucun projet de travaux n'est proposé pour votre logement.</p>
        ) : modeles.familles.map((f) => {
          const liste = modeles.modeles.filter((m) => m.famille === f)
          if (!liste.length) return null
          return (
            <div key={f}>
              <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-dark/50">{FAMILLES[f] ?? f}</h3>
              <ul className="grid gap-2 sm:grid-cols-2">
                {liste.map((m) => (
                  <li key={m.id}>
                    <button onClick={() => envisager(m.id)}
                      className="flex w-full flex-col items-start rounded-lg border border-bord px-3 py-2 text-left hover:border-primary hover:bg-cream">
                      <span className="text-sm font-semibold text-ink">{m.titre}</span>
                      <span className="text-xs text-dark/60">
                        {m.outil === 'aucun' ? 'Pas de calculateur : des fiches à lire'
                          : m.calcul ? `${CALCULS[m.calcul.type] ?? 'Un calcul'} du ${dateFr(m.calcul.date)} existe` : 'Pas encore de calcul'}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
        {erreur && <p className="text-sm text-terra">{erreur}</p>}
      </Depliant>

      {clos.length > 0 && (
        <div className="mt-3">
          <Depliant titre="Projets clos" resume={`${clos.length}`}>
            <ul className="space-y-2">{clos.map(ligne)}</ul>
          </Depliant>
        </div>
      )}
    </section>
  )
}
