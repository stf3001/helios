import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileUp, Trash2, Download, MessageSquareText } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const MAX_DOCUMENTS = 6

interface Doc {
  id: string
  type: string
  filename: string
  size: number | null
  uploaded_at: string
}

const TYPES = [
  { value: 'dpe', label: 'DPE' },
  { value: 'facture', label: 'Facture' },
  { value: 'devis', label: 'Devis' },
  { value: 'photo', label: 'Photo' },
  { value: 'autre', label: 'Autre' },
]

const TYPE_LABEL: Record<string, string> = Object.fromEntries(TYPES.map((t) => [t.value, t.label]))

function humanSize(n: number | null): string {
  if (!n) return ''
  return n < 1024 * 1024 ? `${Math.round(n / 1024)} Ko` : `${(n / 1024 / 1024).toFixed(1)} Mo`
}

export default function HouseDocuments() {
  const { authFetch } = useAuth()
  const navigate = useNavigate()
  const [docs, setDocs] = useState<Doc[]>([])
  const [type, setType] = useState('dpe')
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [askingId, setAskingId] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const atLimit = docs.length >= MAX_DOCUMENTS

  function load() {
    authFetch('/api/houses/me/documents').then((r) => (r.ok ? r.json() : [])).then(setDocs)
  }
  useEffect(load, [authFetch])

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setError(null)
    setUploading(true)
    try {
      const form = new FormData()
      form.append('type', type)
      form.append('file', file)
      const res = await authFetch('/api/houses/me/documents', { method: 'POST', body: form })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Envoi impossible.')
      }
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function download(doc: Doc) {
    const res = await authFetch(`/api/houses/me/documents/${doc.id}`)
    if (!res.ok) return
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = doc.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  async function remove(doc: Doc) {
    if (!confirm(`Supprimer « ${doc.filename} » ?`)) return
    const res = await authFetch(`/api/houses/me/documents/${doc.id}`, { method: 'DELETE' })
    if (res.ok) load()
  }

  async function askHelios(doc: Doc) {
    setAskingId(doc.id)
    setError(null)
    try {
      const res = await authFetch(`/api/houses/me/documents/${doc.id}/extract`)
      const body = await res.json().catch(() => null)
      if (!res.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : 'Extraction impossible.')
      const extrait = body.tronque ? `${body.text}\n\n[…texte tronqué, document plus long]` : body.text
      const question =
        `J'ai déposé le document « ${doc.filename} » dans mon espace, peux-tu me donner ton avis dessus ?\n\n` +
        `--- Contenu du document ---\n${extrait}`
      navigate(`/espace/helios?ask=${encodeURIComponent(question)}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setAskingId(null)
    }
  }

  return (
    <div className="bg-gray-50 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-semibold">Mes documents</h3>
        <span className={'text-xs ' + (atLimit ? 'text-amber-600 font-medium' : 'text-gray-400')}>
          {docs.length} / {MAX_DOCUMENTS}
        </span>
      </div>
      <p className="text-sm text-gray-500 mb-4">
        Ajoutez votre DPE, vos factures, un devis (pour l'avis d'Helios) ou des photos de votre logement
        (PDF ou image, 10 Mo max, {MAX_DOCUMENTS} documents maximum pour l'instant).
      </p>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <select value={type} onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
          {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <label className={'inline-flex items-center gap-2 rounded-xl text-sm font-semibold px-4 py-2 ' +
          (atLimit ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-primary text-white hover:opacity-90 cursor-pointer')}>
          <FileUp className="w-4 h-4" /> {uploading ? 'Envoi…' : atLimit ? 'Limite atteinte' : 'Ajouter un document'}
          <input ref={fileRef} type="file" className="hidden" onChange={onFile}
            accept="application/pdf,image/*" disabled={uploading || atLimit} />
        </label>
      </div>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {docs.length === 0 ? (
        <p className="text-sm text-gray-400">Aucun document pour l'instant.</p>
      ) : (
        <ul className="divide-y divide-gray-200">
          {docs.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-3 py-2 text-sm">
              <div className="min-w-0">
                <span className="text-xs uppercase text-primary mr-2">{TYPE_LABEL[d.type] ?? d.type}</span>
                <span className="text-gray-700">{d.filename}</span>
                <span className="text-gray-400 ml-2">{humanSize(d.size)}</span>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                {d.type === 'devis' && (
                  <button onClick={() => askHelios(d)} disabled={askingId === d.id}
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline disabled:opacity-50"
                    title="Demander l'avis d'Helios">
                    <MessageSquareText className="w-3.5 h-3.5" />
                    {askingId === d.id ? 'Lecture…' : "Avis d'Helios"}
                  </button>
                )}
                <button onClick={() => download(d)} className="text-gray-500 hover:text-primary" title="Télécharger">
                  <Download className="w-4 h-4" />
                </button>
                <button onClick={() => remove(d)} className="text-gray-400 hover:text-red-500" title="Supprimer">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
