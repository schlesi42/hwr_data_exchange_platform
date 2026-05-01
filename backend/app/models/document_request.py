"""
Modelle: Dokumentenanforderung, Zuweisung, hochgeladene Datei.

Ablauf:
  1. Büro erstellt DocumentRequest mit Deadline
  2. Büro weist Dozenten zu → RequestAssignment (status=pending)
  3. Dozent lädt Datei hoch → UploadedFile, Assignment status=uploaded
  4. Deadline verstrichen ohne Upload → status=overdue
"""
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, DateTime, Text, ForeignKey,
    Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.user import User


class RequestStatus(str, enum.Enum):
    """Status einer gesamten Anforderung."""
    open = "open"           # Offen, mind. eine Zuweisung ausstehend
    partial = "partial"     # Einige haben geliefert, nicht alle
    completed = "completed" # Alle haben geliefert
    overdue = "overdue"     # Deadline verstrichen, noch nicht vollständig


class AssignmentStatus(str, enum.Enum):
    """Status einer einzelnen Dozenten-Zuweisung."""
    pending = "pending"     # Ausstehend
    uploaded = "uploaded"   # Dokument hochgeladen
    overdue = "overdue"     # Deadline verstrichen ohne Upload


class DocumentRequest(Base):
    """Eine Dokumentenanforderung eines Fachbereichsbüros."""
    __tablename__ = "document_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        SQLEnum(RequestStatus), default=RequestStatus.open
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Beziehungen
    department: Mapped["Department"] = relationship(back_populates="requests")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    assignments: Mapped[list["RequestAssignment"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )

    def update_status(self):
        """Aktualisiert den Gesamt-Status basierend auf den Zuweisungen."""
        if not self.assignments:
            return
        statuses = {a.status for a in self.assignments}
        if all(s == AssignmentStatus.uploaded for s in statuses):
            self.status = RequestStatus.completed
        elif all(s == AssignmentStatus.overdue for s in statuses):
            self.status = RequestStatus.overdue
        elif AssignmentStatus.uploaded in statuses:
            self.status = RequestStatus.partial
        elif datetime.utcnow() > self.deadline:
            self.status = RequestStatus.overdue
        else:
            self.status = RequestStatus.open


class RequestAssignment(Base):
    """Zuweisung einer Anforderung an einen bestimmten Dozenten."""
    __tablename__ = "request_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("document_requests.id"), nullable=False
    )
    dozent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SQLEnum(AssignmentStatus), default=AssignmentStatus.pending
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # Zeitstempel der letzten gesendeten Erinnerung (für Throttling)
    last_reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # Anzahl gesendeter Erinnerungen
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)

    # Beziehungen
    request: Mapped["DocumentRequest"] = relationship(back_populates="assignments")
    dozent: Mapped["User"] = relationship(back_populates="assignments")
    files: Mapped[list["UploadedFile"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class UploadedFile(Base):
    """Eine hochgeladene Datei, verknüpft mit einer Zuweisung."""
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("request_assignments.id"), nullable=False
    )
    # S3-Schlüssel, z.B. "uploads/2024/request-42/assignment-7/lebenslauf.pdf"
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Beziehungen
    assignment: Mapped["RequestAssignment"] = relationship(back_populates="files")
