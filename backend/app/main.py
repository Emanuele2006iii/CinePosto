"""FastAPI entrypoint — composizione app + router + middleware + lifecycle."""
# Decisione D2: niente scheduler dentro al backend (lo scraper gira via systemd timer su VM).
#
# TODO struttura attesa:
#   from contextlib import asynccontextmanager
#   from fastapi import FastAPI
#   from fastapi.middleware.cors import CORSMiddleware
#   from .config import get_settings
#   from .database import Base, engine
#   from .routers import cinema, film, showings, admin
#
#   @asynccontextmanager
#   async def lifespan(app: FastAPI):
#       Base.metadata.create_all(bind=engine)  # solo dev; in prod usare Alembic
#       yield
#
#   def create_app() -> FastAPI:
#       settings = get_settings()
#       app = FastAPI(
#           title="CinePosto API",
#           version="1.0.0",
#           lifespan=lifespan,
#       )
#       app.add_middleware(
#           CORSMiddleware,
#           allow_origins=settings.cors_origins,
#           allow_methods=["*"],
#           allow_headers=["*"],
#       )
#       app.include_router(cinema.router,   prefix="/api/v1", tags=["cinemas"])
#       app.include_router(film.router,     prefix="/api/v1", tags=["films"])
#       app.include_router(showings.router, prefix="/api/v1", tags=["showings"])
#       app.include_router(admin.router,    prefix="/api/v1/admin", tags=["admin"])
#
#       @app.get("/health")
#       def health(): return {"status": "ok"}
#       return app
#
#   app = create_app()
#
# Run dev:   uvicorn app.main:app --reload --port 8000
# Run prod:  uvicorn app.main:app --host 0.0.0.0 --port 8000 (dietro nginx)
