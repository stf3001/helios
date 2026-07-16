import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

type Status = 'checking' | 'ok' | 'error'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const [status, setStatus] = useState<Status>('checking')

  useEffect(() => {
    const token = params.get('token')
    if (!token) {
      setStatus('error')
      return
    }
    fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then((res) => setStatus(res.ok ? 'ok' : 'error'))
      .catch(() => setStatus('error'))
  }, [params])

  return (
    <section className="max-w-[520px] mx-auto px-4 py-16 text-center">
      {status === 'checking' && <p className="text-gray-500">Vérification en cours…</p>}
      {status === 'ok' && (
        <>
          <h1 className="text-2xl font-bold mb-3">Email vérifié !</h1>
          <p className="text-gray-700 mb-6">Votre adresse email est confirmée. Vous pouvez continuer.</p>
          <Link to="/mon-espace" className="text-primary font-semibold">Aller à mon espace →</Link>
        </>
      )}
      {status === 'error' && (
        <>
          <h1 className="text-2xl font-bold mb-3">Lien invalide ou expiré</h1>
          <p className="text-gray-700 mb-6">
            Ce lien de vérification n'est plus valable. Connectez-vous pour en recevoir un nouveau.
          </p>
          <Link to="/connexion" className="text-primary font-semibold">Retour à la connexion →</Link>
        </>
      )}
    </section>
  )
}
