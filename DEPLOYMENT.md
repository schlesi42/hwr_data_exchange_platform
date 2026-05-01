# Deployment-Anleitung

## Übersicht

Das Deployment erfolgt in zwei Wegen:
- **Lokal (empfohlen zum Start):** AWS CDK CLI direkt vom Terminal
- **Automatisch (später):** GitHub Actions bei jedem Push auf `main`

---

## Teil 1: Einmalige Voraussetzungen

### 1.1 AWS CLI installieren und konfigurieren

```bash
# macOS
brew install awscli

# Anmelden (du brauchst deinen AWS Access Key)
aws configure
# AWS Access Key ID: [dein Key]
# AWS Secret Access Key: [dein Secret]
# Default region: eu-central-1
# Default output format: json
```

Deinen Access Key findest du in der AWS Console unter:
**IAM → Users → [dein User] → Security credentials → Access keys**

### 1.2 AWS CDK CLI installieren

```bash
npm install -g aws-cdk

# Testen
cdk --version  # sollte 2.x.x ausgeben
```

### 1.3 Docker installieren

Docker wird gebraucht, um das Lambda-Docker-Image zu bauen.

- Download: https://www.docker.com/products/docker-desktop/
- Nach der Installation: Docker starten und `docker ps` testen

### 1.4 Python-Umgebung für CDK

```bash
cd infrastructure/
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 1.5 Domain registrieren

1. AWS Console öffnen → **Route 53** → **Register domains**
2. Domain `hwr-fb2-dozierenden-portal.de` suchen und kaufen (~12€/Jahr)
3. Nach der Registrierung (kann 24h dauern) ist die Hosted Zone automatisch angelegt

---

## Teil 2: Erstes Deployment

### 2.1 CDK Bootstrap (einmalig!)

CDK benötigt S3-Buckets und IAM-Rollen in deinem AWS-Account,
bevor es zum ersten Mal deployen kann. Das heißt "Bootstrap":

```bash
cd infrastructure/
source .venv/bin/activate

# Bootstrap in beiden Regionen (us-east-1 für Zertifikat, eu-central-1 für alles andere)
cdk bootstrap aws://DEIN_ACCOUNT_ID/us-east-1
cdk bootstrap aws://DEIN_ACCOUNT_ID/eu-central-1
```

Deine Account-ID findest du in der AWS Console oben rechts (12-stellige Zahl).

### 2.2 Stacks deployen

```bash
cd infrastructure/
source .venv/bin/activate

# Beide Stacks deployen (CertStack zuerst, dann PlatformStack)
cdk deploy --all
```

CDK zeigt dir vor dem Deployment eine Zusammenfassung der Änderungen
und fragt zur Bestätigung. Tippe `y` und Enter.

**Wichtig:** Das erste Deployment dauert ca. 15-20 Minuten, weil:
- Das Docker-Image gebaut werden muss
- RDS PostgreSQL provisioniert wird
- CloudFront-Distribution erstellt wird
- TLS-Zertifikat ausgestellt wird (DNS-Validierung)

### 2.3 CDK-Outputs notieren

Nach dem Deployment zeigt CDK die wichtigen Werte an:

```
Outputs:
HwrPlatformStack.FrontendUrl        = https://hwr-fb2-dozierenden-portal.de
HwrPlatformStack.ApiUrl             = https://api.hwr-fb2-dozierenden-portal.de
HwrPlatformStack.CognitoUserPoolId  = eu-central-1_XXXXXXXXX
HwrPlatformStack.CognitoClientId    = XXXXXXXXXXXXXXXXXXXXXXXXXX
HwrPlatformStack.UploadsBucketName  = hwrplatformstack-uploadsbucketXXXXX
HwrPlatformStack.WebsiteBucketName  = hwrplatformstack-websitebucketXXXXX
HwrPlatformStack.CloudFrontDistributionId = EXXXXXXXXXXXXXXXXX
```

**Diese Werte bitte notieren!** Du brauchst sie in den nächsten Schritten.

---

## Teil 3: SES aus dem Sandbox-Modus holen

AWS SES startet im "Sandbox-Modus": Emails können nur an verifizierte Adressen gesendet werden.
Für echten Betrieb musst du Production-Zugang beantragen:

1. AWS Console → **SES** → **Account dashboard**
2. Klick auf **Request production access**
3. Formular ausfüllen:
   - Website URL: `https://hwr-fb2-dozierenden-portal.de`
   - Use case: Transactional emails für Dokumentenanforderungen
   - Expected volume: < 1000 Emails/Monat
