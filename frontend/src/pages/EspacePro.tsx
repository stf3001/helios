import { useEffect, useState, type FormEvent } from 'react'
import { Building2, Lightbulb } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'

const SECTEURS = [
  ['boulangerie', 'Boulangerie / pâtisserie'], ['restauration', 'Restauration'],
  ['commerce', 'Commerce'], ['artisanat', 'Artisanat / atelier'],
  ['bureau', 'Bureau / tertiaire'], ['hotellerie', 'Hôtellerie'], ['autre', 'Autre'],
]
const EQUIPEMENTS = [
  ['four', 'Four'], ['chambre_froide', 'Chambre froide'], ['vitrine_refrigeree', 'Vitrine réfrigérée'],
  ['climatisation', 'Climatisation'], ['eclairage_intensif', 'Éclairage intensif'],
  ['machines', 'Machines'], ['air_comprime', 'Air comprimé'], ['informatique', 'Informatique'],
]

interface Profile {
  raison_sociale?: string; secteur?: string; code_postal?: string; surface_m2?: number
  effectif?: number; equipements?: string[]; conso_annuelle_kwh?: number; puissance_kva?: number
  fournisseur_actuel?: string; contrat_actuel?: string
}
interface Advice { secteur: string; recommandations: { sujet: string; conseil: string }[]; courtage_recommande: boolean; avertissement: string }
interface Courtage { favorable: boolean; helios_opinion: string; partenaire: string | null; comparateur_public: string; partner_link: string | null; estimation: { gain_estime_pct: number; gain_estime_eur_an: number } }

