"""
Router: Nutzerverwaltung.

Admins: können alle Nutzer sehen, anlegen, deaktivieren.
Büros: können Dozenten ihres Fachbereichs anlegen und sehen.
Dozenten: können nur ihr eigenes Profil sehen.

Onboarding-Ablauf:
  1. Büro gibt E-Mail + Rolle ein → POST /users/
  2. Backend legt Nutzer in DB und Cognito an
  3. Cognito sendet automatisch Einladungs-E-Mail mit temporärem Passwort
  4. Dozent loggt sich ein, muss Passwort ändern (Cognito erzwingt das)
"""
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin, require_buero_or_admin, CurrentUser
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()


def _create_cognito_user(email: str, role: str, department_id: int | None) -> None:
    """
    Legt Nutzer in Cognito an und fügt ihn der richtigen Gruppe hinzu.
    Cognito verschickt automatisch die Einladungs-E-Mail.
    """
    settings = get_settings()
    cognito = boto3.client("cognito-idp", region_name=settings.aws_region_name)

    try:
        # Nutzer anlegen (Cognito verschickt Einladungs-E-Mail automatisch)
        cognito.admin_create_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:role", "Value": role},
                {"Name": "custom:department_id", "Value": str(department_id or "")},
            ],
            # DesiredDeliveryMediums: E-Mail wird automatisch gesendet
            DesiredDeliveryMediums=["EMAIL"],
        )

        # Nutzer zur richtigen Gruppe hinzufügen
        cognito.admin_add_user_to_group(
            UserPoolId=settings.cognito_user_pool_id,
            Username=email,
            GroupName=role,
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "UsernameExistsException":
            raise HTTPException(
                status_code=400,
                detail=f"E-Mail {email} ist bereits in Cognito registriert."
            )
        raise HTTPException(status_code=500, detail=f"Cognito-Fehler: {str(e)}")


def _enrich_user_response(user: User, db: Session) -> UserResponse:
    """Fügt department_name zum UserResponse hinzu."""
    response = UserResponse.model_validate(user)
    if user.department_id:
        dept = db.query(Department).filter(Department.id == user.department_id).first()
        response.department_name = dept.name if dept else None
    return response


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Eigenes Profil abrufen."""
    return _enrich_user_response(current_user.user, db)


@router.get("/", response_model=list[UserResponse])
def list_users(
    department_id: int | None = None,
    role: UserRole | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Nutzer auflisten. Büros sehen nur ihren Fachbereich."""
    query = db.query(User)

    # Büros sehen nur Nutzer ihres Fachbereichs
    if current_user.is_buero():
        query = query.filter(User.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(User.department_id == department_id)

    if role:
        query = query.filter(User.role == role)

    users = query.order_by(User.email).all()
    return [_enrich_user_response(u, db) for u in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_buero_or_admin),
):
    """
    Neuen Nutzer anlegen.

    Büros können nur Dozenten für ihren Fachbereich anlegen.
    Admins können beliebige Nutzer anlegen.
    """
    # Büros dürfen nur Dozenten in ihrem Fachbereich anlegen
    if current_user.is_buero():
        if data.role != UserRole.dozent:
            raise HTTPException(status_code=403, detail="Büros können nur Dozenten anlegen.")
        if data.department_id and data.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Nur Dozenten des eigenen Fachbereichs.")
        data.department_id = current_user.department_id

    # E-Mail-Duplikat prüfen
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail=f"E-Mail {data.email} bereits vorhanden.")

    # Cognito-Nutzer anlegen (verschickt Einladungs-E-Mail)
    _create_cognito_user(data.email, data.role.value, data.department_id)

    # DB-Eintrag anlegen
    user = User(
        email=data.email,
        name=data.name,
        role=data.role,
        department_id=data.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _enrich_user_response(user, db)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """Nutzerdaten aktualisieren (nur Admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Nutzer nicht gefunden.")

    if data.name is not None:
        user.name = data.name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.department_id is not None:
        user.department_id = data.department_id

    db.commit()
    db.refresh(user)
    return _enrich_user_response(user, db)
