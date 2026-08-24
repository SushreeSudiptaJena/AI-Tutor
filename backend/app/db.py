"""Database engine and session.

Sync SQLAlchemy 2.0 only -- see the Async policy in CLAUDE.md. The engine is
created lazily so importing the app (for tests, or `--help`) does not require a
reachable database.
"""

import os
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from . import config

# Opening a connection to Neon costs ~3.5s (TLS + SCRAM with channel binding,
# to another region). Running a query on an already-open one costs ~0.12s.
# Every number in this module follows from that 30x gap: a request must never
# be the thing that opens a connection.
POOL_SIZE = 20

# Warming pays for itself across a demo session and is dead weight in a test
# run, where it doubled the suite. Off under pytest, and `DB_WARM_POOL=0`
# switches it off anywhere else.
WARM_ON_CREATE = os.getenv("DB_WARM_POOL", "1") != "0" and "pytest" not in sys.modules

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.database_url(),
            pool_pre_ping=True,   # a hosted free-tier DB will drop idle connections
            # A request holds its session for its whole lifetime -- including
            # across a provider call, because get_db() is request-scoped. At
            # 5+5 connections, three students clicking "practise this" while a
            # teacher tab polled the heatmap exhausted the pool, and everyone
            # else blocked on the default 30s pool_timeout BEFORE their request
            # started. That is where a one-minute click came from.
            pool_size=POOL_SIZE,
            # Deliberately small. An overflow connection is CLOSED when it is
            # returned, so every burst that reaches into overflow pays the 3.5s
            # open cost again, and again. Overflow is an emergency valve here,
            # not capacity -- capacity is pool_size, which is kept warm below.
            max_overflow=5,
            # Fail fast instead of hanging. If 25 connections are genuinely
            # busy, a quick error is better demo behaviour than a 30s stall.
            pool_timeout=10,
            pool_recycle=1800,
        )
        if WARM_ON_CREATE:
            warm_pool(_engine)
    return _engine


def warm_pool(engine: Engine, size: int = POOL_SIZE) -> int:
    """Open `size` connections at once and hand them straight back to the pool.

    Sequentially this takes ~71s for 20 connections; in parallel it takes ~6s,
    because the cost is round-trip latency rather than work on the server. Done
    once at first use, it means no student's click ever pays for a handshake.

    Threads, not async -- see the Async policy in CLAUDE.md. This is a one-shot
    startup routine, not a concurrency model, and it is gone by the time the
    first request is served.

    Never raises: a warm-up that fails must not stop the app from starting. The
    connections simply get opened on demand, exactly as they did before.
    """
    def _open():
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True

    try:
        with ThreadPoolExecutor(max_workers=size) as pool:
            results = list(pool.map(lambda _: _open(), range(size)))
        return sum(1 for r in results if r)
    except Exception:  # noqa: BLE001 -- warming is an optimisation, never a gate
        return 0


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
