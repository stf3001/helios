import { useEffect, useState, type FormEvent } from 'react'
import { useAuth } from '../../context/AuthContext'
import { dateFr } from '../carnet/libelles'
import Dossier, { Creneaux, JOURS, PLAGES, Score, type Creneau, type DossierLead, type LigneScore } from './Dossier'

/** Ce que le foyer transmet avec sa demande (série 4, lot 2). Rien n'est coché d'avance ; l'aperçu
 *  vient de l'API (`POST /leads/apercu`), qui passe par la même fonction que la création : ce qui
 *  s'affiche au-dessus de la case de consentement est exactement ce qui part. */
interface Partageable {
  contact: { nom: string; email: string; telephone: string | null }
  projets: { id: string; titre: string; etape: string }[]
  etudes: { audit: { id: string; date: string } | null; simulateur: { id: string; date: string } | null }
  documents: { id: string; type: string; filename: string }[]
  documents_max: number
}
interface Apercu { dossier: DossierLead; score: number; score_detail: LigneScore[]; creneaux: Creneau[] }

const champ = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm'

export default function FormulaireDemande({ partnerId, metier, consentement, onEnvoye }: {
  partnerId: string; metier: string; consentement: string; onEnvoye: () => void
}) {
  const { authFetch } = useAuth()
  const [base, setBase] = useState<Partageable | null>(null)
  const [fiche, setFiche] = useState(false)
  const [projetId, setProjetId] = useState('')
  const [etude, setEtude] = useState('')
  const [docs, setDocs] = useState<string[]>([])
  const [nom, setNom] = useState('')
  const [telephone, setTelephone] = useState('')
  const [email, setEmail] = useState('')
  const [creneaux, setCreneaux] = useState<string[]>([])
  const [message, setMessage] = useState('')
  const [apercu, setApercu] = useState<Apercu | null>(null)
  const [consent, setConsent] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)

  useEffect(() => {
    authFetch('/api/leads/partageable').then((r) => (r.ok ? r.json() : Promise.reject(new Error()))).then((b: Partageable) => {
      setBase(b); setNom(b.contact.nom); setEmail(b.contact.email)
    }).catch(() => setErreur('Vos informations sont momentanément indisponibles.'))
  }, [authFetch])

  const corps = {
    metier, message: message || null,
    partage: { fiche, projet_id: projetId || null, etude: etude || null, document_ids: docs },
    contact: { nom, email, telephone: telephone || null },
    creneaux: creneaux.map((c) => { const [jour, plage] = c.split('|'); return { jour, plage } }),
  }
  const cle = JSON.stringify(corps)
  const pret = creneaux.length > 0 && nom.trim() !== '' && email.includes('@')

  // L'aperçu suit chaque changement ; la case de consentement se décoche, puisque ce qu'elle
  // approuvait a changé.
  useEffect(() => {
    setConsent(false)
    if (!pret) { setApercu(null); return }
    const t = setTimeout(async () => {
      const r = await authFetch('/api/leads/apercu', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: cle })
      const b = await r.json().catch(() => null)
      if (r.ok) { setApercu(b); setErreur(null) } else {
        setApercu(null)
        setErreur(typeof b?.detail === 'string' ? b.detail : 'Vérifiez vos coordonnées.')
      }
    }, 300)
    return () => clearTimeout(t)
  }, [cle, pret, authFetch])

  async function envoyer(e: FormEvent) {
    e.preventDefault()
    setEnvoi(true); setErreur(null)
    const r = await authFetch('/api/leads', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...corps, partner_id: partnerId, type: 'travaux', consent }),
    })
    setEnvoi(false)
    if (r.ok) { onEnvoye(); return }
    const b = await r.json().catch(() => null)
    setErreur(typeof b?.detail === 'string' ? b.detail : 'Mise en relation impossible.')
  }

  const basculer = (liste: string[], v: string, max = Infinity) =>
    liste.includes(v) ? liste.filter((x) => x !== v) : liste.length < max ? [...liste, v] : liste

  if (!base) return erreur ? <p className="text-sm text-red-600">{erreur}</p> : <p className="text-sm text-gray-400">Chargement…</p>

  return (
    <form onSubmit={envoyer} className="space-y-6 rounded-xl border border-bord bg-white p-4">
      <fieldset className="space-y-2">
        <legend className="mb-1 text-sm font-semibold text-ink">Ce que vous transmettez</legend>
        <p className="text-xs text-dark/60">Toujours transmis : votre code postal, le type de logement, les travaux et votre message. Le reste, seulement si vous le cochez.</p>
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={fiche} onChange={(e) => setFiche(e.target.checked)} className="mt-1" />
          Le résumé de ma fiche maison (surface, année, chauffage, isolation, horizon et budget envisagés)</label>
        {base.projets.length > 0 && (
          <label className="block text-sm">Un projet de mon carnet
            <select value={projetId} onChange={(e) => setProjetId(e.target.value)} className={champ + ' mt-1 sm:w-96'}>
              <option value="">Aucun</option>
              {base.projets.map((p) => <option key={p.id} value={p.id}>{p.titre}</option>)}
            </select>
          </label>
        )}
        {(base.etudes.audit || base.etudes.simulateur) && (
          <label className="block text-sm">Mon dernier calcul
            <select value={etude} onChange={(e) => setEtude(e.target.value)} className={champ + ' mt-1 sm:w-96'}>
              <option value="">Aucun</option>
              {base.etudes.audit && <option value="audit">Pré-audit du {dateFr(base.etudes.audit.date.slice(0, 10))}</option>}
              {base.etudes.simulateur && <option value="simulateur">Étude du simulateur du {dateFr(base.etudes.simulateur.date.slice(0, 10))}</option>}
            </select>
          </label>
        )}
        {base.documents.length > 0 && (
          <div className="text-sm">
            <p>Des documents ({base.documents_max} au plus : devis, photos, DPE…)</p>
            <div className="mt-1 max-h-48 space-y-1 overflow-y-auto">
              {base.documents.map((d) => (
                <label key={d.id} className="flex items-center gap-2">
                  <input type="checkbox" checked={docs.includes(d.id)} disabled={!docs.includes(d.id) && docs.length >= base.documents_max}
                    onChange={() => setDocs(basculer(docs, d.id, base.documents_max))} />
                  <span className="min-w-0 truncate">{d.filename}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </fieldset>

      <fieldset className="grid gap-3 sm:grid-cols-3">
        <legend className="mb-1 text-sm font-semibold text-ink">Vos coordonnées</legend>
        <label className="text-sm">Nom<input value={nom} onChange={(e) => setNom(e.target.value)} className={champ + ' mt-1'} autoComplete="name" /></label>
        <label className="text-sm">Téléphone <span className="text-dark/50">(facultatif)</span>
          <input value={telephone} onChange={(e) => setTelephone(e.target.value)} className={champ + ' mt-1'} inputMode="tel" autoComplete="tel" /></label>
        <label className="text-sm">E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={champ + ' mt-1'} autoComplete="email" /></label>
        <p className="text-xs text-dark/60 sm:col-span-3">Sans téléphone, l'entreprise vous écrit.</p>
      </fieldset>

      <fieldset>
        <legend className="mb-1 text-sm font-semibold text-ink">Quand peut-on vous appeler ?</legend>
        <p className="mb-2 text-xs text-dark/60">L'entreprise ne vous appelle que dans ces créneaux. Au moins un.</p>
        <div className="overflow-x-auto">
          <table className="text-sm">
            <thead><tr><th />{PLAGES.map(([, l]) => <th key={l} className="px-2 font-normal text-dark/60">{l}</th>)}</tr></thead>
            <tbody>
              {JOURS.map(([j, lj]) => (
                <tr key={j}>
                  <th className="pr-3 text-left font-normal">{lj}</th>
                  {PLAGES.map(([p, lp]) => (
                    <td key={p} className="px-2 text-center">
                      <input type="checkbox" aria-label={`${lj} ${lp}`} checked={creneaux.includes(`${j}|${p}`)}
                        onChange={() => setCreneaux(basculer(creneaux, `${j}|${p}`))} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </fieldset>

      <label className="block text-sm font-semibold text-ink">Votre message
        <textarea value={message} onChange={(e) => setMessage(e.target.value)} maxLength={2000} rows={3}
          placeholder="Ce que vous attendez, vos questions…" className={champ + ' mt-1 font-normal'} /></label>

      <div className="rounded-xl border border-bord bg-sable p-4">
        <h3 className="mb-3 font-semibold text-ink">Exactement ce qui sera transmis</h3>
        {apercu ? (
          <div className="space-y-4">
            <Creneaux creneaux={apercu.creneaux} />
            <div className="text-sm"><span className="text-dark/60">Coordonnées : </span>{nom}{telephone && ` · ${telephone}`} · {email}</div>
            <Dossier dossier={apercu.dossier} />
            <Score score={apercu.score} detail={apercu.score_detail} />
            <p className="text-xs text-dark/60">Ce score aide l'entreprise à préparer son appel. Il ne change ni le prix, ni l'ordre des propositions, ni votre accès aux mises en relation.</p>
          </div>
        ) : <p className="text-sm text-dark/60">Indiquez vos coordonnées et au moins un créneau pour voir l'aperçu.</p>}
      </div>

      {apercu && (
        <label className="flex items-start gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
          <span>{consentement}</span>
        </label>
      )}
      {erreur && <p className="text-sm text-red-600">{erreur}</p>}
      <button type="submit" disabled={!apercu || !consent || envoi}
        className="rounded-xl bg-primary px-5 py-2.5 font-semibold text-white hover:opacity-90 disabled:opacity-40">
        {envoi ? 'Envoi…' : 'Demander la mise en relation'}
      </button>
    </form>
  )
}
