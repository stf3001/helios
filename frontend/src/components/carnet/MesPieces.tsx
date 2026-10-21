import { useCallback, useEffect, useRef, useState } from 'react'
import { LayoutGrid, Plus, Trash2, Pencil, Camera, ImageIcon } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import ApiError from '../ApiError'
import FieldInput from '../fiche/FieldInput'
import type { Draft, FieldSpec, FieldValue } from '../fiche/types'
import { messageErreur } from './Formulaires'
import { libelleType } from './libelles'
import {
  type Emetteur, NIVEAUX, ORIENTATIONS, TYPES_EMETTEUR, TYPES_PIECE, libelleEmetteur, libelleNiveau, phraseEmetteurs,
} from './libellesPieces'

/**
 * Carnet de maison, lot 2 : « Mes pièces ».
 *
 * Saisie DÉCLARATIVE ; le résumé additionne et compare (`services/pieces.py`), il ne
 * calcule ni déperdition ni puissance nécessaire. Un écart avec la fiche est signalé,
 * jamais corrigé. La photo d'une pièce est stockée, jamais analysée.
 */

type Piece = {
  id: string; nom: string; type: string; niveau: number; surface_m2: number | null; chauffee: boolean
  orientation: string | null; note: string | null; emetteurs: Emetteur[]; photo: { id: string; filename: string } | null
}
type Valeur<T> = { valeur: T; statut: 'declare' | 'calcule' }
type Ecart = { message: string; statut: string }
type Resume = {
  nb_pieces: Valeur<number>; nb_chauffees: Valeur<number>
  surface_pieces_m2: Valeur<number | null> & { pieces_sans_surface: number }
  ecart_surface: Ecart | null; ecart_clim: Ecart | null
  emetteurs_par_type: { type: string; nombre: number; puissance_totale_w: number | null }[]
  chauffees_sans_emetteur: Valeur<string[]>
}
export type EquipementCourt = { id: string; categorie: string; type: string; marque: string | null; en_service: boolean }

const CHAMPS_PIECE = ['nom', 'type', 'niveau', 'surface_m2', 'chauffee', 'orientation', 'note']
const CHAMPS_EMETTEUR = ['type', 'nombre', 'puissance_w', 'robinet_thermostatique', 'programmable', 'equipement_id', 'note']

function corps(d: Draft, champs: string[]) {
  const sortie: Record<string, FieldValue> = {}
  for (const k of champs) if (k in d) sortie[k] = d[k] === '' ? null : d[k]
  if (typeof sortie.niveau === 'string') sortie.niveau = Number(sortie.niveau)
  return sortie
}

const bouton = 'rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50'
const boutonDiscret = 'rounded-lg border border-bord px-3.5 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary'
const icone = 'rounded p-1.5 text-dark/50 hover:bg-cream hover:text-primary'

/** La vignette se charge avec le jeton : une balise <img src> nue n'en porterait pas. */
function Vignette({ docId, taille = 'h-12 w-12' }: { docId: string | null; taille?: string }) {
  const { authFetch } = useAuth()
  const [url, setUrl] = useState<string | null>(null)
  useEffect(() => {
    if (!docId) { setUrl(null); return }
    let lien: string | null = null
    let actif = true
    authFetch(`/api/houses/me/documents/${docId}`).then((r) => (r.ok ? r.blob() : null)).then((b) => {
      if (b && actif) { lien = URL.createObjectURL(b); setUrl(lien) }
    })
    return () => { actif = false; if (lien) URL.revokeObjectURL(lien) }
  }, [docId, authFetch])
  return url
    ? <img src={url} alt="" className={`${taille} shrink-0 rounded-md border border-bord object-cover`} />
    : <span className={`${taille} flex shrink-0 items-center justify-center rounded-md border border-dashed border-bord text-dark/30`}>
        <ImageIcon className="h-5 w-5" />
      </span>
}

function Grille({ specs, draft, set }: { specs: FieldSpec[]; draft: Draft; set: (k: string, v: FieldValue) => void }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {specs.map((s) => (
        <div key={s.key} className={s.type === 'textarea' ? 'sm:col-span-2' : ''}>
          <FieldInput spec={s} value={draft[s.key]} onChange={(v) => set(s.key, v)} />
        </div>
      ))}
    </div>
  )
}

