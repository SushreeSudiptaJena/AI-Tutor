"""admin-011 -- give a user the read-marker the notification bell needs.

    .venv/Scripts/python.exe backend/scripts/migrate_admin_notifications.py [--dry-run]

**Why this file exists.** No Alembic, by decision (CLAUDE.md), and
`create_all()` only creates tables that are *missing* -- it will not add a
column to a table that already exists. `users` is already in the shared
database with everybody's account in it, so the change has to be spelled out.

The statement is idempotent: running it twice is safe, and running it against a
database `create_all()` built fresh is a no-op.

Nothing is dropped and no row is rewritten. Every existing user simply gains a
NULL `notifications_seen_at`, which is exactly what "has never opened the bell"
means -- so the first `GET /admin/notifications` after this migration correctly
reports everything as unread rather than silently reporting nothing.

There is deliberately no second column here. The other half of admin-011 --
"has this teacher ever logged in" -- is a row in `audit_log`, not a column: see
`app/routers/auth.py:_note_first_login`.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "backend")

from sqlalchemy import inspect, text  # noqa: E402

from app.db import get_engine  # noqa: E402

DRY = "--dry-run" in sys.argv

COLUMNS = ("notifications_seen_at",)

STATEMENTS = [
    ("add notifications_seen_at",
     "ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_seen_at TIMESTAMPTZ"),
]


def describe(engine) -> None:
    cols = {c["name"]: c for c in inspect(engine).get_columns("users")}
    for name in COLUMNS:
        c = cols.get(name)
        if c is None:
            print(f"    {name:<24} MISSING")
        else:
            print(f"    {name:<24} {str(c['type']):<26} "
                  f"{'NULL ok' if c['nullable'] else 'NOT NULL'}")


def main() -> int:
    engine = get_engine()

    print("before:")
    describe(engine)

    print("\nwould run:" if DRY else "\nrunning:")
    for label, sql in STATEMENTS:
        print(f"    {label}")
        if not DRY:
            with engine.begin() as conn:
                conn.execute(text(sql))

    if DRY:
        print("\nNothing was changed. Drop --dry-run to apply.")
        return 0

    print("\nafter:")
    describe(engine)

    cols = {c["name"]: c for c in inspect(engine).get_columns("users")}
    missing = [c for c in COLUMNS if c not in cols]
    not_null = [c for c in COLUMNS if c in cols and not cols[c]["nullable"]]
    if missing or not_null:
        print(f"\nMIGRATION DID NOT TAKE -- missing={missing} not_null={not_null}")
        return 1
    print("\nmigration OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
