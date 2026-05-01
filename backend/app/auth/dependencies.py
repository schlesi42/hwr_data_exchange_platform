"""
JWT-Authentifizierung mit Amazon Cognito.

Ablauf:
  1. Frontend loggt sich bei Cognito ein und erhält JWT-Token
  2. Frontend schickt Token im Header: Authorization: Bearer <token>
  3. Backend verifiziert Token gegen Cognito's öffentliche Schlüssel (JWKS)
  4. Backend liest Nutzerrolle und -ID aus dem Token

Cognito JWKS URL:
  https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json
"""
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole

# FastAPI Security-Scheme: erwartet "Authorization: Bearer <token>"
security = HTTPBearer()


@lru_cache(maxsize=1)
def get_cognito_jwks() -> dict:
    """
    Lädt die öffentlichen Schlüssel von Cognito (gecacht).
    Diese werden genutzt, um die Signatur des JWT-Tokens zu prüfen.
    Gecacht, damit nicht bei jedem Request ein HTTP-Call nötig ist.
    """
    settings = get_settings()
    url = (
        f"https://cognito-idp.{settings.aws_region_name}.amazonaws.com"
        f"/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()


def verify_token(token: str) -> dict:
    """
    Verifiziert ein Cognito JWT-Token und gibt die Claims zurück.

    Claims sind die "Aussagen" im Token, z.B.:
    - sub: eindeutige Cognito User-ID
    - email: E-Mail-Adresse
    - cognito:groups: Gruppen des Nutzers ["admin", "buero", "dozent"]
    - exp: Ablaufzeitpunkt
    """
    settings = get_settings()
    try:
        jwks = get_cognito_jwks()
        # jose.jwt verifiziert Signatur, Ablaufzeit und Audience automatisch
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
            options={"verify_at_hash": False},
        )
        return claims
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Ungültiges Token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


class CurrentUser:
    """Hilfsobjekt: aktuell eingeloggter Nutzer mit DB-Eintrag."""
    def __init__(self, db_user: User, claims: dict):
        self.user = db_user
        self.claims = claims

    @property
    def role(self) -> UserRole:
        return self.user.role

    @property
    def department_id(self) -> Optional[int]:
        return self.user.department_id

    def has_role(self, *roles: UserRole) -> bool:
        """
        Generische Rollenprüfung – erweiterbar ohne neue Methoden.

        Beispiele:
            current.has_role(UserRole.admin)
            current.has_role(UserRole.buero, UserRole.admin)  # eines von beiden reicht
        """
        return self.role in roles

    # Convenience-Methoden für Lesbarkeit im Code.
    # Neue Rollen können direkt mit has_role() genutzt werden,
    # ohne hier eine neue Methode anlegen zu müssen.
    def is_admin(self) -> bool:
        return self.has_role(UserRole.admin)

    def is_buero(self) -> bool:
        return self.has_role(UserRole.buero)

    def is_dozent(self) -> bool:
        return self.has_role(UserRole.dozent)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI Dependency: Gibt den eingeloggten Nutzer zurück.

    Wird so verwendet:
        @router.get("/protected")
        def endpoint(current_user: CurrentUser = Depends(get_current_user)):
            ...
    """
    claims = verify_token(credentials.credentials)
    cognito_sub = claims.get("sub")

    # Nutzer in der DB nachschlagen
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()

    if not user:
        # Erster Login: cognito_sub noch nicht in DB
        # Versuche, den Nutzer über die E-Mail zu finden
        email = claims.get("email", "")
        user = db.query(User).filter(User.email == email).first()
        if user:
            # cognito_sub nachträglich speichern
            user.cognito_sub = cognito_sub
            db.commit()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nutzer nicht im System registriert. Bitte wenden Sie sich an den Administrator.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ihr Konto ist deaktiviert.",
        )

    return CurrentUser(db_user=user, claims=claims)


def require_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Nur für Admins."""
    if not current.is_admin():
        raise HTTPException(status_code=403, detail="Nur für Administratoren zugänglich.")
    return current


def require_buero_or_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Für Büros und Admins."""
    if not (current.is_buero() or current.is_admin()):
        raise HTTPException(status_code=403, detail="Nur für Fachbereichsbüros zugänglich.")
    return current
