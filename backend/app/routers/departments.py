"""
Router: Fachbereiche (Departments).

Nur Admins können Fachbereiche anlegen, bearbeiten und löschen.
Büros können ihre eigenen Fachbereichsdaten lesen.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin, CurrentUser
from app.models.department import Department, ReminderConfig
from app.schemas.department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    ReminderConfigUpdate, ReminderConfigResponse,
)

router = APIRouter()


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Alle Fachbereiche auflisten."""
    return db.query(Department).order_by(Department.name).all()


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """Neuen Fachbereich anlegen (nur Admin)."""
    if db.query(Department).filter(Department.slug == data.slug).first():
        raise HTTPException(status_code=400, detail=f"Slug '{data.slug}' bereits vergeben.")

    dept = Department(name=data.name, slug=data.slug)
    db.add(dept)
    db.flush()  # ID generieren

    # Standard Reminder-Config anlegen
    reminder = ReminderConfig(department_id=dept.id)
    db.add(reminder)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """Fachbereich aktualisieren (nur Admin)."""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Fachbereich nicht gefunden.")

    if data.name is not None:
        dept.name = data.name
    if data.slug is not None:
        dept.slug = data.slug

    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """Fachbereich löschen (nur Admin). Vorsicht: löscht auch alle zugehörigen Daten!"""
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Fachbereich nicht gefunden.")

    db.delete(dept)
    db.commit()


@router.get("/{dept_id}/reminder-config", response_model=ReminderConfigResponse)
def get_reminder_config(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    config = db.query(ReminderConfig).filter(
        ReminderConfig.department_id == dept_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Keine Reminder-Konfiguration gefunden.")
    return config


@router.put("/{dept_id}/reminder-config", response_model=ReminderConfigResponse)
def update_reminder_config(
    dept_id: int,
    data: ReminderConfigUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Reminder-Konfiguration aktualisieren (Admin oder eigenes Büro)."""
    if not current_user.is_admin() and current_user.department_id != dept_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diesen Fachbereich.")

    config = db.query(ReminderConfig).filter(
        ReminderConfig.department_id == dept_id
    ).first()
    if not config:
        config = ReminderConfig(department_id=dept_id)
        db.add(config)

    config.days_before = data.days_before
    config.send_overdue = data.send_overdue
    config.overdue_interval_days = data.overdue_interval_days
    db.commit()
    db.refresh(config)
    return config
