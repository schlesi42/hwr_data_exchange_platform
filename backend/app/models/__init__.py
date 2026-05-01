# Alle Modelle importieren, damit Alembic sie findet
from app.models.department import Department, ReminderConfig
from app.models.user import User, UserRole
from app.models.document_request import (
    DocumentRequest,
    RequestAssignment,
    UploadedFile,
    RequestStatus,
    AssignmentStatus,
)
from app.models.email_template import EmailTemplate