export default function EspacePro() {
  useTitle('Espace Pro')
  const { authFetch } = useAuth()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [advice, setAdvice] = useState<Advice | null>(null)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState<Profile>({ equipements: [] })
  const [saving, setSaving] = useState(false)
  const [facture, setFacture] = useState('')
  const [consent, setConsent] = useState(false)
  const [courtage, setCourtage] = useState<Courtage | null>(null)

  function load() {
    authFetch('/api/pro/profile').then((r) => (r.ok ? r.json() : null)).then((p) => {
      setProfile(p)
      if (p) { setForm(p); authFetch('/api/pro/advice').then((r) => (r.ok ? r.json() : null)).then(setAdvice) }
    }).finally(() => setLoading(false))
  }
  useEffect(load, [authFetch])

  function toggleEquip(e: string) {
    setForm((f) => {
      const eq = f.equipements ?? []
      return { ...f, equipements: eq.includes(e) ? eq.filter((x) => x !== e) : [...eq, e] }
    })
  }

  async function save(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    const method = profile ? 'PATCH' : 'POST'
    const res = await authFetch('/api/pro/profile', {
      method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form),
    })
    if (res.ok) load()
    setSaving(false)
  }

  async function launchCourtage() {
    if (!consent) return
    const res = await authFetch('/api/pro/courtage', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consent, montant_facture_annuelle_eur: facture ? Number(facture) : null }),
    })
    if (res.ok) setCourtage(await res.json())
  }

  const num = (k: keyof Profile) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value ? Number(e.target.value) : undefined }))
  const str = (k: keyof Profile) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value || undefined }))

  if (loading) return <p className="text-gray-400 p-12 text-center">Chargement…</p>

  return (
    <section className="max-w-[900px] mx-auto px-4 py-12">
      <div className="flex items-center gap-2 mb-2">
        <Building2 className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Espace professionnel</h1>
      </div>
      <p className="text-gray-600 mb-8">
        Vous êtes une entreprise ? Helios adapte ses conseils à votre métier et peut faire jouer la concurrence
        sur vos factures d'énergie — souvent un gros levier en professionnel.
      </p>

      {/* Profil */}
      <form onSubmit={save} className="bg-gray-50 rounded-2xl p-6 grid gap-4 sm:grid-cols-2 mb-8">
        <div className="sm:col-span-2 font-semibold">{profile ? 'Mon profil professionnel' : 'Créer mon profil professionnel'}</div>
        <input value={form.raison_sociale ?? ''} onChange={str('raison_sociale')} placeholder="Raison sociale"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <select value={form.secteur ?? ''} onChange={str('secteur')} className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
          <option value="">— secteur —</option>
          {SECTEURS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <input value={form.code_postal ?? ''} onChange={str('code_postal')} placeholder="Code postal"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <input type="number" value={form.surface_m2 ?? ''} onChange={num('surface_m2')} placeholder="Surface (m²)"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <input type="number" value={form.conso_annuelle_kwh ?? ''} onChange={num('conso_annuelle_kwh')} placeholder="Conso annuelle (kWh)"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <input type="number" value={form.puissance_kva ?? ''} onChange={num('puissance_kva')} placeholder="Puissance (kVA)"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <input value={form.fournisseur_actuel ?? ''} onChange={str('fournisseur_actuel')} placeholder="Fournisseur actuel"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <input value={form.contrat_actuel ?? ''} onChange={str('contrat_actuel')} placeholder="Contrat actuel"
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
        <div className="sm:col-span-2">
          <div className="text-sm font-medium mb-1">Équipements énergivores</div>
          <div className="flex flex-wrap gap-2">
            {EQUIPEMENTS.map(([v, l]) => (
              <button type="button" key={v} onClick={() => toggleEquip(v)}
                className={'text-xs px-3 py-1.5 rounded-full border ' +
                  ((form.equipements ?? []).includes(v) ? 'bg-primary text-white border-primary' : 'border-gray-300 text-gray-600')}>
                {l}
              </button>
            ))}
          </div>
        </div>
        <button type="submit" disabled={saving} className="sm:col-span-2 justify-self-start rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-50">
          {saving ? 'Enregistrement…' : profile ? 'Mettre à jour' : 'Créer mon profil'}
        </button>
      </form>

      {/* Conseils */}
      {advice && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-primary" />
            <h2 className="font-semibold text-lg">Les conseils d'Helios — {advice.secteur}</h2>
          </div>
          <div className="space-y-3">
            {advice.recommandations.map((r, i) => (
              <div key={i} className="border border-gray-200 rounded-xl p-4">
                <div className="font-medium text-sm">{r.sujet}</div>
                <div className="text-sm text-gray-600 mt-1">{r.conseil}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">{advice.avertissement}</p>
        </div>
      )}

      {/* Courtage pro */}
      {profile && (
        <div className="border-t border-gray-200 pt-8">
          <h2 className="font-semibold text-lg mb-2">Étude de courtage professionnelle</h2>
          <p className="text-sm text-gray-600 mb-4">
            Un partenaire courtier compare les offres pros selon votre profil. <strong>Helios vous donne son avis indépendant.</strong>
          </p>
          {!courtage ? (
            <div className="bg-gray-50 rounded-2xl p-5 space-y-3">
              <input type="number" value={facture} onChange={(e) => setFacture(e.target.value)} placeholder="Facture annuelle (€, si connue)"
                className="w-full sm:w-72 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
              <label className="flex items-start gap-2 text-sm text-gray-700">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
                <span>J'autorise HELIOS à transmettre mon profil à un partenaire courtier pour comparer les offres pros.</span>
              </label>
              <button onClick={launchCourtage} disabled={!consent}
                className="rounded-xl bg-primary text-white font-semibold px-5 py-2.5 hover:opacity-90 disabled:opacity-40">
                Lancer l'étude de courtage
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className={'rounded-2xl p-5 border ' + (courtage.favorable ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200')}>
                <div className="font-semibold mb-1">L'avis d'Helios{courtage.partenaire ? ` (courtier : ${courtage.partenaire})` : ''}</div>
                <p className="text-sm text-gray-700">{courtage.helios_opinion}</p>
              </div>
              <div className="text-sm text-gray-600">Gain estimé <strong>~{courtage.estimation.gain_estime_pct}%</strong> soit ~{courtage.estimation.gain_estime_eur_an} €/an.</div>
              <p className="text-xs text-gray-400">Comparez aussi sur <a href={courtage.comparateur_public} target="_blank" rel="noopener noreferrer" className="underline">energie-info.fr</a>.</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
