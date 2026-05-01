"""
FastAPI Anwendung – Einstiegspunkt.

Die Variable `handler` am Ende ist der Lambda-Einstiegspunkt:
AWS Lambda ruft handler(event, context) auf, Mangum übersetzt
das in einen ASGI-Request für FastAPI.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.config import get_settings
from app.database import Base, get_engine
from app.routers import departments, users, requests, files, templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Wird beim Start der Anwendung ausgeführt.
    Erstellt alle Datenbanktabellen, falls sie noch nicht existieren.
    (Für Migrationen: später Alembic nutzen)
    """
    logger.info("Anwendung startet – Datenbanktabellen prüfen...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Datenbank bereit.")
    yield
    logger.info("Anwendung wird beendet.")


settings = get_settings()

app = FastAPI(
    title="HWR Dozierenden-Portal API",
    description="API für den Datenaustausch zwischen Fachbereichsbüros und Dozierenden.",
    version="1.0.0",
    lifespan=lifespan,
    # Swagger UI nur im Dev-Modus zugänglich
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS: Nur Anfragen vom Frontend zulassen
# Im lokalen Dev auch localhost:5173 (Vite Dev Server)
allowed_origins = [settings.frontend_url]
if "localhost" in settings.frontend_url or "127.0.0.1" in settings.frontend_url:
    allowed_origins += ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers einbinden ──────────────────────────────────────────────────────
app.include_router(
    departments.router,
    prefix="/api/v1/departments",
    tags=["Fachbereiche"],
)
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Nutzer"],
)
app.include_router(
    requests.router,
    prefix="/api/v1/requests",
    tags=["Anforderungen"],
)
app.include_router(
    files.router,
    prefix="/api/v1/files",
    tags=["Dateien"],
)
app.include_router(
    templates.router,
    prefix="/api/v1/templates",
    tags=["E-Mail Templates"],
)


@app.get("/api/health")
def health_check():
    """Einfacher Health-Check-Endpunkt. Wird von AWS genutzt."""
    return {"status": "ok", "version": "1.0.0"}


# ── Lambda-Handler ─────────────────────────────────────────────────────────
# Mangum konvertiert Lambda-Events → ASGI-Requests für FastAPI
handler = Mangum(app, lifespan="off")
