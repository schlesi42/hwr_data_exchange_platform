"""
Router: Dokumentenanforderungen (Document Requests).

Dies ist der Kern der Plattform.

Büros:
  - Anforderungen erstellen (mit Deadline und Dozenten-Zuweisung)
  - Eigene Anforderungen sehen und verwalten
  - E-Mail-Benachrichtigung an Dozenten beim Erstellen

Dozenten:
  - Eigene zugewiesene Anforderungen sehen
  - Upload-URLs anfordern

Admins:
  - Alle Anforderungen sehen
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_buero_or_admin, CurrentUser
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.document_request import (
    DocumentRequest, RequestAssignment, AssignmentStatus, RequestStatus
)
from app.schemas.document_request import (
    DocumentRequestCreate, DocumentRequestUpdate,
    DocumentRequestResponse, DocumentRequestSummary, AssignmentResponse,
)
from app.services.email import send_request_notification

router = APIRouter()


def _build_assignment_response(assignment: RequestAssignment) -> AssignmentResponse:
    """Reichert eine Assignment mit Dozenten-Daten an."""
    resp = AssignmentResponse.model_validate(assignment)
    resp.dozent_email = assignment.dozent.email
    resp.dozent_name = assignment.dozent.name
    return resp


def _build_request_response(req: DocumentRequest, db: Session) -> DocumentRequestResponse:
    """Baut die vollständige Request-Response mit allen Zuweisungen."""
    dept = db.query(Department).filter(Department.id == req.department_id).first()
    resp = DocumentRequestResponse.model_validate(req)
    resp.department_name = dept.name if dept else ""
    resp.assignments = [_build_assignment_response(a) for a in req.assignments]
    return resp


@router.get("/", response_model=list[DocumentRequestSummary])
def list_requests(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Anforderungen auflisten.

    Admins: alle
    Büros: nur ihr Fachbereich
    Dozenten: nur eigene Zuweisungen
    """
    if current_user.is_admin():
        requests = db.query(DocumentRequest).order_by(
            DocumentRequest.deadline.asc()
        ).all()
    elif current_user.is_buero():
        requests = db.query(DocumentRequest).filter(
            DocumentRequest.department_id == current_user.department_id
        ).order_by(DocumentRequest.deadline.asc()).all()
    else:
        # Dozent: Anforderungen über Assignments finden
        assignments = db.query(RequestAssignment).filter(
            RequestAssignment.dozent_id == current_user.user.id
        ).all()
        request_ids = [a.request_id for a in assignments]
        requests = db.query(DocumentRequest).filter(
            DocumentRequest.id.in_(request_ids)
        ).order_by(DocumentRequest.deadline.asc()).all()

    result = []
    for req in requests:
        dept = db.query(Department).filter(Department.id == req.department_id).first()
        summary = DocumentRequestSummary.model_validate(req)
        summary.department_name = dept.name if dept else ""
        summary.total_assignments = len(req.assignments)
        summary.uploaded_count = sum(
            1 for a in req.assignments if a.status == AssignmentStatus.uploaded
        )
        result.append(summary)
    return result


@router.post("/", response_model=DocumentRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    data: DocumentRequestCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_buero_or_admin),
):
    """
    Neue Dokumentenanforderung erstellen.

    Erstellt Anforderung + Zuweisungen und versendet E-Mails an alle Dozenten.
    """
    if data.deadline <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Deadline muss in der Zukunft liegen.")

    department_id = current_user.department_id
    if current_user.is_admin():
        # Admin muss einen Fachbereich angeben (über query param oder im Body erweitern)
        # Vereinfacht: Admin nutzt den ersten FB oder wir erweitern das Schema später
        raise HTTPException(
            status_code=400,
            detail="Admins müssen einen Fachbereich als Parameter angeben. "
                   "Bitte als Büro-Nutzer des Fachbereichs anmelden."
        )

    # Prüfen, ob alle Dozenten-IDs valide sind und zum Fachbereich gehören
    dozents = []
    for dozent_id in data.dozent_ids:
        dozent = db.query(User).filter(
            User.id == dozent_id,
            User.role == UserRole.dozent,
            User.is_active == True,
        ).first()
        if not dozent:
            raise HTTPException(
                status_code=400,
                detail=f"Dozent mit ID {dozent_id} nicht gefunden oder inaktiv."
            )
        dozents.append(dozent)

    # Anforderung anlegen
    req = DocumentRequest(
        title=data.title,
        description=data.description,
        department_id=department_id,
        created_by=current_user.user.id,
        deadline=data.deadline,
        status=RequestStatus.open,
    )
    db.add(req)
    db.flush()  # ID generieren ohne commit

    # Zuweisungen und E-Mails
    for dozent in dozents:
        assignment = RequestAssignment(
            request_id=req.id,
            dozent_id=dozent.id,
            status=AssignmentStatus.pending,
        )
        db.add(assignment)
        db.flush()

        # E-Mail an Dozenten senden
        send_request_notification(
            db=db,
            to_email=dozent.email,
            dozent_name=dozent.name or dozent.email,
            request_title=data.title,
            request_description=data.description,
            deadline=data.deadline,
            assignment_id=assignment.id,
            department_id=department_id,
        )

    db.commit()
    db.refresh(req)
    return _build_request_response(req, db)


@router.get("/{request_id}", response_model=DocumentRequestResponse)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Details einer Anforderung abrufen."""
    req = db.query(DocumentRequest).filter(DocumentRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Anforderung nicht gefunden.")

    # Zugriffsprüfung
    if current_user.is_buero() and req.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff.")
    if current_user.is_dozent():
        has_assignment = any(
            a.dozent_id == current_user.user.id for a in req.assignments
        )
        if not has_assignment:
            raise HTTPException(status_code=403, detail="Kein Zugriff.")

    return _build_request_response(req, db)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_buero_or_admin),
):
    """Anforderung löschen (Büro oder Admin)."""
    req = db.query(DocumentRequest).filter(DocumentRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Anforderung nicht gefunden.")

    if current_user.is_buero() and req.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff.")

    db.delete(req)
    db.commit()
