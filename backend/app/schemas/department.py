"""
Pydantic Schemas für Departments und ReminderConfig.

Schemas sind die "Verträge" zwischen Frontend und Backend.
Sie definieren, welche Felder bei Requests/Responses erwartet werden
und validieren die Daten automatisch.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    """Daten zum Erstellen eines neuen Fachbereichs."""
    name: str = Field(..., min_length=2, max_length=200, example="Wirtschaftsinformatik")
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9\-]+$",
                      example="wirtschaftsinformatik")


class DepartmentUpdate(BaseModel):
    """Daten zum Aktualisieren eines Fachbereichs (alle Felder optional)."""
    name: str | None = Field(None, min_length=2, max_length=200)
    slug: str | None = Field(None, min_length=2, max_length=100, pattern=r"^[a-z0-9\-]+$")


class DepartmentResponse(BaseModel):
    """Fachbereich-Daten für das Frontend."""
    id: int
    name: str
    slug: str
    created_at: datetime

    # Gibt an, dass SQLAlchemy-Objekte direkt konvertiert werden können
    model_config = {"from_attributes": True}


class ReminderConfigUpdate(BaseModel):
    """Reminder-Konfiguration aktualisieren."""
    days_before: str = Field(
        "7,3,1",
        description="Kommagetrennte Tage vor Deadline, z.B. '7,3,1'",
        example="7,3,1"
    )
    send_overdue: bool = True
    overdue_interval_days: int = Field(3, ge=1, le=30)


class ReminderConfigResponse(BaseModel):
    """Reminder-Konfiguration für das Frontend."""
    id: int
    department_id: int
    days_before: str
    send_overdue: bool
    overdue_interval_days: int

    model_config = {"from_attributes": True}