const SPECS_PIECE: FieldSpec[] = [
  { key: 'nom', label: 'Nom', type: 'text' },
  { key: 'type', label: 'Type de pièce', type: 'select', options: TYPES_PIECE },
  { key: 'niveau', label: 'Niveau', type: 'select', options: NIVEAUX },
  { key: 'surface_m2', label: 'Surface (m²)', type: 'number', min: 0, step: 'any' },
  { key: 'chauffee', label: 'Pièce chauffée ?', type: 'boolean' },
  { key: 'orientation', label: 'Orientation principale', type: 'select', options: ORIENTATIONS },
  { key: 'note', label: 'Note', type: 'textarea' },
]

function FormPiece({ initial, enregistrer, onAnnuler }: {
  initial: Draft; enregistrer: (d: Draft) => Promise<string | null>; onAnnuler?: () => void
}) {
  const [draft, setDraft] = useState<Draft>(initial)
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  return (
    <form className="space-y-3" onSubmit={async (e) => {
      e.preventDefault()
      if (!draft.nom || !draft.type) { setErreur('Donnez un nom et un type à la pièce.'); return }
      setEnvoi(true); setErreur(await enregistrer(draft)); setEnvoi(false)
    }}>
      <Grille specs={SPECS_PIECE} draft={draft} set={(k, v) => setDraft((d) => ({ ...d, [k]: v }))} />
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={envoi} className={bouton}>{envoi ? 'Enregistrement…' : 'Enregistrer la pièce'}</button>
        {onAnnuler && <button type="button" onClick={onAnnuler} className={boutonDiscret}>Annuler</button>}
      </div>
    </form>
  )
}

function FormEmetteur({ initial, equipements, enregistrer, onAnnuler }: {
  initial: Draft; equipements: EquipementCourt[]
  enregistrer: (d: Draft) => Promise<string | null>; onAnnuler: () => void
}) {
  const [draft, setDraft] = useState<Draft>(initial)
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  // Ce qui produit la chaleur ou le froid d'un émetteur : un ballon ou des panneaux n'en sont pas.
  const sources = equipements.filter((e) => e.categorie === 'chauffage' || e.categorie === 'clim')
  const specs: FieldSpec[] = [
    { key: 'type', label: 'Émetteur', type: 'select', options: TYPES_EMETTEUR },
    { key: 'nombre', label: 'Combien ?', type: 'number', min: 1, max: 50 },
    { key: 'puissance_w', label: 'Puissance par unité (W)', type: 'number', min: 0, step: 'any', help: 'Sur la plaque, si vous la connaissez' },
    ...(draft.type === 'radiateur_eau'
      ? [{ key: 'robinet_thermostatique', label: 'Robinets thermostatiques ?', type: 'boolean' as const }] : []),
    { key: 'programmable', label: 'Programmable ?', type: 'boolean' },
    ...(sources.length ? [{ key: 'equipement_id', label: 'Alimenté par', type: 'select' as const,
      options: sources.map((e) => ({ value: e.id, label: [libelleType(e.categorie, e.type), e.marque].filter(Boolean).join(' · ') })) }] : []),
  ]
  return (
    <form className="space-y-3 rounded-lg border border-primary/40 bg-cream/60 p-3" onSubmit={async (e) => {
      e.preventDefault()
      if (!draft.type) { setErreur("Choisissez le type d'émetteur."); return }
      setEnvoi(true); setErreur(await enregistrer(draft)); setEnvoi(false)
    }}>
      <Grille specs={specs} draft={draft} set={(k, v) => setDraft((d) => ({ ...d, [k]: v }))} />
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="submit" disabled={envoi} className={bouton}>{envoi ? 'Enregistrement…' : 'Enregistrer'}</button>
        <button type="button" onClick={onAnnuler} className={boutonDiscret}>Annuler</button>
      </div>
    </form>
  )
}