4. Genehmigung kommt meist innerhalb von 24h

**Bis zur Genehmigung:** Im Sandbox-Modus kannst du trotzdem testen,
wenn du Empfänger-E-Mails vorher in SES verifizierst.

---

## Teil 4: Datenbank migrieren

```bash
cd backend/

# Python-Umgebung anlegen
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# .env für lokale DB-Verbindung anlegen (für Migrationen)
# Zugangsdaten findest du im AWS Secrets Manager
cat > .env << EOF
DB_HOST=DEIN_RDS_ENDPOINT.eu-central-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=hwrportal
DB_USER=hwrdbadmin
DB_PASSWORD=DEIN_PASSWORT_AUS_SECRETS_MANAGER
COGNITO_USER_POOL_ID=eu-central-1_XXXXXXXXX
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
AWS_REGION_NAME=eu-central-1
FRONTEND_URL=https://hwr-fb2-dozierenden-portal.de
EOF

# Migrationen anwenden
alembic upgrade head
```

Das RDS-Passwort findest du in der AWS Console:
**Secrets Manager → hwrdbadmin-XXXX → Retrieve secret value**

---

## Teil 5: Standard E-Mail-Templates anlegen

Nach der DB-Migration: Templates über die API anlegen.

```bash
# Backend lokal starten
uvicorn app.main:app --reload

# In einem anderen Terminal: Templates anlegen
curl -X POST http://localhost:8000/api/v1/templates/seed-defaults \
  -H "Authorization: Bearer DEIN_JWT_TOKEN"
```

---

## Teil 6: Frontend konfigurieren und deployen

### 6.1 .env.local für lokale Entwicklung

```bash
cd frontend/

cat > .env.local << EOF
VITE_API_URL=https://api.hwr-fb2-dozierenden-portal.de/api
VITE_COGNITO_USER_POOL_ID=eu-central-1_XXXXXXXXX   # aus CDK-Output
VITE_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX    # aus CDK-Output
VITE_AWS_REGION=eu-central-1
EOF
```

### 6.2 Frontend bauen und zu S3 deployen

```bash
cd frontend/
npm install
npm run build

# Zu S3 hochladen (BUCKET_NAME aus CDK-Output)
aws s3 sync dist/ s3://DEIN_WEBSITE_BUCKET_NAME --delete

# CloudFront Cache leeren (DISTRIBUTION_ID aus CDK-Output)
aws cloudfront create-invalidation \
  --distribution-id DEINE_DISTRIBUTION_ID \
  --paths "/*"
```

---

## Teil 7: Ersten Admin-Nutzer anlegen

```bash
# Über AWS CLI direkt in Cognito anlegen
aws cognito-idp admin-create-user \
  --user-pool-id eu-central-1_XXXXXXXXX \
  --username admin@deine-email.de \
  --user-attributes Name=email,Value=admin@deine-email.de \
                    Name=email_verified,Value=true \
                    Name="custom:role",Value=admin \
  --desired-delivery-mediums EMAIL

# Admin-Gruppe zuweisen
aws cognito-idp admin-add-user-to-group \
  --user-pool-id eu-central-1_XXXXXXXXX \
  --username admin@deine-email.de \
  --group-name admin
```

Dann im Backend (via API oder direkt in DB):

```sql
INSERT INTO users (email, role, is_active, created_at)
VALUES ('admin@deine-email.de', 'admin', true, NOW());
```

---

## Teil 8: GitHub Actions einrichten (für automatisches Deployment)

### 8.1 GitHub Secrets hinterlegen

Gehe zu deinem GitHub-Repository → **Settings → Secrets and variables → Actions**

