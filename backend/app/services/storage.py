"""
S3-Dateioperationen.

Wichtig: Dateien werden NICHT über Lambda hoch-/heruntergeladen.
Stattdessen werden Pre-signed URLs genutzt:

  Upload-Flow:
    1. Frontend fragt Backend: "Gib mir eine Upload-URL für diese Datei"
    2. Backend erstellt eine temporäre S3-URL (15 Minuten gültig)
    3. Frontend lädt direkt zu S3 hoch (kein Umweg über Lambda/API Gateway)
    4. Frontend meldet Backend: "Upload abgeschlossen"

  Download-Flow:
    1. Frontend fragt Backend: "Gib mir Download-URL für Datei X"
    2. Backend prüft Berechtigung
    3. Backend erstellt temporäre Download-URL (1 Stunde gültig)
    4. Frontend öffnet/zeigt die URL

Vorteil: Lambda hat kein 6 MB Payload-Limit für Dateien.
"""
import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


def generate_upload_url(
    filename: str,
    content_type: str,
    assignment_id: int,
    request_id: int,
    expiry_seconds: int = 900,  # 15 Minuten
) -> tuple[str, str]:
    """
    Erstellt eine Pre-signed Upload-URL.

    Gibt (s3_key, upload_url) zurück.
    s3_key ist der Pfad in S3, den wir in der DB speichern.
    upload_url ist die temporäre URL, die das Frontend nutzt.
    """
    settings = get_settings()

    # Strukturierter S3-Schlüssel für einfaches Auffinden
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    # Dateiname bereinigen (keine Sonderzeichen im S3-Key)
    safe_filename = "".join(c if c.isalnum() or c in ".-_" else "_" for c in filename)
    s3_key = f"uploads/request-{request_id}/assignment-{assignment_id}/{timestamp}_{safe_filename}"

    s3_client = boto3.client("s3", region_name=settings.aws_region_name)

    try:
        # PUT: Direkt in S3 schreiben
        upload_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_uploads_bucket,
                "Key": s3_key,
                "ContentType": content_type,
                # Maximale Dateigröße: 100 MB
                "ContentLength": 100 * 1024 * 1024,
            },
            ExpiresIn=expiry_seconds,
        )
        return s3_key, upload_url
    except ClientError as e:
        logger.error(f"Fehler beim Erstellen der Upload-URL: {e}")
        raise


def generate_download_url(
    s3_key: str,
    filename: str,
    expiry_seconds: int = 3600,  # 1 Stunde
) -> str:
    """
    Erstellt eine Pre-signed Download-URL.

    Content-Disposition-Header sorgt dafür, dass der Browser
    den Dateinamen korrekt setzt.
    """
    settings = get_settings()
    s3_client = boto3.client("s3", region_name=settings.aws_region_name)

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_uploads_bucket,
                "Key": s3_key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=expiry_seconds,
        )
        return url
    except ClientError as e:
        logger.error(f"Fehler beim Erstellen der Download-URL für {s3_key}: {e}")
        raise


def delete_file(s3_key: str) -> bool:
    """Löscht eine Datei aus S3."""
    settings = get_settings()
    s3_client = boto3.client("s3", region_name=settings.aws_region_name)

    try:
        s3_client.delete_object(
            Bucket=settings.s3_uploads_bucket,
            Key=s3_key,
        )
        logger.info(f"Datei gelöscht: {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Fehler beim Löschen von {s3_key}: {e}")
        return False
