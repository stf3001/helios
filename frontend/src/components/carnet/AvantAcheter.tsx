import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ClipboardCheck, Paperclip } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { faqSlug } from '../../lib/faqSlug'
import type { Doc } from './Formulaires'
import { messageErreur } from './Formulaires'
import { signalerMaj, useMaj } from './commun'

/**
 * « Avant d'acheter » (carnet, lot 8) : à la place du bloc « À faire » quand la fiche dit
 * « en cours d'achat ». Les documents à demander au vendeur, à cocher ; une pièce reçue se
 * dépose comme n'importe quel document de la maison (limites de nombre et de taille comprises) et se rattache
 * à sa ligne. Les libellés viennent de `kb/achat_logement.md`, par l'API.
 * Au passage à « propriétaire », le serveur archive la liste au journal.
 */

type Ligne = { id: string; libelle: string; coche: boolean; document_id: string | null; type_document: string }

export default function AvantAcheter() {
  const { authFetch } = useAuth()
  const [lignes, setLignes] = useState<Ligne[] | null>(null)
  const [fiche, setFiche] = useState('')
  const [documents, setDocuments] = useState<Doc[]>([])
  const [erreur, setErreur] = useState<string | null>(null)
  const [envoi, setEnvoi] = useState<string | null>(null)
  const fichier = useRef<HTMLInputElement>(null)
  const cible = useRef<Ligne | null>(null)

  const charger = useCallback(() => {
    const json = (url: string) => authFetch(url).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
    Promise.all([json('/api/houses/me/avant-achat'), json('/api/houses/me/documents')])
      .then(([a, docs]) => { setLignes(a.lignes); setFiche(a.fiche); setDocuments(docs) })
      .catch(() => setLignes(null))
  }, [authFetch])
  useEffect(charger, [charger])
  useMaj(charger)

  async function ecrire(id: string, corps: object) {
    setErreur(null)
    const res = await authFetch(`/api/houses/me/avant-achat/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
    })
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    setLignes((await res.json()).lignes)
  }

  async function deposer(f: File) {
    const l = cible.current
    if (!l) return
    setErreur(null)
    setEnvoi(l.id)
    const form = new FormData()
    form.append('file', f)
    form.append('type', l.type_document)
    const res = await authFetch('/api/houses/me/documents', { method: 'POST', body: form })
    setEnvoi(null)
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    const doc = await res.json()
    await ecrire(l.id, { coche: true, document_id: doc.id })
    signalerMaj()  // l'onglet « Papiers » se recharge aussi
  }

  if (!lignes) return null
  const nomDoc = (id: string | null) => documents.find((d) => d.id === id)?.filename
  const recus = lignes.filter((l) => l.coche).length

  return (
    <section className="mb-4 rounded-xl border border-bord bg-white p-4" aria-label="Avant d'acheter">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-display text-lg text-ink">
          <ClipboardCheck className="h-5 w-5 text-primary" /> Avant d'acheter
        </span>
        <span className="text-sm text-dark/60">{recus} / {lignes.length} reçus</span>
      </div>
      <p className="mb-2 text-sm text-dark/70">
        Les papiers à demander au vendeur. Cochez ce que vous avez reçu, joignez-le si vous l'avez.{' '}
        {fiche && <Link to={`/faq/${faqSlug(fiche)}`} className="font-semibold text-primary hover:underline">En savoir plus</Link>}
      </p>
      <input ref={fichier} type="file" accept="application/pdf,image/*" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) deposer(f) }} />
      <ul className="divide-y divide-bord">
        {lignes.map((l) => (
          <li key={l.id} className="flex items-start gap-3 py-2.5">
            <input id={`achat-${l.id}`} type="checkbox" checked={l.coche}
              onChange={(e) => ecrire(l.id, { coche: e.target.checked })}
              className="mt-0.5 h-4 w-4 shrink-0 accent-primary" />
            <span className="min-w-0 flex-1 text-sm">
              <label htmlFor={`achat-${l.id}`} className={'block ' + (l.coche ? 'text-dark/60' : 'text-ink')}>{l.libelle}</label>
              {l.document_id && nomDoc(l.document_id) && (
                <span className="mt-0.5 inline-flex items-center gap-1 text-xs text-dark/60">
                  <Paperclip className="h-3 w-3" /> {nomDoc(l.document_id)}
                </span>
              )}
            </span>
            {!l.document_id && (
              <button onClick={() => { cible.current = l; fichier.current?.click() }} disabled={envoi !== null}
                className="shrink-0 text-xs font-semibold text-primary hover:underline disabled:opacity-50">
                {envoi === l.id ? 'Envoi…' : 'Joindre'}
              </button>
            )}
          </li>
        ))}
      </ul>
      {erreur && <p className="mt-2 text-sm text-terra">{erreur}</p>}
      <p className="mt-2 text-xs text-dark/50">
        Une fois propriétaire, indiquez-le dans votre fiche : cette liste sera rangée dans le journal de la maison.
      </p>
    </section>
  )
}
