import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { AlertTriangle, Building2, CalendarClock, FileText, Flag, Upload } from 'lucide-react'
import PasswordInput from '../components/PasswordInput'
import Dossier, { Creneaux, Score, type Creneau, type DossierLead, type LigneScore } from '../components/mer/Dossier'
import {
  ETAT_JUSTIFICATIF, JUSTIFICATIFS, LIBELLE_JUSTIFICATIF, MOTIFS_CONTESTATION, STATUT_CONTESTATION, dateCourte,
} from '../components/mer/libelles'

/** Espace partenaire (mises en relation, lots 1 à 3). Le suivi déclaré ici ne change jamais le
 *  prix ; seule une contestation acceptée par l'administration rend une demande non facturable. */
interface ContestationP {
  motif: string; libelle: string; commentaire: string; essais: string[] | null; statut: string
  decision_motif: string | null; decidee_le: string | null; created_at: string
}
interface Suivi {
  statut: string; contacte_le: string | null; montant_travaux: number | null; motif_perdu: string | null
  facturable: boolean; prix_ht: number | null; fin_contestation: string; peut_contester: boolean
  contestation: ContestationP | null
}
interface PLead extends Suivi {
  id: string; type: string; metier: string | null; code_postal: string | null; consent_retire: boolean
  score: number | null; creneaux: Creneau[]; created_at: string
}
interface PDetail extends Suivi {
  id: string; creneaux: Creneau[]; message: string | null; score: number | null; score_detail: LigneScore[]
  contact: { nom: string | null; telephone: string | null; email: string | null }
  dossier: DossierLead | null; rappel_legal: string; consent_retire: boolean
}
interface Moi {
  raison_sociale: string; email: string; siret: string | null; zones: string[]; metiers: string[]; rge: boolean
  en_regle: boolean; alertes: string[]
  justificatifs: Record<string, { etat: string; date_fin: string | null; libelle: string }>
  documents: { id: string; type: string; filename: string; date_delivrance: string | null; date_fin: string | null
    statut: string; motif_refus: string | null; created_at: string }[]
  charte: { version: string | null; texte: string | null; version_signee: string | null; signee_le: string | null }
}

const STATUT_LABEL: Record<string, string> = {
  transmis: 'Transmis', contacte: 'Contacté', devis: 'Devis', signe: 'Signé', perdu: 'Sans suite',
}
const METIER_LABEL: Record<string, string> = {
  solaire: 'Panneaux solaires', pv: 'Photovoltaïque', pac: 'Pompe à chaleur', isolation: 'Isolation',
  eau: "Machine à eau de l'air", eolien: 'Éolienne', inertie: 'Stockage par inertie',
  menuiseries: 'Menuiseries', vmc: 'Ventilation', regulation: 'Régulation',
}
const JOUR: Record<string, string> = { lundi: 'lun.', mardi: 'mar.', mercredi: 'mer.', jeudi: 'jeu.', vendredi: 'ven.', samedi: 'sam.' }
const PLAGE: Record<string, string> = { matin: 'matin', midi: 'midi', apres_midi: 'après-midi', soir: 'soir' }
const TOKEN_KEY = 'helios_partner_token'
const champ = 'rounded-lg border border-gray-300 px-3 py-2 text-sm'
const btn = 'text-xs rounded-lg border border-gray-300 bg-white px-3 py-1.5 hover:bg-gray-50'
const aujourdhui = () => new Date().toLocaleDateString('sv-SE')

type PFetch = (path: string, init?: RequestInit) => Promise<Response>

async function erreurDe(r: Response, defaut: string): Promise<string> {
  const b = await r.json().catch(() => null)
  return typeof b?.detail === 'string' ? b.detail : defaut
}

