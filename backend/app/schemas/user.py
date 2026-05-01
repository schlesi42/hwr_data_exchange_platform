from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Neuen Nutzer anlegen (vom Admin oder Büro)."""
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    department_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Nutzerdaten aktualisieren."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None


class UserResponse(BaseModel):
    """Nutzerdaten für das Frontend."""
    id: int
    email: str
    name: Optional[str]
    role: UserRole
    department_id: Optional[int]
    department_name: Optional[str] = None  # wird im Router befüllt
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
