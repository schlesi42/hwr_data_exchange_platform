"""
E-Mail-Versand via Amazon SES.

Ablauf für jede E-Mail:
  1. Template für den Fachbereich laden (oder globales Fallback)
  2. Platzhalter ersetzen ({{name}}, {{deadline}}, etc.)
  3. E-Mail über SES senden

Unterstützte Template-Typen:
  invitation  – Einladung zum Portal (wird von Cognito übernommen, hier optional)
  request     – Neue Dokumentenanforderung
  reminder    – Erinnerung vor Deadline
  overdue     – Mahnung nach Deadline
"""
import re
import logging
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.email_template import EmailTemplate

logger = logging.getLogger(__name__)


def get_template(db: Session, template_type: str, department_id: Optional[int]) -> Optional[EmailTemplate]:
    """
    Lädt das passende Template.

    Sucht zuerst nach einem fachbereichsspezifischen Template,
    fällt dann auf das globale Standard-Template zurück.
    """
    if department_id:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.type == template_type,
            EmailTemplate.department_id == department_id,
        ).first()
        if template:
            return template

    # Globales Fallback (department_id=NULL)
    return db.query(EmailTemplate).filter(
        EmailTemplate.type == template_type,
        EmailTemplate.department_id.is_(None),
    ).first()


def render_template(template: EmailTemplate, variables: dict) -> tuple[str, str]:
    """
    Ersetzt Platzhalter im Template.

    Platzhalter-Format: {{variable_name}}
    Bekannte Variablen: name, email, title, description, deadline, portal_url

    Gibt (subject, body_html) zurück.
    """
    subject = template.subject
    body = template.body_html

    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))

    return subject, body


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    from_email: Optional[str] = None,
) -> bool:
    """
    Sendet eine E-Mail über Amazon SES.

    Gibt True bei Erfolg zurück, False bei Fehler.
    """
    settings = get_settings()
    sender = from_email or settings.ses_from_email

    ses_client = boto3.client("ses", region_name=settings.aws_region_name)

    try:
        ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                    "Text": {
                        # Einfache Text-Version als Fallback
                        "Data": re.sub(r"<[^>]+>", "", body_html),
                        "Charset": "UTF-8",
                    },
                },
            },
        )
        logger.info(f"E-Mail gesendet an {to_email} (Betreff: {subject})")
        return True
    except ClientError as e:
        logger.error(f"SES-Fehler beim Senden an {to_email}: {e.response['Error']['Message']}")
        return False


def send_request_notification(
    db: Session,
    to_email: str,
    dozent_name: str,
    request_title: str,
    request_description: Optional[str],
    deadline: datetime,
    assignment_id: int,
    department_id: int,
) -> bool:
    """Sendet die initiale E-Mail bei einer neuen Anforderung."""
    settings = get_settings()
    template = get_template(db, "request", department_id)

    if not template:
        logger.warning(f"Kein 'request'-Template für Fachbereich {department_id} oder global gefunden.")
        return False

    upload_url = f"{settings.frontend_url}/upload/{assignment_id}"

    variables = {
        "name": dozent_name or to_email,
        "email": to_email,
        "title": request_title,
        "description": request_description or "",
        "deadline": deadline.strftime("%d.%m.%Y"),
        "portal_url": settings.frontend_url,
        "upload_url": upload_url,
    }

    subject, body_html = render_template(template, variables)
    return send_email(to_email, subject, body_html)


def send_reminder(
    db: Session,
    to_email: str,
    dozent_name: str,
    request_title: str,
    deadline: datetime,
    assignment_id: int,
    department_id: int,
    is_overdue: bool = False,
) -> bool:
    """Sendet eine Erinnerung oder Mahnung."""
    settings = get_settings()
    template_type = "overdue" if is_overdue else "reminder"
    template = get_template(db, template_type, department_id)

    if not template:
        logger.warning(f"Kein '{template_type}'-Template gefunden.")
        return False

    days_until = (deadline - datetime.utcnow()).days
    upload_url = f"{settings.frontend_url}/upload/{assignment_id}"

    variables = {
        "name": dozent_name or to_email,
        "email": to_email,
        "title": request_title,
        "deadline": deadline.strftime("%d.%m.%Y"),
        "days_until_deadline": str(max(0, days_until)),
        "portal_url": settings.frontend_url,
        "upload_url": upload_url,
    }

    subject, body_html = render_template(template, variables)
    return send_email(to_email, subject, body_html)
