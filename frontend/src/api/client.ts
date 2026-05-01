/**
 * Axios HTTP-Client.
 *
 * Dieser Client wird für alle API-Anfragen genutzt.
 * Er fügt automatisch den JWT-Token aus Cognito als
 * Authorization-Header hinzu.
 */
import axios from 'axios'
import { fetchAuthSession } from 'aws-amplify/auth'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request-Interceptor: JWT-Token automatisch anhängen
apiClient.interceptors.request.use(async (config) => {
  try {
    const session = await fetchAuthSession()
    const token = session.tokens?.idToken?.toString()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  } catch {
    // Nicht eingeloggt – Token fehlt, Request wird trotzdem gesendet
    // (für public endpoints)
  }
  return config
})

// Response-Interceptor: 401/403 → Weiterleitung zum Login
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
