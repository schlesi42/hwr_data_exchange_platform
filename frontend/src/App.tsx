/**
 * App – Hauptkomponente mit Routing.
 *
 * React Router v6:
 *   - <Routes>: Container für alle Routen
 *   - <Route path="..." element={...}>: Eine Route
 *   - <Navigate to="...">: Weiterleitung
 *
 * Rollenbasiertes Routing:
 *   /admin/*  → nur für Admins
 *   /buero/*  → nur für Büros
 *   /dozent/* → nur für Dozenten
 *   /         → Weiterleitung je nach Rolle
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/auth/AuthContext'
import { ProtectedRoute } from '@/auth/ProtectedRoute'

// Pages
import LoginPage from '@/pages/Login'
import AdminDashboard from '@/pages/admin/AdminDashboard'
import DepartmentsPage from '@/pages/admin/DepartmentsPage'
import UsersPage from '@/pages/admin/UsersPage'
import BueroDashboard from '@/pages/buero/BueroDashboard'
import NewRequestPage from '@/pages/buero/NewRequestPage'
import RequestDetailPage from '@/pages/buero/RequestDetailPage'
import DozentDashboard from '@/pages/dozent/DozentDashboard'
import UploadPage from '@/pages/dozent/UploadPage'

/**
 * Root-Weiterleitung je nach Rolle.
 * Wird aufgerufen, wenn Nutzer "/" besucht.
 */
function RootRedirect() {
  const { user, isLoading } = useAuth()

  if (isLoading) return null

  if (!user) return <Navigate to="/login" replace />

  switch (user.role) {
    case 'admin':  return <Navigate to="/admin" replace />
    case 'buero':  return <Navigate to="/buero" replace />
    case 'dozent': return <Navigate to="/dozent" replace />
    default:       return <Navigate to="/login" replace />
  }
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Öffentliche Routen */}
          <Route path="/login" element={<LoginPage />} />

          {/* Root: Weiterleitung je nach Rolle */}
          <Route path="/" element={<RootRedirect />} />

          {/* Admin-Bereich */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/departments"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DepartmentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <UsersPage />
              </ProtectedRoute>
            }
          />

          {/* Büro-Bereich */}
          <Route
            path="/buero"
            element={
              <ProtectedRoute allowedRoles={['buero', 'admin']}>
                <BueroDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/buero/requests/new"
            element={
              <ProtectedRoute allowedRoles={['buero']}>
                <NewRequestPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/buero/requests/:id"
            element={
              <ProtectedRoute allowedRoles={['buero', 'admin']}>
                <RequestDetailPage />
              </ProtectedRoute>
            }
          />

          {/* Dozenten-Bereich */}
          <Route
            path="/dozent"
            element={
              <ProtectedRoute allowedRoles={['dozent']}>
                <DozentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dozent/upload/:id"
            element={
              <ProtectedRoute allowedRoles={['dozent']}>
                <UploadPage />
              </ProtectedRoute>
            }
          />

          {/* Fallback: 404 → Root */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
