/**
 * ProtectedRoute – Schützt Routen vor nicht autorisierten Zugriffen.
 *
 * Wenn nicht eingeloggt → Weiterleitung zum Login.
 * Wenn falsche Rolle → Zugriff verweigert.
 */
import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { UserRole } from '@/types'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: UserRole[]  // wenn leer: alle eingeloggten Nutzer
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Zugriff verweigert</h1>
          <p className="text-gray-600 mt-2">Sie haben keine Berechtigung für diese Seite.</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
