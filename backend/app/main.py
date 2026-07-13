"""FastAPI entrypoint — composizione app + router + middleware + lifecycle."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine

# Import dei moduli models — necessario perche' SQLAlchemy scopra tutte le tabelle
# prima di chiamare Base.metadata.create_all().
from app.models import Cinema, Film, Showing  # noqa: F401
from app.routers import admin, cinema, film, showings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hook. In dev creiamo le tabelle al volo;
    in prod si usa Alembic con `alembic upgrade head`.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # (nessun teardown particolare per SQLite)


def create_app() -> FastAPI:
    """Application factory: costruisce e configura l'istanza FastAPI.

    Tenere la costruzione in una funzione (invece che a livello modulo) permette
    di creare app configurate diversamente nei test e rende esplicito l'ordine
    di composizione: middleware CORS → router → route di monitoring.
    """
    settings = get_settings()

    app = FastAPI(
        title="CinePosto API",
        version="1.0.0",
        description="API REST per la programmazione dei cinema umbri.",
        lifespan=lifespan,
    )

    # CORS: le origin sono in .env (JSON array); se assente, config.py mette i default dev (localhost).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # L'app non usa cookie/sessioni: nessuna credenziale cross-origin.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Router principali sotto /api/v1
    app.include_router(cinema.router, prefix="/api/v1")
    app.include_router(film.router, prefix="/api/v1")
    app.include_router(showings.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    # /health resta senza versione (usato da UptimeRobot / monitoring)
    @app.get("/health", tags=["health"])
    def health():
        """Liveness probe: risponde 200 se il processo è vivo. Non tocca il DB."""
        return {"status": "ok"}

    return app


app = create_app()

# Uso:
#   dev:   uvicorn app.main:app --reload --port 8000
#   prod:  uvicorn app.main:app --host 0.0.0.0 --port 8000  (dietro Caddy/Nginx)
