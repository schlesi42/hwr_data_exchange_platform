from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.document_request import RequestStatus, AssignmentStatus


class UploadedFileResponse(BaseModel):
    id: int
    filename: str
    size_bytes: int
    content_type: str
    uploaded_at: datetime
    download_url: Optional[str] = None  # Pre-signed URL, im Router befüllt

    model_config = {"from_attributes": True}


class AssignmentResponse(BaseModel):
    id: int
    request_id: int
    dozent_id: int
    dozent_email: str = ""        # im Router befüllt
    dozent_name: Optional[str] = None  # im Router befüllt
    status: AssignmentStatus
    submitted_at: Optional[datetime]
    files: list[UploadedFileResponse] = []

    model_config = {"from_attributes": True}


class DocumentRequestCreate(BaseModel):
    """Neue Dokumentenanforderung erstellen."""
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None
    deadline: datetime
    # Liste der Dozenten-IDs, die aufgefordert werden sollen
    dozent_ids: list[int] = Field(..., min_length=1)


class DocumentRequestUpdate(BaseModel):
    """Anforderung aktualisieren (nur vor dem Versand sinnvoll)."""
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    deadline: Optional[datetime] = None


class DocumentRequestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    department_id: int
    department_name: str = ""  # im Router befüllt
    created_by: int
    deadline: datetime
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    assignments: list[AssignmentResponse] = []

    model_config = {"from_attributes": True}


class DocumentRequestSummary(BaseModel):
    """Kurz-Zusammenfassung für das Dashboard (ohne assignments)."""
    id: int
    title: str
    department_id: int
    department_name: str = ""
    deadline: datetime
    status: RequestStatus
    created_at: datetime
    total_assignments: int = 0
    uploaded_count: int = 0

    model_config = {"from_attributes": True}
