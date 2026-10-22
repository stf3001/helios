import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Building2 } from 'lucide-react'
import PasswordInput from '../components/PasswordInput'
import { useTitle } from '../hooks/useTitle'

/** Activation d'un compte partenaire (mises en relation, lot 3) : le lien, à usage unique et
 *  valable 7 jours, est transmis par l'administration elle-même — aucun e-mail ne part. */
export default function ActivationPartenaire() {
  useTitle('Activer mon espace partenaire')
  const [params] = useSearchParams()
  const jeton = params.get('jeton') ?? ''
  const navigate = useNavigate()
  const [compte, setCompte] = useState<{ raison_sociale: string; email: string } | null>(null)
  const [invalide, setInvalide] = useState(false)
  const [mdp, setMdp] = useState('')
  const [mdp2, setMdp2] = useState('')
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    fetch(`/api/partner/activation?jeton=${encodeURIComponent(jeton)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then(setCompte).catch(() => setInvalide(true))
  }, [jeton])

  async function activer(e: FormEvent) {
    e.preventDefault()
    if (mdp !== mdp2) { setErreur('Les deux mots de passe diffèrent.'); return }
    const r = await fetch('/api/partner/activation', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ jeton, password: mdp }),
    })
    if (!r.ok) { setErreur(r.status === 410 ? "Ce lien n'est plus valable : demandez-en un nouveau." : 'Mot de passe trop court (8 caractères au moins).'); return }
    localStorage.setItem('helios_partner_token', (await r.json()).access_token)
    navigate('/partenaire', { replace: true })
  }

  return (
    <section className="max-w-sm mx-auto px-4 py-16">
      <div className="flex items-center gap-2 mb-6">
        <Building2 className="w-7 h-7 text-primary" />
        <h1 className="text-2xl font-bold">Activer mon espace</h1>
      </div>
      {invalide ? (
        <p className="text-sm text-dark/80">
          Ce lien d'activation n'est plus valable : il a déjà servi, a expiré (7 jours), ou un nouveau lien l'a remplacé.
          Demandez-en un nouveau à Hélios.
        </p>
      ) : !compte ? <p className="text-sm text-gray-400">Vérification du lien…</p> : (
        <form onSubmit={activer} className="space-y-4">
          <p className="text-sm text-dark/80">
            <strong>{compte.raison_sociale}</strong> — vous vous connecterez avec <strong>{compte.email}</strong>.
            Choisissez votre mot de passe.
          </p>
          <label className="block text-sm font-medium">Mot de passe (8 caractères au moins)
            <PasswordInput required minLength={8} value={mdp} onChange={(e) => setMdp(e.target.value)} autoComplete="new-password"
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </label>
          <label className="block text-sm font-medium">Confirmez-le
            <PasswordInput required minLength={8} value={mdp2} onChange={(e) => setMdp2(e.target.value)} autoComplete="new-password"
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
          </label>
          <button type="submit" className="w-full rounded-xl bg-primary text-white font-semibold px-4 py-2.5 hover:opacity-90">
            Activer et entrer
          </button>
          {erreur && <p className="text-sm text-red-600">{erreur}</p>}
        </form>
      )}
    </section>
  )
}