/** « Combien de chambres ? Une salle de bain ou deux ? » — séjour et cuisine sont d'office. */
function Demarrage({ creer }: { creer: (pieces: Draft[]) => Promise<string | null> }) {
  const [chambres, setChambres] = useState(2)
  const [sdb, setSdb] = useState(1)
  const [wc, setWc] = useState(1)
  const [extras, setExtras] = useState<string[]>([])
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState(false)
  const EXTRAS = [['entree', 'Entrée'], ['bureau', 'Bureau'], ['buanderie', 'Buanderie'], ['garage', 'Garage']]
  const nombre = (label: string, valeur: number, set: (n: number) => void, max: number) => (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{label}</span>
      <select value={valeur} onChange={(e) => set(Number(e.target.value))}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
        {Array.from({ length: max + 1 }, (_, i) => <option key={i} value={i}>{i}</option>)}
      </select>
    </label>
  )

  async function valider() {
    const numerote = (n: number, type: string, nom: string) =>
      Array.from({ length: n }, (_, i) => ({ type, nom: n > 1 ? `${nom} ${i + 1}` : nom }))
    const pieces: Draft[] = [
      { type: 'sejour', nom: 'Séjour' }, { type: 'cuisine', nom: 'Cuisine' },
      ...numerote(chambres, 'chambre', 'Chambre'), ...numerote(sdb, 'salle_de_bain', 'Salle de bain'),
      ...numerote(wc, 'wc', 'WC'),
      ...EXTRAS.filter(([t]) => extras.includes(t)).map(([t, nom]) => ({ type: t, nom, chauffee: t !== 'garage' })),
    ]
    setEnvoi(true); setErreur(await creer(pieces)); setEnvoi(false)
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-dark/70">
        Décrivez votre maison en quelques clics : on crée les pièces, vous les affinez ensuite.
      </p>
      <div className="grid grid-cols-3 gap-3">
        {nombre('Chambres', chambres, setChambres, 8)}
        {nombre('Salles de bain', sdb, setSdb, 4)}
        {nombre('WC', wc, setWc, 4)}
      </div>
      <div className="flex flex-wrap gap-2">
        {EXTRAS.map(([t, label]) => {
          const choisi = extras.includes(t)
          return (
            <button key={t} type="button" onClick={() => setExtras((x) => (choisi ? x.filter((y) => y !== t) : [...x, t]))}
              className={'rounded-full border px-3 py-1.5 text-sm transition-colors ' +
                (choisi ? 'border-primary bg-primary text-white' : 'border-bord bg-white text-dark/70 hover:border-primary')}>
              {label}
            </button>
          )
        })}
      </div>
      {erreur && <p className="text-sm text-terra">{erreur}</p>}
      <button onClick={valider} disabled={envoi} className={bouton}>
        {envoi ? 'Création…' : `Créer mes ${2 + chambres + sdb + wc + extras.length} pièces`}
      </button>
    </div>
  )
}

