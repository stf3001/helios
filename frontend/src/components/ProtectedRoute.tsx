import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="max-w-[900px] mx-auto px-4 py-16 text-center text-gray-500">Chargement…</div>
  }
  if (!user) {
    return <Navigate to="/connexion" replace />
  }
  return <>{children}</>
}
