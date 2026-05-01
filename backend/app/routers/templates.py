"""
Router: E-Mail-Templates verwalten.

Büros können Templates für ihren Fachbereich anlegen und bearbeiten.
Admins können globale Templates (department_id=None) verwalten.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin, CurrentUser
from app.models.email_template import EmailTemplate
from app.schemas.email_template import (
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse
)

router = APIRouter()

# Standard-Templates für neue Fachbereiche
DEFAULT_TEMPLATES = [
    {
        "type": "request",
        "subject": "Neue Dokumentenanforderung: {{title}}",
        "body_html": """
<p>Guten Tag {{name}},</p>
<p>das Fachbereichsbüro hat folgende Dokumente angefordert:</p>
<p><strong>{{title}}</strong></p>
<p>{{description}}</p>
<p><strong>Deadline: {{deadline}}</strong></p>
<p>Bitte laden Sie Ihre Dokumente bis zu diesem Datum hoch:</p>
<p><a href="{{upload_url}}">Jetzt Dokumente hochladen</a></p>
<p>Mit freundlichen Grüßen<br>Ihr Fachbereichsbüro</p>
""",
    },
    {
        "type": "reminder",
        "subject": "Erinnerung: Dokumente bis {{deadline}} einreichen",
        "body_html": """
<p>Guten Tag {{name}},</p>
<p>wir möchten Sie daran erinnern, dass die Dokumente für
<strong>{{title}}</strong> noch fehlen.</p>
<p><strong>Deadline: {{deadline}} (noch {{days_until_deadline}} Tage)</strong></p>
<p><a href="{{upload_url}}">Jetzt Dokumente hochladen</a></p>
<p>Mit freundlichen Grüßen<br>Ihr Fachbereichsbüro</p>
""",
    },
    {
        "type": "overdue",
        "subject": "DRINGEND: Dokumente für {{title}} überfällig",
        "body_html": """
<p>Guten Tag {{name}},</p>
<p>die Deadline für <strong>{{title}}</strong> ist abgelaufen.
Wir bitten Sie, die Dokumente umgehend einzureichen.</p>
<p><a href="{{upload_url}}">Jetzt Dokumente hochladen</a></p>
<p>Bei Fragen wenden Sie sich bitte an Ihr Fachbereichsbüro.</p>
<p>Mit freundlichen Grüßen<br>Ihr Fachbereichsbüro</p>
""",
    },
]


@router.get("/", response_model=list[EmailTemplateResponse])
def list_templates(
    department_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Templates auflisten (global + fachbereichsspezifisch)."""
    query = db.query(EmailTemplate)
    if department_id:
        query = query.filter(
            (EmailTemplate.department_id == department_id) |
            (EmailTemplate.department_id.is_(None))
        )
    return query.order_by(EmailTemplate.type).all()


@router.post("/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    data: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Template anlegen."""
    # Büros können nur Templates für ihren Fachbereich anlegen
    if current_user.is_buero():
        data.department_id = current_user.department_id

    template = EmailTemplate(**data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=EmailTemplateResponse)
def update_template(
    template_id: int,
    data: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Template bearbeiten."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template nicht gefunden.")

    if current_user.is_buero() and template.department_id != current_user.department_id:
        raise HTTPException(status_code=403, detail="Kein Zugriff.")

    if data.subject is not None:
        template.subject = data.subject
    if data.body_html is not None:
        template.body_html = data.body_html

    db.commit()
    db.refresh(template)
    return template


@router.post("/seed-defaults", status_code=status.HTTP_201_CREATED)
def seed_default_templates(
    department_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """
    Standard-Templates anlegen (nur Admin).

    Nützlich beim ersten Setup oder für einen neuen Fachbereich.
    """
    created = []
    for tmpl_data in DEFAULT_TEMPLATES:
        template = EmailTemplate(
            department_id=department_id,
            **tmpl_data,
        )
        db.add(template)
        created.append(tmpl_data["type"])

    db.commit()
    return {"created": created, "department_id": department_id}
