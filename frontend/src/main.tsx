/**
 * Einstiegspunkt der React-Anwendung.
 *
 * Reihenfolge:
 *   1. Tailwind CSS importieren
 *   2. AWS Amplify konfigurieren (Cognito)
 *   3. React-App rendern
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { configureAmplify } from './aws-exports'
import App from './App'

// AWS Amplify einmalig konfigurieren
configureAmplify()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
