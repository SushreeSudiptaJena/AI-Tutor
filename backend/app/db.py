"""Database engine and session.

Sync SQLAlchemy 2.0 only -- see the Async policy in CLAUDE.md. The engine is
created lazily so importing the app (for tests, or `--help`) does not require a
reachable database.
"""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from . import config

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.database_url(),
            pool_pre_ping=True,   # a hosted free-tier DB will drop idle connections
            pool_size=5,
            max_overflow=5,
        )
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_db() -> Iterator[Session]:
    """FastAPI dependency. Usage: `def route(db: Session = Depends(get_db))`."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> tuple[bool, str]:
    """Cheap liveness probe for /health. Never raises."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:  # noqa: BLE001 -- health must report, not crash
        return False, type(exc).__name__