export default function PartnerPortal() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [moi, setMoi] = useState<Moi | null>(null)
  const [leads, setLeads] = useState<PLead[]>([])
  const [onglet, setOnglet] = useState<'demandes' | 'entreprise'>('demandes')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const pFetch: PFetch = useCallback((path, init) =>
    fetch(path, { ...init, headers: { ...(init?.headers || {}), Authorization: `Bearer ${token}` } }), [token])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null); setLeads([]); setMoi(null)
  }, [])

  const charger = useCallback(() => {
    if (!token) return
    pFetch('/api/partner/leads').then((r) => {
      if (r.status === 401) { logout(); return [] }
      return r.ok ? r.json() : []
    }).then(setLeads)
    pFetch('/api/partner/me').then((r) => (r.ok ? r.json() : null)).then(setMoi)
  }, [token, pFetch, logout])
  useEffect(charger, [charger])

  async function login(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const res = await fetch('/api/partner/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }),
    })
    if (!res.ok) { setError('Identifiants invalides.'); return }
    const data = await res.json()
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setToken(data.access_token)
  }

  if (!token) {
    return (
      <section className="max-w-sm mx-auto px-4 py-16">
        <div className="flex items-center gap-2 mb-6">
          <Building2 className="w-7 h-7 text-primary" />
          <h1 className="text-2xl font-bold">Espace partenaire</h1>
        </div>
        <form onSubmit={login} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Mot de passe</label>
            <PasswordInput required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <button type="submit" className="w-full rounded-xl bg-primary text-white font-semibold px-4 py-2.5 hover:opacity-90">
            Se connecter
          </button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </form>
        <p className="text-xs text-gray-400 mt-6">
          Vous n'êtes pas encore partenaire ? Faites votre demande sur la page « Devenir partenaire ».
          Votre premier accès se fait par le lien d'activation que nous vous transmettons.
        </p>
      </section>
    )
  }

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex min-w-0 items-center gap-2">
          <Building2 className="w-7 h-7 shrink-0 text-primary" />
          <h1 className="truncate text-2xl font-bold">{moi?.raison_sociale ?? 'Espace partenaire'}</h1>
        </div>
        <button onClick={logout} className="shrink-0 text-sm text-gray-500 hover:text-primary">Déconnexion</button>
      </div>

      {moi && moi.alertes.length > 0 && (
        <div role="alert" className={'mb-5 rounded-xl border p-3 text-sm '
          + (moi.en_regle ? 'border-sun/50 bg-sun/10 text-dark/80' : 'border-primary/40 bg-primary/5 text-ink')}>
          <p className="mb-1 flex items-center gap-1.5 font-semibold">
            <AlertTriangle className="h-4 w-4 text-primary" />
            {moi.en_regle ? 'À prévoir' : 'Vous ne recevez plus de nouvelles demandes'}
          </p>
          <ul className="list-disc space-y-0.5 pl-5">{moi.alertes.map((a) => <li key={a}>{a}</li>)}</ul>
          {!moi.en_regle && onglet !== 'entreprise' && (
            <button onClick={() => setOnglet('entreprise')} className="mt-2 text-primary underline">Mettre à jour mon entreprise</button>
          )}
        </div>
      )}

      <div className="mb-5 flex gap-2 border-b border-bord" role="tablist">
        {([['demandes', `Mes demandes (${leads.length})`], ['entreprise', 'Mon entreprise']] as const).map(([k, l]) => (
          <button key={k} role="tab" aria-selected={onglet === k} onClick={() => setOnglet(k)}
            className={'-mb-px border-b-2 px-3 py-2 text-sm ' + (onglet === k ? 'border-primary font-semibold text-ink' : 'border-transparent text-dark/60')}>
            {l}
          </button>
        ))}
      </div>

      {onglet === 'demandes'
        ? (leads.length === 0
          ? <p className="text-gray-400">Aucune demande reçue pour l'instant.</p>
          : <div className="space-y-3">{leads.map((l) => <Demande key={l.id} lead={l} pFetch={pFetch} onMaj={charger} />)}</div>)
        : moi && <Entreprise moi={moi} pFetch={pFetch} onMaj={charger} />}
    </section>
  )
}

