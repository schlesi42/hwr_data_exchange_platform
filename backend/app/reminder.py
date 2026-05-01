"""
Reminder Lambda Handler – täglich durch EventBridge ausgelöst.

Ablauf:
  1. Alle offenen Zuweisungen aus der DB laden
  2. Prüfen: Deadline in X Tagen? → Erinnerung senden (je nach Fachbereich-Config)
  3. Prüfen: Deadline überschritten? → Mahnung senden
  4. Status der Anforderungen aktualisieren

Dieser Handler wird durch den Reminder-Lambda aufgerufen.
Er nutzt dasselbe Docker-Image wie der Haupt-Backend-Lambda,
aber mit einem anderen Einstiegspunkt (CMD in Dockerfile).
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database import get_session_factory
from app.models.document_request import (
    DocumentRequest, RequestAssignment, AssignmentStatus, RequestStatus
)
from app.models.department import ReminderConfig
from app.models.user import User
from app.services.email import send_reminder

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def process_reminders(db: Session) -> dict:
    """
    Hauptlogik: Alle Deadlines prüfen und Erinnerungen senden.
    Gibt eine Zusammenfassung der gesendeten E-Mails zurück.
    """
    now = datetime.utcnow()
    stats = {"reminders_sent": 0, "overdue_sent": 0, "errors": 0}

    # Alle offenen Zuweisungen (pending) laden
    assignments = db.query(RequestAssignment).filter(
        RequestAssignment.status == AssignmentStatus.pending
    ).all()

    for assignment in assignments:
        request: DocumentRequest = assignment.request
        dozent: User = assignment.dozent

        # Reminder-Config des Fachbereichs laden
        config = db.query(ReminderConfig).filter(
            ReminderConfig.department_id == request.department_id
        ).first()

        if not config:
            continue

        days_until_deadline = (request.deadline - now).days

        # Case 1: Deadline noch nicht überschritten → Erinnerung prüfen
        if days_until_deadline >= 0:
            # Soll heute eine Erinnerung gesendet werden?
            if days_until_deadline in config.days_before_list:
                # Throttle: nicht zweimal am selben Tag senden
                if assignment.last_reminder_sent_at:
                    last_sent_date = assignment.last_reminder_sent_at.date()
                    if last_sent_date == now.date():
                        continue  # Heute schon gesendet

                success = send_reminder(
                    db=db,
                    to_email=dozent.email,
                    dozent_name=dozent.name or dozent.email,
                    request_title=request.title,
                    deadline=request.deadline,
                    assignment_id=assignment.id,
                    department_id=request.department_id,
                    is_overdue=False,
                )
                if success:
                    assignment.last_reminder_sent_at = now
                    assignment.reminder_count += 1
                    stats["reminders_sent"] += 1
                else:
                    stats["errors"] += 1

        # Case 2: Deadline überschritten
        elif config.send_overdue:
            days_overdue = abs(days_until_deadline)

            # Mahnung nur alle N Tage senden (laut Konfiguration)
            should_send = False
            if assignment.last_reminder_sent_at is None:
                should_send = True
            else:
                days_since_last = (now - assignment.last_reminder_sent_at).days
                if days_since_last >= config.overdue_interval_days:
                    should_send = True

            if should_send:
                success = send_reminder(
                    db=db,
                    to_email=dozent.email,
                    dozent_name=dozent.name or dozent.email,
                    request_title=request.title,
                    deadline=request.deadline,
                    assignment_id=assignment.id,
                    department_id=request.department_id,
                    is_overdue=True,
                )
                if success:
                    assignment.status = AssignmentStatus.overdue
                    assignment.last_reminder_sent_at = now
                    assignment.reminder_count += 1
                    stats["overdue_sent"] += 1
                else:
                    stats["errors"] += 1

    # Gesamt-Status aller offenen Anforderungen aktualisieren
    open_requests = db.query(DocumentRequest).filter(
        DocumentRequest.status.in_([RequestStatus.open, RequestStatus.partial])
    ).all()

    for req in open_requests:
        req.update_status()

    db.commit()
    return stats


def handler(event: dict, context) -> dict:
    """Lambda-Einstiegspunkt für den Reminder-Job."""
    logger.info("Reminder-Job gestartet.")

    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        stats = process_reminders(db)
        logger.info(f"Reminder-Job abgeschlossen: {stats}")
        return {
            "statusCode": 200,
            "body": str(stats),
        }
    except Exception as e:
        logger.error(f"Fehler im Reminder-Job: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": str(e),
        }
    finally:
        db.close()
