"""
Modell: Nutzer (User).

Alle Nutzer (Admin, Büro, Dozent) liegen in dieser Tabelle.
Die Rolle bestimmt, was der Nutzer sehen und tun darf.
"""
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.document_request import RequestAssignment


class UserRole(str, enum.Enum):
    """Rollen im System."""
    admin = "admin"    # Plattform-Administrator: sieht alles
    buero = "buero"    # Fachbereichsbüro: stellt Anforderungen
    dozent = "dozent"  # Dozent/Dozentin: liefert Dokumente


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(300), unique=True, index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(300))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)

    # Fachbereich: Admin hat keinen (NULL), Büro und Dozent gehören einem FB an
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )

    # Cognito Sub: eindeutige ID aus dem Cognito-Token
    # Wird gesetzt, sobald der Nutzer sich erstmals einloggt
    cognito_sub: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Beziehungen
    department: Mapped[Optional["Department"]] = relationship(back_populates="users")
    assignments: Mapped[list["RequestAssignment"]] = relationship(
        back_populates="dozent"
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
