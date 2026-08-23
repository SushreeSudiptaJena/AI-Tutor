"""Drop and recreate every table.

    .venv/Scripts/python.exe backend/scripts/reset_db.py

DESTRUCTIVE, and the database is SHARED. Everyone loses their data, not just
you. Announce it in the team channel before running it.

Pass --force to skip the confirmation prompt (for scripts and CI).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.db import get_engine
from app.models import Base


def main() -> None:
    force = "--force" in sys.argv
    engine = get_engine()

    # Never print the password back at the user.
    url = engine.url.render_as_string(hide_password=True)
    print(f"target: {url}")

    if not force:
        print("\nThis DROPS EVERY TABLE in the shared database.")
        print("Everyone on the team loses their data. Announce it first.")
        reply = input("Type 'reset' to continue: ").strip()
        if reply != "reset":
            sys.exit("aborted")

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        tables = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
        ).scalars().all()

    print(f"\nschema recreated - {len(tables)} tables:")
    for t in tables:
        print(f"  {t}")
    print("\nNext: backend/scripts/seed.py")


if __name__ == "__main__":
    main()
