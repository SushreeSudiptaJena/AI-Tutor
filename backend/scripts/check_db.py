"""Verification tool for infra-001: shared Postgres + pgvector reachable by the team.

Run --write on one machine, then --read on another. If the second machine sees the
first machine's row, the shared database is real and infra-001 passes.

    python backend/scripts/check_db.py --write
    python backend/scripts/check_db.py --read

With no flag it does both locally, which only proves the connection works -- it does
NOT satisfy infra-001. The two-machine check is the point.
"""

import argparse
import os
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_database_url() -> str:
    load_dotenv(REPO_ROOT / ".env")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        sys.exit(
            "DATABASE_URL is not set.\n"
            "Copy .env.example to .env and paste the connection string from the team channel."
        )
    # Neon hands out postgresql://... ; we drive it with psycopg 3.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def machine_label() -> str:
    return f"{socket.gethostname()} ({platform.system()})"


def main() -> None:
    parser = argparse.ArgumentParser(description="infra-001 shared database check")
    parser.add_argument("--write", action="store_true", help="insert a row stamped with this machine")
    parser.add_argument("--read", action="store_true", help="list rows written by any machine")
    args = parser.parse_args()
    do_write = args.write or not (args.write or args.read)
    do_read = args.read or not (args.write or args.read)

    engine = create_engine(load_database_url(), pool_pre_ping=True)

    with engine.begin() as conn:
        version = conn.execute(text("SELECT version()")).scalar_one()
        print(f"connected      : {version.split(',')[0]}")
        print(f"this machine   : {machine_label()}")

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        ext = conn.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one_or_none()
        if not ext:
            sys.exit("pgvector extension is NOT installed and could not be created.")
        print(f"pgvector       : {ext}")

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS _infra_check (
                    id          serial PRIMARY KEY,
                    machine     text        NOT NULL,
                    noted_at    timestamptz NOT NULL,
                    probe       vector(3)   NOT NULL
                )
                """
            )
        )

        if do_write:
            conn.execute(
                text(
                    "INSERT INTO _infra_check (machine, noted_at, probe)"
                    " VALUES (:m, :t, '[1,2,3]')"
                ),
                {"m": machine_label(), "t": datetime.now(timezone.utc)},
            )
            print("wrote          : 1 row")

        if do_read:
            rows = conn.execute(
                text(
                    "SELECT machine, noted_at, probe <-> '[1,2,3]' AS dist"
                    " FROM _infra_check ORDER BY noted_at DESC LIMIT 10"
                )
            ).all()
            print(f"rows visible   : {len(rows)}")
            for machine, noted_at, dist in rows:
                print(f"  - {noted_at.isoformat(timespec='seconds')}  {machine}  (vector op ok, dist={dist})")
            distinct = {r[0] for r in rows}
            if len(distinct) >= 2:
                print("\nPASS: rows from more than one machine are visible. infra-001 is satisfied.")
            else:
                print(
                    "\nINCOMPLETE: only one machine has written so far."
                    " Run --write on a second machine, then --read here again."
                )


if __name__ == "__main__":
    main()
