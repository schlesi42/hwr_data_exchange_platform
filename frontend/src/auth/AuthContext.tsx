/**
 * Auth Context – verwaltet den Anmeldestatus der gesamten Anwendung.
 *
 * React Context macht den eingeloggten Nutzer in allen Komponenten
 * verfügbar, ohne Props durch die ganze App-Hierarchie zu reichen.
 *
 * Cognito via AWS Amplify v6:
 *   - signIn():          E-Mail + Passwort
 *   - confirmSignIn():   Neues Passwort setzen (Erst-Login)
 *   - signOut():         Ausloggen
 *   - getCurrentUser():  Aktuell eingeloggter Cognito-Nutzer
 */
import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  signIn,
  signOut,
  getCurrentUser,
  confirmSignIn,
  type SignInOutput,
} from 'aws-amplify/auth'
import { usersApi } from '@/api/users'
import type { User } from '@/types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<SignInOutput>
  confirmNewPassword: (newPassword: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Beim App-Start: prüfen ob bereits eingeloggt (Token im Browser-Speicher)
  useEffect(() => {
    checkAuthState()
  }, [])

  async function checkAuthState() {
    try {
      // getCurrentUser() wirft einen Fehler wenn nicht eingeloggt
      await getCurrentUser()
      // Nutzerdaten vom Backend laden
      const userData = await usersApi.me()
      setUser(userData)
    } catch {
      // Nicht eingeloggt oder Token abgelaufen
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  async function login(email: string, password: string): Promise<SignInOutput> {
    const result = await signIn({ username: email, password })

    // Wenn Login erfolgreich und kein weiterer Schritt nötig
    if (result.isSignedIn) {
      const userData = await usersApi.me()
      setUser(userData)
    }

    // result.nextStep kann sein:
    //   CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED → Erst-Login
    //   DONE → Fertig
    return result
  }

  async function confirmNewPassword(newPassword: string): Promise<void> {
    await confirmSignIn({ challengeResponse: newPassword })
    const userData = await usersApi.me()
    setUser(userData)
  }

  async function logout(): Promise<void> {
    await signOut()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        confirmNewPassword,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// Custom Hook für einfachen Zugriff auf den Auth-Context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth muss innerhalb von AuthProvider verwendet werden.')
  }
  return context
}
