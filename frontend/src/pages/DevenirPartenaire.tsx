import { useState, type FormEvent } from 'react'
import Hero from '../components/Hero'
import { useTitle } from '../hooks/useTitle'

const METIERS = [
  { value: 'pv', label: 'Photovoltaïque' },
  { value: 'pac', label: 'Pompe à chaleur' },
  { value: 'isolation', label: 'Isolation' },
  { value: 'menuiseries', label: 'Menuiseries' },
  { value: 'vmc', label: 'Ventilation' },
  { value: 'regulation', label: 'Régulation' },
]

export default function DevenirPartenaire() {
  useTitle('Devenir partenaire')
  const [raison, setRaison] = useState('')
  const [siret, setSiret] = useState('')
  const [email, setEmail] = useState('')
  const [rge, setRge] = useState(false)
  const [zones, setZones] = useState('')
  const [metiers, setMetiers] = useState<string[]>([])
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function toggleMetier(m: string) {
    setMetiers((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const res = await fetch('/api/partners/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raison_sociale: raison,
          siret,
          email,
          rge,
          zones: zones.split(',').map((z) => z.trim()).filter(Boolean),
          metiers,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(typeof body?.detail === 'string' ? body.detail : 'Candidature impossible — vérifiez les champs.')
      }
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Hero title="Devenez partenaire HELIOS." />
      <section className="max-w-[700px] mx-auto px-4 py-12">
        <p className="text-gray-600 mb-8">
          HELIOS vous apporte des clients qualifiés (fiche maison + pré-audit + projet), avec leur consentement.
          Commission d'apport d'affaires uniquement si les travaux sont signés — jamais d'abonnement.
          Référencement soumis à vérification (RGE si requis, assurance décennale, Kbis).
        </p>

        {done ? (
          <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-green-800">
            <strong>Candidature reçue !</strong> Nous revenons vers vous après vérification de votre dossier.
          </div>
        ) : (
          <form onSubmit={onSubmit} className="bg-gray-50 rounded-2xl p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Raison sociale</label>
              <input required value={raison} onChange={(e) => setRaison(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">SIRET (14 chiffres)</label>
                <input required value={siret} onChange={(e) => setSiret(e.target.value.replace(/\D/g, '').slice(0, 14))}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email de contact</label>
                <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Zones couvertes (codes postaux, séparés par des virgules)</label>
              <input value={zones} onChange={(e) => setZones(e.target.value)} placeholder="69001, 69002, 38000"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Métiers</label>
              <div className="flex flex-wrap gap-2">
                {METIERS.map((m) => (
                  <button type="button" key={m.value} onClick={() => toggleMetier(m.value)}
                    className={'text-sm px-3 py-1.5 rounded-full border ' +
                      (metiers.includes(m.value) ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-700')}>
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={rge} onChange={(e) => setRge(e.target.checked)} />
              Je suis certifié RGE
            </label>
            <button type="submit" disabled={submitting || !raison || siret.length !== 14 || metiers.length === 0}
              className="rounded-xl bg-primary text-white font-semibold px-6 py-2.5 hover:opacity-90 disabled:opacity-40">
              {submitting ? 'Envoi…' : 'Envoyer ma candidature'}
            </button>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </form>
        )}
      </section>
    </>
  )
}
