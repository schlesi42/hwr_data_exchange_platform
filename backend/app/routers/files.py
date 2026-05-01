"""
Router: Datei-Uploads und Downloads.

Pre-signed URL-Ablauf:
  1. POST /files/upload-url  → Backend gibt S3 Upload-URL zurück
  2. Frontend PUT direkt zu S3 (kein Lambda beteiligt)
  3. POST /files/confirm     → Frontend bestätigt Upload, Backend speichert in DB
  4. GET  /files/{file_id}/download → Backend gibt temporäre Download-URL zurück
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, CurrentUser
from app.models.document_request import (
    RequestAssignment, UploadedFile, AssignmentStatus
)
from app.schemas.document_request import UploadedFileResponse
from app.services.storage import generate_upload_url, generate_download_url

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


class UploadUrlRequest(BaseModel):
    assignment_id: int
    filename: str
    content_type: str
    size_bytes: int


class UploadUrlResponse(BaseModel):
    upload_url: str
    s3_key: str


class ConfirmUploadRequest(BaseModel):
    assignment_id: int
    s3_key: str
    filename: str
    content_type: str
    size_bytes: int


@router.post("/upload-url", response_model=UploadUrlResponse)
def get_upload_url(
    data: UploadUrlRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Pre-signed Upload-URL anfordern.

    Nur der zugewiesene Dozent kann eine Upload-URL für seine Zuweisung anfordern.
    """
    if data.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Dateityp nicht erlaubt. Erlaubt: PDF, Word, JPEG, PNG."
        )

    if data.size_bytes > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Datei zu groß. Maximum: 100 MB."
        )

    assignment = db.query(RequestAssignment).filter(
        RequestAssignment.id == data.assignment_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Zuweisung nicht gefunden.")

    # Nur der zugewiesene Dozent darf hochladen
    if current_user.is_dozent() and assignment.dozent_id != current_user.user.id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Zuweisung.")

    s3_key, upload_url = generate_upload_url(
        filename=data.filename,
        content_type=data.content_type,
        assignment_id=data.assignment_id,
        request_id=assignment.request_id,
    )

    return UploadUrlResponse(upload_url=upload_url, s3_key=s3_key)


@router.post("/confirm", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
def confirm_upload(
    data: ConfirmUploadRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload-Abschluss bestätigen.

    Nachdem das Frontend die Datei direkt zu S3 hochgeladen hat,
    meldet es dem Backend: "Upload fertig, speichere den Eintrag."
    """
    assignment = db.query(RequestAssignment).filter(
        RequestAssignment.id == data.assignment_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Zuweisung nicht gefunden.")

    if current_user.is_dozent() and assignment.dozent_id != current_user.user.id:
        raise HTTPException(status_code=403, detail="Kein Zugriff.")

    # Datei-Eintrag in DB speichern
    file = UploadedFile(
        assignment_id=data.assignment_id,
        s3_key=data.s3_key,
        filename=data.filename,
        content_type=data.content_type,
        size_bytes=data.size_bytes,
    )
    db.add(file)

    # Zuweisung auf "uploaded" setzen
    from datetime import datetime
    assignment.status = AssignmentStatus.uploaded
    assignment.submitted_at = datetime.utcnow()

    # Gesamt-Status der Anforderung aktualisieren
    assignment.request.update_status()

    db.commit()
    db.refresh(file)
    return file


@router.get("/{file_id}/download", response_model=UploadedFileResponse)
def get_download_url(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Pre-signed Download-URL für eine Datei anfordern."""
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")

    # Zugriffsprüfung
    assignment = file.assignment
    request = assignment.request

    if current_user.is_dozent() and assignment.dozent_id != current_user.user.id:
        raise HTTPException(status_code=403, detail="Kein Zugriff.")
    if current_user.is_buero() and request.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff.")

    download_url = generate_download_url(
        s3_key=file.s3_key,
        filename=file.filename,
    )

    response = UploadedFileResponse.model_validate(file)
    response.download_url = download_url
    return response
