import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import PasswordInput from '../../components/PasswordInput'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [prenom, setPrenom] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [consentCgu, setConsentCgu] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!consentCgu) {
      setError("L'acceptation des CGU est requise pour créer un compte.")
      return
    }
    setSubmitting(true)
    try {
      await register(email, password, prenom, consentCgu)
      navigate('/mon-espace')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Inscription impossible')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="max-w-[440px] mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold mb-6 text-center">Créer un compte</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="prenom">Prénom</label>
          <input
            id="prenom" type="text" autoComplete="given-name" value={prenom}
            onChange={(e) => setPrenom(e.target.value)}
            className="w-full rounded-xl border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="email">Email</label>
          <input
            id="email" type="email" required autoComplete="email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="password">Mot de passe</label>
          <PasswordInput
            id="password" required minLength={8} autoComplete="new-password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <p className="text-xs text-gray-500 mt-1">8 caractères minimum.</p>
        </div>
        <label className="flex items-start gap-2 text-sm text-gray-700">
          <input
            type="checkbox" checked={consentCgu}
            onChange={(e) => setConsentCgu(e.target.checked)}
            className="mt-0.5"
          />
          J'accepte les Conditions Générales d'Utilisation d'Helios.
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit" disabled={submitting}
          className="w-full rounded-xl bg-primary text-white font-semibold py-2.5 hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? 'Création…' : 'Créer mon compte'}
        </button>
      </form>
      <p className="text-sm text-gray-600 text-center mt-6">
        Déjà un compte ? <Link to="/connexion" className="text-primary font-semibold">Se connecter</Link>
      </p>
    </section>
  )
}
