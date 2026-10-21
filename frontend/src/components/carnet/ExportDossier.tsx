import { useState } from 'react'
import { FileDown } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { messageErreur } from './Formulaires'

/**
 * « Télécharger le dossier de ma maison » (carnet, lot 6) — gratuit, généré à la demande.
 *
 * Le foyer coche les sections (toutes par défaut) ; les numéros de série sont EXCLUS par
 * défaut. Les codes de section sont ceux de `api/app/services/pdf_dossier.py` (SECTIONS).
 */
const SECTIONS: [string, string][] = [
  ['logement', 'Le logement'], ['enveloppe', "L'enveloppe"], ['equipements', 'Les équipements'],
  ['pieces', 'Les pièces et leurs émetteurs'], ['travaux', 'Les travaux et les garanties'],
  ['entretien', "L'entretien et le journal"], ['energie', "L'énergie déclarée"], ['documents', 'Les documents disponibles'],
]

export default function ExportDossier() {
  const { authFetch } = useAuth()
  const [ouvert, setOuvert] = useState(false)
  const [choix, setChoix] = useState<string[]>(SECTIONS.map(([c]) => c))
  const [series, setSeries] = useState(false)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)

  async function telecharger() {
    setEnvoi(true)
    setErreur(null)
    const res = await authFetch('/api/houses/me/dossier', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sections: choix, numeros_serie: series }),
    })
    setEnvoi(false)
    if (!res.ok) { setErreur(await messageErreur(res)); return }
    const blob = await res.blob()
    const nom = /filename="([^"]+)"/.exec(res.headers.get('Content-Disposition') ?? '')?.[1] ?? 'dossier-maison.pdf'
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = nom
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mb-4 rounded-xl border border-bord bg-white p-4">
      <p className="mb-2 text-sm text-dark/70">Utile pour une vente, une location, un artisan ou votre assureur.</p>
      {!ouvert ? (
        <button onClick={() => setOuvert(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
          <FileDown className="h-4 w-4" /> Télécharger le dossier de ma maison
        </button>
      ) : (
        <div className="space-y-3">
          <fieldset>
            <legend className="mb-1.5 text-sm font-semibold text-ink">Sections à inclure</legend>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {SECTIONS.map(([code, libelle]) => (
                <label key={code} className="flex items-center gap-2 text-sm text-dark/80">
                  <input type="checkbox" className="h-4 w-4 accent-[rgb(var(--h-accent))]" checked={choix.includes(code)}
                    onChange={(e) => setChoix((c) => (e.target.checked ? [...c, code] : c.filter((x) => x !== code)))} />
                  {libelle}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="flex items-start gap-2 text-sm text-dark/80">
            <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[rgb(var(--h-accent))]" checked={series}
              onChange={(e) => setSeries(e.target.checked)} />
            <span>Inclure les numéros de série des appareils <span className="text-dark/50">(non inclus par défaut)</span></span>
          </label>
          {erreur && <p className="text-sm text-terra">{erreur}</p>}
          <div className="flex flex-wrap gap-2">
            <button onClick={telecharger} disabled={envoi || choix.length === 0}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50">
              <FileDown className="h-4 w-4" /> {envoi ? 'Préparation…' : 'Télécharger le PDF'}
            </button>
            <button onClick={() => setOuvert(false)}
              className="rounded-lg border border-bord px-4 py-2 text-sm text-dark/70 hover:border-primary hover:text-primary">
              Fermer
            </button>
          </div>
          <p className="text-xs text-dark/50">Gratuit. Le dossier n'est pas conservé : il est préparé à chaque téléchargement.</p>
        </div>
      )}
    </div>
  )
}
