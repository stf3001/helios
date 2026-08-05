import { type ReactNode, useEffect, useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import AdminLayout from './AdminLayout'

/** Garde du back-office. Le droit admin n'est pas exposé dans le profil utilisateur :
 * on le vérifie côté serveur via /api/admin/me. C'est volontaire — le serveur reste
 * l'autorité, l'interface ne fait qu'afficher le résultat. */
export default function AdminRoute({ children }: { children: ReactNode }) {
  const { user, loading, authFetch } = useAuth()
  const location = useLocation()
  const [autorise, setAutorise] = useState<boolean | null>(null)

  useEffect(() => {
    if (!user) return
    let annule = false
    authFetch('/api/admin/me')
      .then((r) => { if (!annule) setAutorise(r.ok) })
      .catch(() => { if (!annule) setAutorise(false) })
    return () => { annule = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  if (loading || (user && autorise === null)) {
    return <div className="min-h-screen bg-slate-950 text-slate-500 flex items-center justify-center">Vérification…</div>
  }

  if (!user) {
    // On mémorise la destination pour y revenir après connexion.
    return <Navigate to="/connexion" state={{ from: location.pathname }} replace />
  }

  if (!autorise) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center px-4">
        <div className="max-w-sm text-center">
          <ShieldAlert className="w-10 h-10 mx-auto text-rose-400" />
          <h1 className="mt-4 text-lg font-semibold text-white">Accès réservé</h1>
          <p className="mt-2 text-sm text-slate-400">
            Ce compte n'a pas les droits d'administration. Si c'est une erreur, l'accès se donne
            en base de données — aucune page ne permet de se l'attribuer soi-même.
          </p>
          <Link to="/" className="mt-5 inline-block rounded-lg border border-slate-700 px-4 py-2 text-sm hover:bg-slate-800">
            Retour au site
          </Link>
        </div>
      </div>
    )
  }

  return <AdminLayout>{children}</AdminLayout>
}
