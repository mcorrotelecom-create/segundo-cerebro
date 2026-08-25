"""Motor de base de datos y utilidades de sesión (SQLAlchemy 2.x)."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión y la cierra siempre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea las tablas si no existen.

    Fase 0 usa create_all() por simplicidad. Cuando el esquema se estabilice
    (Fase 1, con boq_item/progress_account), se introduce Alembic para
    migraciones versionadas — hacerlo antes sería mantener migraciones de
    un esquema que todavía está cambiando de forma.
    """
    from app import models  # noqa: F401  (registra los modelos en Base.metadata)

    Base.metadata.create_all(bind=engine)