function Demande({ lead: l, pFetch, onMaj }: { lead: PLead; pFetch: PFetch; onMaj: () => void }) {
  const [ouvert, setOuvert] = useState<PDetail | null>(null)
  const [panneau, setPanneau] = useState<'suivi' | 'contester' | null>(null)

  async function ouvrir() {
    if (ouvert) { setOuvert(null); return }
    const r = await pFetch(`/api/partner/leads/${l.id}`)
    if (r.ok) setOuvert(await r.json())
  }

  async function telecharger(docId: string, nom: string) {
    const r = await pFetch(`/api/partner/leads/${l.id}/documents/${docId}`)
    if (!r.ok) return
    const url = URL.createObjectURL(await r.blob())
    const a = document.createElement('a')
    a.href = url; a.download = nom; a.click()
    URL.revokeObjectURL(url)
  }

  const fini = l.statut === 'signe' || l.statut === 'perdu' || l.consent_retire
  return (
    <div className="border border-gray-200 rounded-xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
        <div className="font-medium">{l.metier ? (METIER_LABEL[l.metier] ?? l.metier) : 'Travaux'} · {l.code_postal}</div>
        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">{STATUT_LABEL[l.statut] ?? l.statut}</span>
      </div>
      <div className="text-xs text-gray-500 mb-2">
        Reçue le {dateCourte(l.created_at)}
        {l.prix_ht != null && <> · {l.prix_ht.toLocaleString('fr-FR')} € HT{!l.facturable && <span className="text-leaf"> · non facturable</span>}</>}
        {l.score != null && <> · score {l.score}/100</>}
        {l.contacte_le && <> · contacté le {dateCourte(l.contacte_le)}</>}
        {l.montant_travaux != null && <> · {l.montant_travaux.toLocaleString('fr-FR')} € HT de travaux déclarés</>}
        {l.consent_retire && <span className="text-red-500"> · consentement retiré</span>}
      </div>
      {l.creneaux.length > 0 && !l.consent_retire && (
        <p className="mb-2 flex items-center gap-1.5 text-xs text-ink">
          <CalendarClock className="h-3.5 w-3.5 shrink-0" /> À appeler : {l.creneaux.map((c) => `${JOUR[c.jour]} ${PLAGE[c.plage]}`).join(' · ')}
        </p>
      )}
      {l.contestation && (
        <p className="mb-2 text-xs text-dark/70">
          <Flag className="mr-1 inline h-3.5 w-3.5" />Contestée ({l.contestation.libelle}) — {STATUT_CONTESTATION[l.contestation.statut]}
          {l.contestation.decision_motif && <> : {l.contestation.decision_motif}</>}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button onClick={ouvrir} className={btn}>{ouvert ? 'Fermer le dossier' : 'Voir le dossier'}</button>
        {!fini && <button onClick={() => setPanneau(panneau === 'suivi' ? null : 'suivi')} className={btn}>Déclarer le suivi</button>}
        {l.peut_contester && (
          <button onClick={() => setPanneau(panneau === 'contester' ? null : 'contester')} className={btn}>
            Contester (jusqu'au {dateCourte(l.fin_contestation)})
          </button>
        )}
      </div>
      {panneau === 'suivi' && <FormSuivi lead={l} pFetch={pFetch} onFait={() => { setPanneau(null); onMaj() }} />}
      {panneau === 'contester' && <FormContester lead={l} pFetch={pFetch} onFait={() => { setPanneau(null); onMaj() }} />}
      {ouvert && (
        ouvert.dossier ? (
          <div className="mt-3 space-y-4 rounded-xl border border-bord bg-sable p-4">
            <Creneaux creneaux={ouvert.creneaux} />
            <p className="text-xs text-dark/70">{ouvert.rappel_legal}</p>
            <div className="text-sm"><span className="text-dark/60">Contact : </span>
              {ouvert.contact.nom}{ouvert.contact.telephone && ` · ${ouvert.contact.telephone}`} · {ouvert.contact.email}</div>
            <Dossier dossier={ouvert.dossier} lienDocument={(docId) => {
              const d = ouvert.dossier?.documents?.find((x) => x.id === docId)
              if (d) telecharger(docId, d.filename)
            }} />
            {ouvert.score != null && <Score score={ouvert.score} detail={ouvert.score_detail} />}
          </div>
        ) : <p className="mt-3 text-sm text-gray-500">Aucun dossier : le foyer a retiré son consentement, ou la demande précède les dossiers.</p>
      )}
    </div>
  )
}

function FormSuivi({ lead, pFetch, onFait }: { lead: PLead; pFetch: PFetch; onFait: () => void }) {
  const [statut, setStatut] = useState(lead.statut === 'transmis' ? 'contacte' : 'devis')
  const [jour, setJour] = useState(aujourdhui())
  const [montant, setMontant] = useState('')
  const [motif, setMotif] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)

  async function envoyer(e: FormEvent) {
    e.preventDefault()
    const corps: Record<string, unknown> = { statut }
    if (statut === 'contacte') corps.contacte_le = jour
    if ((statut === 'devis' || statut === 'signe') && montant) corps.montant_travaux = Number(montant)
    if (statut === 'perdu') corps.motif_perdu = motif
    const r = await pFetch(`/api/partner/leads/${lead.id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
    })
    if (r.ok) onFait(); else setErreur(await erreurDe(r, 'Suivi impossible.'))
  }

  return (
    <form onSubmit={envoyer} className="mt-3 space-y-2 rounded-xl border border-bord bg-cream/50 p-3 text-sm">
      <div className="flex flex-wrap gap-3">
        {[['contacte', 'Contacté'], ['devis', 'Devis envoyé'], ['signe', 'Signé'], ['perdu', 'Sans suite']].map(([v, lbl]) => (
          <label key={v} className="flex items-center gap-1.5">
            <input type="radio" name={`suivi-${lead.id}`} checked={statut === v} onChange={() => setStatut(v)} /> {lbl}
          </label>
        ))}
      </div>
      {statut === 'contacte' && (
        <label className="block">Date du contact
          <input type="date" value={jour} max={aujourdhui()} onChange={(e) => setJour(e.target.value)} className={champ + ' ml-2'} />
        </label>
      )}
      {(statut === 'devis' || statut === 'signe') && (
        <label className="block">Montant des travaux HT <span className="text-dark/50">(facultatif)</span>
          <input type="number" min={0} value={montant} onChange={(e) => setMontant(e.target.value)} className={champ + ' ml-2 w-36'} />
        </label>
      )}
      {statut === 'perdu' && (
        <label className="block">Pourquoi ?
          <input value={motif} onChange={(e) => setMotif(e.target.value)} required className={champ + ' mt-1 w-full'} />
        </label>
      )}
      <p className="text-xs text-dark/60">Ce suivi sert aux statistiques et informe le foyer. Il ne change jamais le prix.</p>
      {erreur && <p className="text-red-600">{erreur}</p>}
      <button type="submit" className="rounded-xl bg-primary px-4 py-1.5 font-semibold text-white">Enregistrer</button>
    </form>
  )
}

function FormContester({ lead, pFetch, onFait }: { lead: PLead; pFetch: PFetch; onFait: () => void }) {
  const [motif, setMotif] = useState('')
  const [commentaire, setCommentaire] = useState('')
  const [essais, setEssais] = useState(['', '', ''])
  const [erreur, setErreur] = useState<string | null>(null)

  async function envoyer(e: FormEvent) {
    e.preventDefault()
    const r = await pFetch(`/api/partner/leads/${lead.id}/contestation`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ motif, commentaire, essais: motif === 'injoignable' ? essais.filter(Boolean) : [] }),
    })
    if (r.ok) onFait(); else setErreur(await erreurDe(r, 'Contestation impossible.'))
  }

  return (
    <form onSubmit={envoyer} className="mt-3 space-y-2 rounded-xl border border-bord bg-cream/50 p-3 text-sm">
      <p className="text-xs text-dark/70">
        Possible jusqu'au {dateCourte(lead.fin_contestation)}. L'administration tranche ; acceptée, la demande n'est pas facturée.
      </p>
      <fieldset className="space-y-1">
        {MOTIFS_CONTESTATION.map(([v, lbl]) => (
          <label key={v} className="flex items-start gap-1.5">
            <input type="radio" name={`motif-${lead.id}`} checked={motif === v} onChange={() => setMotif(v)} className="mt-1" /> {lbl}
          </label>
        ))}
      </fieldset>
      {motif === 'injoignable' && (
        <div>
          <p>Dates de vos trois essais, dans les créneaux du foyer :</p>
          <div className="mt-1 flex flex-wrap gap-2">
            {essais.map((d, i) => (
              <input key={i} type="date" value={d} max={aujourdhui()} aria-label={`Essai ${i + 1}`} required
                onChange={(e) => setEssais(essais.map((x, j) => (j === i ? e.target.value : x)))} className={champ} />
            ))}
          </div>
        </div>
      )}
      <label className="block">Commentaire (obligatoire)
        <textarea value={commentaire} onChange={(e) => setCommentaire(e.target.value)} required rows={2} maxLength={2000}
          className={champ + ' mt-1 w-full'} />
      </label>
      {erreur && <p className="text-red-600">{erreur}</p>}
      <button type="submit" disabled={!motif || !commentaire.trim()}
        className="rounded-xl bg-primary px-4 py-1.5 font-semibold text-white disabled:opacity-40">Envoyer la contestation</button>
    </form>
  )
}

function Entreprise({ moi, pFetch, onMaj }: { moi: Moi; pFetch: PFetch; onMaj: () => void }) {
  const [erreur, setErreur] = useState<string | null>(null)
  const [lu, setLu] = useState(false)
  const types = JUSTIFICATIFS.filter(([t]) => t !== 'rge' || moi.rge)
  const aSigner = moi.charte.version && moi.charte.version !== moi.charte.version_signee

  async function signer() {
    setErreur(null)
    const r = await pFetch('/api/partner/charte', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ version: moi.charte.version }),
    })
    if (r.ok) onMaj(); else setErreur(await erreurDe(r, 'Signature impossible.'))
  }

  async function ouvrir(id: string) {
    const r = await pFetch(`/api/partner/documents/${id}`)
    if (r.ok) window.open(URL.createObjectURL(await r.blob()), '_blank')
  }

  return (
    <div className="space-y-8">
      <div className="space-y-1 text-sm text-dark/80">
        <p className="break-words">{moi.email}{moi.siret && <> · SIRET {moi.siret}</>}</p>
        <p>Métiers : {moi.metiers.map((m) => METIER_LABEL[m] ?? m).join(', ') || '—'} · Départements : {moi.zones.join(', ') || '—'}</p>
        <p className={moi.en_regle ? 'text-leaf' : 'text-primary'}>
          {moi.en_regle ? 'Vous êtes proposé aux foyers de vos zones et métiers (tirage au sort).' : "Vous n'êtes pas proposé aux foyers pour l'instant."}
        </p>
      </div>

      <section>
        <h2 className="mb-2 text-xl text-ink">Justificatifs</h2>
        <div className="space-y-3">
          {types.map(([t, libelle]) => {
            const e = moi.justificatifs[t]
            return (
              <div key={t} className="rounded-xl border border-gray-200 p-3">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-medium">{libelle}</span>
                  {e && <span className={'rounded-full border px-2 py-0.5 text-xs ' + ETAT_JUSTIFICATIF[e.etat].style}>
                    {ETAT_JUSTIFICATIF[e.etat].label}{e.date_fin && ` · jusqu'au ${dateCourte(e.date_fin)}`}
                  </span>}
                </div>
                <Depot type={t} pFetch={pFetch} onFait={onMaj} />
              </div>
            )
          })}
        </div>
        {moi.documents.length > 0 && (
          <ul className="mt-3 space-y-1 text-xs text-dark/70">
            {moi.documents.map((d) => (
              <li key={d.id}>
                <button onClick={() => ouvrir(d.id)} className="underline"><FileText className="mr-1 inline h-3.5 w-3.5" />{d.filename}</button>
                {' '}— {LIBELLE_JUSTIFICATIF[d.type]}, déposé le {dateCourte(d.created_at)}
                {d.statut === 'refuse' && <span className="text-primary"> · refusé : {d.motif_refus}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-xl text-ink">Charte partenaire</h2>
        {!moi.charte.version ? (
          <p className="text-sm text-dark/70">La charte est en cours de relecture. Vous pourrez la signer ici dès qu'elle sera en vigueur.</p>
        ) : (
          <>
            <p className="mb-2 text-sm">
              Version en vigueur : <strong>{moi.charte.version}</strong>.{' '}
              {moi.charte.version_signee
                ? <>Vous avez signé la {moi.charte.version_signee} le {dateCourte(moi.charte.signee_le)}.</>
                : 'Pas encore signée.'}
            </p>
            <div className="max-h-96 space-y-2 overflow-y-auto rounded-xl border border-bord bg-white p-4 text-sm text-dark/85">
              <TexteCharte texte={moi.charte.texte ?? ''} />
            </div>
            {aSigner && (
              <div className="mt-3 space-y-2 text-sm">
                <label className="flex items-start gap-2">
                  <input type="checkbox" checked={lu} onChange={(e) => setLu(e.target.checked)} className="mt-1" />
                  J'ai lu la charte {moi.charte.version} et je m'engage à la respecter au nom de {moi.raison_sociale}.
                </label>
                <button disabled={!lu} onClick={signer} className="rounded-xl bg-primary px-4 py-2 font-semibold text-white disabled:opacity-40">
                  Signer la charte {moi.charte.version}
                </button>
              </div>
            )}
            {erreur && <p className="mt-2 text-sm text-red-600">{erreur}</p>}
          </>
        )}
      </section>
    </div>
  )
}

function Depot({ type, pFetch, onFait }: { type: string; pFetch: PFetch; onFait: () => void }) {
  const [fichier, setFichier] = useState<File | null>(null)
  const [jour, setJour] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)
  const [cle, setCle] = useState(0)

  async function deposer(e: FormEvent) {
    e.preventDefault()
    if (!fichier) return
    const corps = new FormData()
    corps.append('type', type); corps.append('fichier', fichier)
    corps.append(type === 'kbis' ? 'date_delivrance' : 'date_fin', jour)
    const r = await pFetch('/api/partner/documents', { method: 'POST', body: corps })
    if (r.ok) { setFichier(null); setJour(''); setErreur(null); setCle((k) => k + 1); onFait() }
    else setErreur(await erreurDe(r, 'Dépôt impossible.'))
  }

  return (
    <form onSubmit={deposer} className="mt-2 flex flex-wrap items-end gap-2 text-sm">
      <input key={cle} type="file" accept="application/pdf,image/jpeg,image/png,image/webp" aria-label={`Fichier ${LIBELLE_JUSTIFICATIF[type]}`}
        onChange={(e) => setFichier(e.target.files?.[0] ?? null)} className="min-w-0 max-w-full text-sm" />
      <label>{type === 'kbis' ? 'Délivré le' : "Valable jusqu'au"}
        <input type="date" value={jour} onChange={(e) => setJour(e.target.value)} required className={champ + ' ml-2'} />
      </label>
      <button type="submit" disabled={!fichier || !jour} className={btn + ' flex items-center gap-1 disabled:opacity-40'}>
        <Upload className="h-3.5 w-3.5" /> Déposer
      </button>
      {erreur && <p className="w-full text-red-600">{erreur}</p>}
    </form>
  )
}

/** Le texte de la charte est du Markdown simple (`kb/charte_partenaire.md`) : titres, listes
 *  numérotées et gras. Ce rendu minimal suffit, sans dépendance. */
function TexteCharte({ texte }: { texte: string }) {
  const gras = (ligne: string) => ligne.split(/\*\*(.+?)\*\*/g).map((m, i) => (i % 2 ? <strong key={i}>{m}</strong> : m))
  const blocs = texte.split(/\n\s*\n/).map((b) => b.replace(/\s*\n\s*/g, ' ').trim()).filter(Boolean)
  return (
    <>
      {blocs.map((b, i) => b.startsWith('# ')
        ? <h3 key={i} className="text-lg text-ink">{b.slice(2)}</h3>
        : b.startsWith('## ')
          ? <h4 key={i} className="pt-2 text-base text-ink">{b.slice(3)}</h4>
          : <p key={i}>{gras(b)}</p>)}
    </>
  )
}