function LignePiece({ piece, equipements, ecrire, envoyerPhoto }: {
  piece: Piece; equipements: EquipementCourt[]
  ecrire: (url: string, method: string, corps?: object) => Promise<string | null>
  envoyerPhoto: (pieceId: string, f: File) => Promise<string | null>
}) {
  const [formEm, setFormEm] = useState<Draft | null>(null)
  const [erreurPhoto, setErreurPhoto] = useState<string | null>(null)
  const fichier = useRef<HTMLInputElement>(null)
  const base = `/api/houses/me/pieces/${piece.id}`
  const details = [piece.surface_m2 ? `${String(piece.surface_m2).replace('.', ',')} m²` : null, libelleNiveau(piece.niveau),
    piece.chauffee ? null : 'non chauffée'].filter(Boolean).join(' · ')

  return (
    <li>
      <details className="group rounded-lg border border-bord bg-white">
        <summary className="flex cursor-pointer list-none items-center gap-3 rounded-lg p-2.5 hover:bg-cream
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50">
          <Vignette docId={piece.photo?.id ?? null} />
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-semibold text-ink">{piece.nom}</span>
            <span className="block text-xs text-dark/60">{details}</span>
            <span className={'block text-xs ' + (piece.emetteurs.length ? 'text-dark/70' : 'text-dark/45 italic')}>
              {piece.emetteurs.length ? phraseEmetteurs(piece.emetteurs) : piece.chauffee ? 'Aucun émetteur indiqué' : ''}
            </span>
          </span>
          <Pencil className="h-4 w-4 shrink-0 text-primary transition-transform group-open:rotate-12" />
        </summary>

        <div className="space-y-4 border-t border-bord p-3">
          <div className="flex flex-wrap items-center gap-3">
            <Vignette docId={piece.photo?.id ?? null} taille="h-24 w-32" />
            <div className="space-y-1">
              <button type="button" onClick={() => fichier.current?.click()}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
                <Camera className="h-4 w-4" /> {piece.photo ? 'Remplacer la photo' : 'Ajouter une photo'}
              </button>
              <p className="text-xs text-dark/50">Une photo par pièce, rangée dans vos papiers.</p>
              {erreurPhoto && <p className="text-xs text-terra">{erreurPhoto}</p>}
              <input ref={fichier} type="file" accept="image/*" className="hidden" onChange={async (e) => {
                const f = e.target.files?.[0]
                if (f) setErreurPhoto(await envoyerPhoto(piece.id, f))
                e.target.value = ''
              }} />
            </div>
          </div>

          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-dark/50">Émetteurs</h4>
            {piece.emetteurs.length > 0 && (
              <ul className="mb-2 divide-y divide-bord rounded-lg border border-bord">
                {piece.emetteurs.map((e) => (
                  <li key={e.id} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
                    <span className="min-w-0">
                      {phraseEmetteurs([e])}
                      {e.puissance_w ? <span className="text-dark/50"> · {e.puissance_w} W chacun</span> : null}
                    </span>
                    <span className="flex shrink-0 gap-1">
                      <button className={icone} title="Modifier" aria-label={`Modifier ${libelleEmetteur(e.type, e.nombre)}`}
                        onClick={() => setFormEm({ ...e })}><Pencil className="h-4 w-4" /></button>
                      <button className={icone} title="Supprimer" aria-label={`Supprimer ${libelleEmetteur(e.type, e.nombre)}`}
                        onClick={() => ecrire(`${base}/emetteurs/${e.id}`, 'DELETE')}><Trash2 className="h-4 w-4" /></button>
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {formEm ? (
              <FormEmetteur key={String(formEm.id ?? 'nouveau')} initial={formEm} equipements={equipements}
                onAnnuler={() => setFormEm(null)}
                enregistrer={async (d) => {
                  const id = d.id as string | undefined
                  const err = await ecrire(id ? `${base}/emetteurs/${id}` : `${base}/emetteurs`, id ? 'PATCH' : 'POST',
                    corps(d, CHAMPS_EMETTEUR))
                  if (!err) setFormEm(null)
                  return err
                }} />
            ) : (
              <button type="button" onClick={() => setFormEm({ type: null, nombre: 1 })}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
                <Plus className="h-4 w-4" /> Ajouter un émetteur
              </button>
            )}
          </div>

          <div className="border-t border-bord pt-3">
            <FormPiece initial={{ nom: piece.nom, type: piece.type, niveau: String(piece.niveau), surface_m2: piece.surface_m2,
              chauffee: piece.chauffee, orientation: piece.orientation, note: piece.note }}
              enregistrer={(d) => ecrire(base, 'PATCH', corps(d, CHAMPS_PIECE))} />
            <button type="button" className="mt-3 text-xs text-dark/50 hover:text-terra hover:underline" onClick={() => {
              if (confirm(`Supprimer « ${piece.nom} » et ses émetteurs ? Sa photo restera dans vos papiers.`)) ecrire(base, 'DELETE')
            }}>Supprimer cette pièce</button>
          </div>
        </div>
      </details>
    </li>
  )
}

function Bilan({ r }: { r: Resume }) {
  const m2 = r.surface_pieces_m2.valeur
  return (
    <div className="mb-3 space-y-1.5 rounded-lg bg-sable/60 px-3 py-2.5 text-sm">
      <p className="text-ink">
        <strong>{r.nb_pieces.valeur}</strong> pièce{r.nb_pieces.valeur > 1 ? 's' : ''}, dont {r.nb_chauffees.valeur} chauffée{r.nb_chauffees.valeur > 1 ? 's' : ''}
        {m2 ? <> · <strong>{String(m2).replace('.', ',')} m²</strong> déclarés{r.surface_pieces_m2.pieces_sans_surface > 0 && ` (${r.surface_pieces_m2.pieces_sans_surface} sans surface)`}</> : null}
      </p>
      {r.emetteurs_par_type.length > 0 && (
        <p className="text-dark/70">
          {r.emetteurs_par_type.map((e) => `${e.nombre} ${libelleEmetteur(e.type, e.nombre)}${e.puissance_totale_w ? ` (${(e.puissance_totale_w / 1000).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} kW)` : ''}`).join(' · ')}
        </p>
      )}
      {[r.ecart_surface, r.ecart_clim].filter(Boolean).map((e) => (
        <p key={e!.message} className="text-terra">{e!.message} <span className="text-xs text-dark/50">Écart calculé, votre fiche n'est pas modifiée.</span></p>
      ))}
      {r.chauffees_sans_emetteur.valeur.length > 0 && (
        <p className="text-xs text-dark/55">Aucun émetteur indiqué pour : {r.chauffees_sans_emetteur.valeur.join(', ')}.</p>
      )}
    </div>
  )
}

export default function MesPieces({ equipements }: { equipements: EquipementCourt[] }) {
  const { authFetch } = useAuth()
  const [pieces, setPieces] = useState<Piece[] | null>(null)
  const [resume, setResume] = useState<Resume | null>(null)
  const [erreur, setErreur] = useState(false)
  const [ajout, setAjout] = useState(false)

  const charger = useCallback(() => {
    setErreur(false)
    const json = (url: string) => authFetch(url).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
    Promise.all([json('/api/houses/me/pieces'), json('/api/houses/me/pieces/resume')])
      .then(([p, r]) => { setPieces(p); setResume(r) })
      .catch(() => setErreur(true))
  }, [authFetch])
  useEffect(charger, [charger])

  async function ecrire(url: string, method: string, body?: object): Promise<string | null> {
    const res = await authFetch(url, {
      method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) return messageErreur(res)
    charger()
    return null
  }

  async function envoyerPhoto(pieceId: string, f: File): Promise<string | null> {
    const form = new FormData()
    form.append('piece_id', pieceId)
    form.append('file', f)
    const res = await authFetch('/api/houses/me/documents', { method: 'POST', body: form })
    if (!res.ok) return messageErreur(res)
    charger()
    return null
  }

  if (erreur) return <ApiError retry={charger} />
  if (!pieces || !resume) return null

  return (
    <section className="rounded-xl border border-ink/10 bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-display text-xl text-ink">
          <LayoutGrid className="h-5 w-5 text-primary" /> Mes pièces
        </h2>
        {pieces.length > 0 && !ajout && (
          <button onClick={() => setAjout(true)} className={'inline-flex items-center gap-1.5 ' + bouton}>
            <Plus className="h-4 w-4" /> Ajouter
          </button>
        )}
      </div>

      {pieces.length === 0 ? (
        <Demarrage creer={(liste) => ecrire('/api/houses/me/pieces/demarrage', 'POST', { pieces: liste })} />
      ) : (
        <>
          <Bilan r={resume} />
          {ajout && (
            <div className="mb-3 rounded-lg border border-primary/40 bg-cream/60 p-3">
              <FormPiece initial={{ type: 'autre', niveau: '0', chauffee: true }} onAnnuler={() => setAjout(false)}
                enregistrer={async (d) => {
                  const err = await ecrire('/api/houses/me/pieces', 'POST', corps(d, CHAMPS_PIECE))
                  if (!err) setAjout(false)
                  return err
                }} />
            </div>
          )}
          <ul className="space-y-2">
            {pieces.map((p) => (
              <LignePiece key={p.id} piece={p} equipements={equipements} ecrire={ecrire} envoyerPhoto={envoyerPhoto} />
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
