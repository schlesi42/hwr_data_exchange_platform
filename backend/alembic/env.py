"""
Alembic Konfiguration für Datenbankmigrationen.

Nutzung:
  cd backend/
  alembic revision --autogenerate -m "beschreibung"  # neue Migration erstellen
  alembic upgrade head                                # Migration anwenden
  alembic downgrade -1                               # eine Migration zurück
"""
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Alle Modelle importieren, damit Alembic sie kennt
from app.models import *  # noqa
from app.database import Base
from app.config import get_settings

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


def get_url() -> str:
    """Datenbankverbindung aus Umgebungsvariablen."""
    settings = get_settings()
    return settings.get_db_url()


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
