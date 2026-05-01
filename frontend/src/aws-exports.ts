/**
 * AWS Amplify Konfiguration.
 *
 * Diese Werte kommen aus Umgebungsvariablen (VITE_*),
 * die nach dem CDK-Deployment in .env.local eingetragen werden.
 * Die genauen Werte gibt CDK nach dem Deployment als Outputs aus.
 *
 * Lokale Entwicklung: frontend/.env.local anlegen mit:
 *   VITE_API_URL=http://localhost:8000
 *   VITE_COGNITO_USER_POOL_ID=eu-central-1_XXXXXXXXX
 *   VITE_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
 *   VITE_AWS_REGION=eu-central-1
 */
import { Amplify } from 'aws-amplify'

export function configureAmplify() {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
        userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
        loginWith: {
          email: true,
        },
      },
    },
  })
}
