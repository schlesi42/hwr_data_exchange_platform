"""
Konfiguration der Anwendung.

Pydantic Settings liest Werte aus Umgebungsvariablen.
Im Lambda werden diese vom CDK-Stack gesetzt.
Lokal kannst du eine .env-Datei im backend/-Verzeichnis anlegen.
"""
import json
import boto3
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # AWS-Region
    aws_region_name: str = "eu-central-1"

    # Datenbank
    # In Lambda: wird aus Secrets Manager geladen (siehe get_db_url())
    db_secret_arn: str = ""
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "hwrportal"
    # Für lokale Entwicklung: direkt setzen
    db_user: str = ""
    db_password: str = ""

    # S3
    s3_uploads_bucket: str = ""

    # Cognito
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""

    # Frontend (für Links in E-Mails)
    frontend_url: str = "http://localhost:5173"
    domain: str = "localhost"

    # Absender-E-Mail für SES
    ses_from_email: str = "noreply@hwr-fb2-dozierenden-portal.de"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def get_db_url(self) -> str:
        """
        Gibt den PostgreSQL-Connection-String zurück (nur ein Text, keine Verbindung!).
        Format: "postgresql://user:password@host:port/dbname"

        Die eigentliche Verbindung wird erst in database.py durch create_engine() geöffnet.

        In Lambda (Produktion): Credentials werden aus AWS Secrets Manager geladen.
          db_secret_arn ist als Umgebungsvariable gesetzt → _get_secret() fragt AWS ab.
          db_user / db_password werden dabei NICHT benutzt.

        Lokal (Entwicklung): db_secret_arn ist leer → Credentials kommen aus .env-Datei.
          db_user und db_password in .env setzen (nie committen – steht in .gitignore).
        """
        if self.db_secret_arn:
            # Produktionsmodus: Credentials aus Secrets Manager
            secret = _get_secret(self.db_secret_arn, self.aws_region_name)
            user = secret["username"]
            password = secret["password"]
        else:
            # Entwicklungsmodus: aus Umgebungsvariablen
            user = self.db_user
            password = self.db_password

        return (
            f"postgresql://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


def _get_secret(secret_arn: str, region: str) -> dict:
    """Liest ein Secret aus AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])


@lru_cache()
def get_settings() -> Settings:
    """
    Gibt eine gecachte Settings-Instanz zurück.
    lru_cache stellt sicher, dass Settings nur einmal erstellt werden
    (wichtig für Lambda, da Secrets Manager-Aufrufe Zeit kosten).
    """
    return Settings()
