import { useState, type FormEvent } from 'react'
import Hero from '../components/Hero'
import { useTitle } from '../hooks/useTitle'

// Codes de l'annuaire (`regions.METIERS`, `schemas/partner.Metier`) : « solaire » et non plus
// « pv », sinon un candidat solaire n'est jamais proposé à un foyer.
const METIERS = [
  { value: 'solaire', label: 'Photovoltaïque' },
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
  // Justificatifs joints d'office (mises en relation, lot 3) : mêmes règles que dans l'espace partenaire.
  const [kbis, setKbis] = useState<File | null>(null)
  const [kbisDate, setKbisDate] = useState('')
  const [decennale, setDecennale] = useState<File | null>(null)
  const [decennaleFin, setDecennaleFin] = useState('')
  const [rgeFichier, setRgeFichier] = useState<File | null>(null)
  const [rgeFin, setRgeFin] = useState('')
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
      const corps = new FormData()
      corps.append('candidature', JSON.stringify({
        raison_sociale: raison,
        siret,
        email,
        rge,
        zones: zones.split(',').map((z) => z.trim()).filter(Boolean),
        metiers,
      }))
      corps.append('kbis', kbis!); corps.append('kbis_date', kbisDate)
      corps.append('decennale', decennale!); corps.append('decennale_fin', decennaleFin)
      if (rge && rgeFichier) { corps.append('rge', rgeFichier); corps.append('rge_fin', rgeFin) }
      const res = await fetch('/api/partners/apply', { method: 'POST', body: corps })
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
          60 € HT par mise en relation, demandée par un foyer, avec son projet et son consentement. Pas d'abonnement, pas de commission sur vos chantiers. Contestation possible sous 7 jours : coordonnées fausses, hors de votre zone ou de vos métiers, doublon, foyer injoignable après trois essais.
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
              {/* On demande des DÉPARTEMENTS, parce que c'est la maille à laquelle Helios
                  cherche un partenaire pour un visiteur. Un code postal reste accepté et
                  ramené à son département à l'enregistrement (`regions.normaliser_zones`),
                  mais l'exemple ne doit plus en proposer : il invitait à saisir ce que le
                  chat ne savait pas relire. */}
              <label className="block text-sm font-medium mb-1">
                Départements couverts, séparés par des virgules
              </label>
              <input value={zones} onChange={(e) => setZones(e.target.value)} placeholder="69, 38, 2A"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              <p className="mt-1 text-xs text-dark/60">
                Un code postal fonctionne aussi — il sera ramené à son département.
              </p>
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
            <fieldset className="space-y-3 rounded-xl border border-bord bg-white p-4">
              <legend className="px-1 text-sm font-medium">Vos justificatifs (PDF ou image, 10 Mo au plus)</legend>
              <Justificatif libelle="Extrait Kbis de moins de 3 mois" dateLibelle="Délivré le"
                onFichier={setKbis} date={kbisDate} onDate={setKbisDate} />
              <Justificatif libelle="Attestation d'assurance décennale" dateLibelle="Valable jusqu'au"
                onFichier={setDecennale} date={decennaleFin} onDate={setDecennaleFin} />
              {rge && (
                <Justificatif libelle="Qualification RGE" dateLibelle="Valable jusqu'au"
                  onFichier={setRgeFichier} date={rgeFin} onDate={setRgeFin} />
              )}
            </fieldset>
            <button type="submit" disabled={submitting || !raison || siret.length !== 14 || metiers.length === 0
              || !kbis || !kbisDate || !decennale || !decennaleFin || (rge && (!rgeFichier || !rgeFin))}
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

function Justificatif({ libelle, dateLibelle, onFichier, date, onDate }: {
  libelle: string; dateLibelle: string; onFichier: (f: File | null) => void; date: string; onDate: (d: string) => void
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-[1fr_auto] sm:items-end">
      <label className="block text-sm">{libelle}
        <input type="file" required accept="application/pdf,image/jpeg,image/png,image/webp"
          onChange={(e) => onFichier(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
      </label>
      <label className="block text-sm">{dateLibelle}
        <input type="date" required value={date} onChange={(e) => onDate(e.target.value)}
          className="mt-1 block rounded-lg border border-gray-300 px-3 py-1.5 text-sm" />
      </label>
    </div>
  )
}
