"""Fixture pytest condivise da tutti i test.

Strategie di test adottate:
- SQLite IN-MEMORY (:memory:) → ogni test parte da un DB pulito, veloce, non lascia file.
- Dependency override → l'app FastAPI usa la nostra session di test invece di quella prod.
- Fixture 'session' e 'client' → il test dichiara cosa gli serve, pytest glielo passa.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Cinema, Film, Showing  # noqa: F401 — assicura registrazione tabelle


@pytest.fixture
def engine():
    """Crea un engine SQLite in memoria + tutte le tabelle. Vive quanto un test.

    `poolclass=StaticPool` + `check_same_thread=False`: SQLite in-memory
    di default vive UNA connessione. StaticPool riusa la stessa connessione
    su tutti i thread → i dati scritti dalla fixture si vedono anche nel client.
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def session(engine) -> Session:
    """Session isolata per il singolo test. Rollback automatico a fine test."""
    TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(engine):
    """TestClient di FastAPI con dependency override su get_db.

    L'endpoint pensa di parlare col DB prod; in realta' parla col DB in-memory.
    Cosi' testiamo la vera catena router → service → repo → DB, ma su dati controllati.
    """
    TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    # Ripristina lo stato dopo il test (evita leak fra test successivi)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_cinema(session) -> Cinema:
    """Un cinema di test, gia' salvato in DB."""
    c = Cinema(
        slug="test-cinema",
        name="Test Cinema",
        city="Perugia",
        address="Via Test 1",
        region="Umbria",
        lat=43.11,
        lon=12.39,
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@pytest.fixture
def sample_film(session) -> Film:
    """Un film di test, gia' salvato in DB."""
    f = Film(
        title="Test Film",
        title_normalized="test film",
        year=2026,
        runtime_minutes=90,
        genres="Drama",
        director="Regista Test",
        poster_url="https://example.com/poster.jpg",
        synopsis="Trama del film di test.",
    )
    session.add(f)
    session.commit()
    session.refresh(f)
    return f
