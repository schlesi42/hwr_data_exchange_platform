"""
Modell: E-Mail-Templates.

Templates können global (department_id=None) oder
fachbereichsspezifisch sein.

Template-Typen:
  invitation  – Einladung neuer Dozenten zum Portal
  request     – Neue Dokumentenanforderung
  reminder    – Erinnerung vor Deadline
  overdue     – Mahnung nach Deadline
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.department import Department

TEMPLATE_TYPES = ["invitation", "request", "reminder", "overdue"]


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # NULL = globales Standard-Template; sonst fachbereichsspezifisch
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    # HTML-Body mit Platzhaltern, z.B. {{name}}, {{deadline}}, {{title}}
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    department: Mapped[Optional["Department"]] = relationship(
        back_populates="email_templates"
    )
