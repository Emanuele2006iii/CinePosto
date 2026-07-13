"""Configurazione SQLAlchemy: engine + SessionLocal + Base + get_db()."""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Base dichiarativa condivisa da tutti i modelli in app/models/."""
    pass


_settings = get_settings()

# `check_same_thread=False` serve solo per SQLite: FastAPI puo' servire
# request su thread diversi e SQLite di default blocca questo uso.
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    _settings.database_url,
    echo=(_settings.env == "development"),  # in dev stampa le query SQL
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Attiva le foreign key su ogni nuova connessione SQLite.

    SQLite di default NON applica i vincoli FK: senza questo PRAGMA si
    potrebbero inserire showings orfani. Il listener è registrato sulla classe
    Engine (vale per tutti gli engine, incluso quello dei test in-memory),
    quindi verifica che la connessione sia davvero SQLite prima di agire.
    """
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    """FastAPI dependency: apre una session per request, la chiude a fine response."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
