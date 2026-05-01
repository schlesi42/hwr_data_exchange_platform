"""
Datenbankverbindung mit SQLAlchemy.

Wir nutzen NullPool für Lambda-Kompatibilität:
Lambda-Instanzen teilen sich keine Verbindungen, deshalb brauchen
wir keinen Connection Pool – jede Invocation verbindet sich neu.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings


class Base(DeclarativeBase):
    """Basis-Klasse für alle SQLAlchemy-Modelle."""
    pass


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.get_db_url(),
        # NullPool: keine Verbindungen cachen (Lambda-kompatibel)
        poolclass=NullPool,
        # SSL für Verbindungen zu RDS erforderlich
        connect_args={"sslmode": "require"},
    )


def get_session_factory():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI Dependency Injection: Datenbankverbindung pro Request.

    Verwendung in Routers:
        @router.get("/...")
        def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
