/**
 * Navigationsleiste – zeigt Logo, Nutzerinfo und Logout-Button.
 */
import { LogOut, User } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'

const ROLE_LABELS = {
  admin: 'Administrator',
  buero: 'Fachbereichsbüro',
  dozent: 'Dozent/in',
}

export function Navbar() {
  const { user, logout } = useAuth()

  return (
    <nav className="bg-primary-700 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo / Titel */}
          <div className="flex items-center">
            <span className="text-xl font-bold">HWR Dozierenden-Portal</span>
          </div>

          {/* Nutzerinfo + Logout */}
          {user && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <User size={16} />
                <span>{user.email}</span>
                <span className="text-primary-300">
                  ({ROLE_LABELS[user.role]})
                </span>
                {user.department_name && (
                  <span className="text-primary-300">– {user.department_name}</span>
                )}
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-1 text-sm hover:text-primary-200 transition-colors"
                title="Abmelden"
              >
                <LogOut size={16} />
                <span className="hidden sm:inline">Abmelden</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
