"""
Modelle: Fachbereich (Department) und Reminder-Konfiguration.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.document_request import DocumentRequest
    from app.models.email_template import EmailTemplate


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    # slug: URL-freundlicher Name, z.B. "wirtschaftsinformatik"
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Beziehungen (lazy geladen)
    users: Mapped[list["User"]] = relationship(back_populates="department")
    requests: Mapped[list["DocumentRequest"]] = relationship(back_populates="department")
    reminder_config: Mapped[Optional["ReminderConfig"]] = relationship(
        back_populates="department", uselist=False
    )
    email_templates: Mapped[list["EmailTemplate"]] = relationship(
        back_populates="department"
    )

    def __repr__(self):
        return f"<Department {self.name}>"


class ReminderConfig(Base):
    """
    Konfiguriert, wann Erinnerungs-Emails für einen Fachbereich versendet werden.

    days_before: kommagetrennte Liste, z.B. "7,3,1" bedeutet:
                 Erinnerung 7 Tage, 3 Tage und 1 Tag vor Deadline.
    """
    __tablename__ = "reminder_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        Integer,
        # ForeignKey direkt als String (vermeidet zirkuläre Imports)
        nullable=False,
        unique=True,
    )
    # Kommagetrennt: "7,3,1" = Erinnerung 7, 3 und 1 Tag vor Deadline
    days_before: Mapped[str] = mapped_column(String(100), default="7,3,1")
    # Mahnung bei überschrittener Deadline?
    send_overdue: Mapped[bool] = mapped_column(Boolean, default=True)
    # Wie oft nach Deadline erinnern (alle N Tage)
    overdue_interval_days: Mapped[int] = mapped_column(Integer, default=3)

    department: Mapped["Department"] = relationship(back_populates="reminder_config")

    @property
    def days_before_list(self) -> list[int]:
        """Gibt die days_before-Tage als Integer-Liste zurück."""
        return [int(d.strip()) for d in self.days_before.split(",") if d.strip()]