Folgende Secrets anlegen:

| Name | Wert | Woher |
|------|------|-------|
| `AWS_ACCESS_KEY_ID` | Dein AWS Access Key | IAM |
| `AWS_SECRET_ACCESS_KEY` | Dein AWS Secret | IAM |
| `AWS_ACCOUNT_ID` | 12-stellige Account-ID | AWS Console oben rechts |
| `COGNITO_USER_POOL_ID` | `eu-central-1_XXXXXXXXX` | CDK-Output |
| `COGNITO_CLIENT_ID` | Client-ID | CDK-Output |
| `FRONTEND_BUCKET_NAME` | Bucket-Name | CDK-Output |
| `CLOUDFRONT_DISTRIBUTION_ID` | Distribution-ID | CDK-Output |

### 8.2 IAM-Berechtigungen für GitHub Actions

Der GitHub Actions-Nutzer (dein IAM User) braucht ausreichend Rechte.
Für den Anfang kannst du `AdministratorAccess` nutzen.
Für Produktion: minimale Rechte über eine Custom Policy.

### 8.3 Testen

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

Dann auf GitHub → **Actions** schauen: Der Workflow sollte starten.

---

## Lokale Entwicklung

### Backend lokal starten

```bash
cd backend/
source .venv/bin/activate

# .env anlegen (siehe oben)

# DB lokal via Docker starten
docker run -d \
  --name hwr-postgres \
  -e POSTGRES_DB=hwrportal \
  -e POSTGRES_USER=hwrdbadmin \
  -e POSTGRES_PASSWORD=localpassword \
  -p 5432:5432 \
  postgres:15

# .env für lokale DB
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hwrportal
DB_USER=hwrdbadmin
DB_PASSWORD=localpassword
COGNITO_USER_POOL_ID=eu-central-1_XXXXXXXXX
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
AWS_REGION_NAME=eu-central-1
FRONTEND_URL=http://localhost:5173
S3_UPLOADS_BUCKET=local-bucket   # wird lokal nicht wirklich genutzt
EOF

# Migrationen
alembic upgrade head

# Server starten (automatisch neu laden bei Änderungen)
uvicorn app.main:app --reload --port 8000

# API-Dokumentation: http://localhost:8000/api/docs
```

### Frontend lokal starten

```bash
cd frontend/
npm install

# .env.local anlegen (zeigt auf lokales Backend)
cat > .env.local << EOF
VITE_API_URL=http://localhost:8000/api
VITE_COGNITO_USER_POOL_ID=eu-central-1_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_AWS_REGION=eu-central-1
EOF

npm run dev
# App läuft auf: http://localhost:5173
```

---

## Kosten-Übersicht (geschätzt)

| Service | ~Kosten/Monat |
|---------|---------------|
| RDS PostgreSQL (db.t3.micro) | ~18€ |
| Lambda (free tier: 1M Requests) | ~0€ |
| S3 (Dateien + Frontend) | ~1-2€ |
| CloudFront | ~1€ |
| API Gateway | ~1€ |
| Route53 (Hosted Zone) | ~0.50€ |
| SES | ~0€ (bis 62k E-Mails/Monat) |
| Cognito (bis 50k MAU) | ~0€ |
| **Gesamt** | **~22-25€/Monat** |

---

## Häufige Fehler & Lösungen

### "Stack does not exist"
→ Erst `cdk bootstrap` ausführen, dann `cdk deploy`.

### "Certificate not found" beim CloudFront-Deployment
→ Warte bis die Route53 Hosted Zone DNS-Records propagiert sind (bis 48h).
   Prüfe mit: `dig hwr-fb2-dozierenden-portal.de NS`

### "Connection refused" beim Backend
→ Prüfe Security Group der RDS-Instanz: Port 5432 muss offen sein.

### "Email not verified" bei SES
→ SES ist noch im Sandbox-Modus. Entweder Production Access beantragen
   oder Empfänger-E-Mail in SES verifizieren (für Tests).

### Alembic "Target database is not up to date"
→ `alembic upgrade head` ausführen.
