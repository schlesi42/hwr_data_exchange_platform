/**
 * Login-Seite.
 *
 * Behandelt drei Zustände:
 *   1. Normales Login (E-Mail + Passwort)
 *   2. Erst-Login: Cognito fordert neues Passwort an
 *   3. Fehler anzeigen
 *
 * Nach erfolgreichem Login: Weiterleitung je nach Rolle.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/auth/AuthContext'

interface LoginForm {
  email: string
  password: string
}

interface NewPasswordForm {
  newPassword: string
  confirmPassword: string
}

export default function LoginPage() {
  const { login, confirmNewPassword } = useAuth()
  const navigate = useNavigate()
  const [requiresNewPassword, setRequiresNewPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const loginForm = useForm<LoginForm>()
  const newPasswordForm = useForm<NewPasswordForm>()

  async function handleLogin(data: LoginForm) {
    setIsLoading(true)
    setError(null)
    try {
      const result = await login(data.email, data.password)
      if (result.nextStep.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') {
        // Erst-Login: Nutzer muss neues Passwort vergeben
        setRequiresNewPassword(true)
      } else {
        // Normaler Login: Weiterleitung zur passenden Seite
        redirectAfterLogin()
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Anmeldung fehlgeschlagen.'
      setError(
        message.includes('Incorrect username or password')
          ? 'E-Mail oder Passwort falsch.'
          : message
      )
    } finally {
      setIsLoading(false)
    }
  }

  async function handleNewPassword(data: NewPasswordForm) {
    if (data.newPassword !== data.confirmPassword) {
      newPasswordForm.setError('confirmPassword', { message: 'Passwörter stimmen nicht überein.' })
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      await confirmNewPassword(data.newPassword)
      redirectAfterLogin()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Fehler beim Setzen des Passworts.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  function redirectAfterLogin() {
    // Weiterleitung basiert auf der Nutzerrolle (wird nach Login gesetzt)
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-700 to-primary-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">HWR Dozierenden-Portal</h1>
          <p className="text-gray-500 mt-1">
            {requiresNewPassword
              ? 'Bitte vergeben Sie ein neues Passwort'
              : 'Bitte melden Sie sich an'}
          </p>
        </div>

        {/* Fehlermeldung */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Normales Login-Formular */}
        {!requiresNewPassword && (
          <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                E-Mail-Adresse
              </label>
              <input
                type="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="name@hwr-berlin.de"
                {...loginForm.register('email', { required: 'E-Mail ist erforderlich.' })}
              />
              {loginForm.formState.errors.email && (
                <p className="text-red-500 text-xs mt-1">
                  {loginForm.formState.errors.email.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Passwort
              </label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                {...loginForm.register('password', { required: 'Passwort ist erforderlich.' })}
              />
              {loginForm.formState.errors.password && (
                <p className="text-red-500 text-xs mt-1">
                  {loginForm.formState.errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 transition-colors font-medium"
            >
              {isLoading ? 'Anmeldung läuft...' : 'Anmelden'}
            </button>
          </form>
        )}

        {/* Neues Passwort setzen (Erst-Login) */}
        {requiresNewPassword && (
          <form onSubmit={newPasswordForm.handleSubmit(handleNewPassword)} className="space-y-4">
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm">
              Sie melden sich zum ersten Mal an. Bitte vergeben Sie ein persönliches Passwort.
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Neues Passwort
              </label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                {...newPasswordForm.register('newPassword', {
                  required: true,
                  minLength: { value: 10, message: 'Mindestens 10 Zeichen.' },
                })}
              />
              {newPasswordForm.formState.errors.newPassword && (
                <p className="text-red-500 text-xs mt-1">
                  {newPasswordForm.formState.errors.newPassword.message}
                </p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Mindestens 10 Zeichen, Groß- und Kleinbuchstaben, Zahlen.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Passwort bestätigen
              </label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                {...newPasswordForm.register('confirmPassword', { required: true })}
              />
              {newPasswordForm.formState.errors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">
                  {newPasswordForm.formState.errors.confirmPassword.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors font-medium"
            >
              {isLoading ? 'Speichern...' : 'Passwort setzen und anmelden'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
