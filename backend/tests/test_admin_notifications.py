"""admin-011 tests -- the admin notification bell. No network, no database.

The guarantees here are about a badge that means something. A notification
feed that invents its own store, counts your own actions as news, or reports a
number scoped to the page you asked for is worse than no bell at all: it is a
bell that rings for nothing, which people learn to ignore.
"""

from __future__ import annotations

import inspect

from app.routers import admin, auth


def _src(fn) -> str:
    return inspect.getsource(fn)


class _Row:
    """Minimal stand-in for an AuditLog row -- matches test_admin.py's."""

    def __init__(self, action, target, detail=None, actor_id=1):
        self.action, self.target, self.detail = action, target, detail or {}
        self.id, self.actor_id, self.at = 1, actor_id, None


# ---------------------------------------------------------------------------
# One store, not two
# ---------------------------------------------------------------------------

def test_notifications_read_the_audit_log_and_do_not_invent_a_second_store():
    """A separate notifications table would be a copy that can disagree with
    the original -- and the original is the one an admin trusts."""
    from app import models

    assert not any(t.name in ("notifications", "admin_notifications")
                   for t in models.Base.metadata.sorted_tables)
    assert "AuditLog" in _src(admin.notifications)


def test_the_bell_is_admin_only():
    for fn in (admin.notifications, admin.notifications_read):
        source = _src(fn)
        assert "admin_only" in source
        assert "teacher_only" not in source


def test_seed_runs_never_ring_and_there_is_no_escape_hatch():
    """A notification about a developer script is not a notification. The
    audit log stays the place to see everything."""
    source = _src(admin._notifications_base) + _src(admin.notifications)
    assert "notin_(SYSTEM_ACTIONS)" in source
    assert "include_system" not in inspect.signature(admin.notifications).parameters


# ---------------------------------------------------------------------------
# The count has to mean something
# ---------------------------------------------------------------------------

def test_unread_is_counted_over_the_table_not_over_the_page():
    """A bell that says '3' because you asked for 3 rows is lying."""
    source = _src(admin.notifications)
    unread = source[source.index("unread_stmt ="):source.index("rows = db.scalars")]
    assert "func.count()" in unread
    assert "limit" not in unread and "offset" not in unread


def test_your_own_actions_are_listed_but_do_not_ring():
    """Counting your own uploads leaves the badge permanently lit."""
    source = _src(admin.notifications)
    assert "is_distinct_from(user.id)" in source, "own rows must be excluded"
    # ...but still listed. The page query filters on nothing but the system
    # actions: history is history.
    page = source[source.index("rows = db.scalars"):source.index("actors = {")]
    assert "actor_id" not in page


def test_a_null_actor_still_counts_as_unread():
    """`actor_id != 3` is NULL -- therefore false -- for a row with no actor,
    which would silently drop exactly the rows nobody is accountable for."""
    assert "!= user.id" not in _src(admin.notifications)
    assert "is_distinct_from" in _src(admin.notifications)


def test_the_seen_marker_comes_from_the_database_clock():
    """Every audit `at` is a server_default=func.now() stamp. A marker from a
    laptop running fast marks rows read that were not written yet."""
    source = _src(admin.notifications_read)
    assert "select(func.now())" in source
    assert "datetime.now" not in source and "utcnow" not in source


def test_the_read_marker_is_nullable_and_says_never_opened():
    """It was added to a table that already had every account in it."""
    from app.models import User

    col = User.__table__.columns["notifications_seen_at"]
    assert col.nullable
    assert "seen_at is None" in _src(admin.notifications), \
        "a null marker must mean everything is unread, not everything is read"


def test_the_read_marker_never_leaves_through_auth_me():
    """UserOut is an allow-list on purpose. When the bell was marked read is
    nobody's business but the bell's."""
    from app.schemas import UserOut

    assert "notifications_seen_at" not in UserOut.model_fields


# ---------------------------------------------------------------------------
# teacher.first_login -- the other source
# ---------------------------------------------------------------------------

def test_the_first_login_verb_is_spelled_in_exactly_one_place():
    """auth.py writes the row and admin.py reads it. Two literals in two files
    is how an ?action= filter silently stops matching."""
    assert admin.FIRST_LOGIN_ACTION is auth.FIRST_LOGIN_ACTION
    assert auth.FIRST_LOGIN_ACTION == "teacher.first_login"


def test_only_teachers_are_recorded_and_only_once():
    """Not a login log. Only a teacher account is born from an admin
    generating a password and handing it over."""
    source = _src(auth._note_first_login)
    assert 'user.role != "teacher"' in source
    assert "already is not None" in source and "return" in source


def test_there_is_no_last_login_column_anywhere():
    """models.py forbids a last-seen column and means it. The existence of the
    audit row IS the record, which is also why it can only fire once."""
    from app.models import User

    names = set(User.__table__.columns.keys())
    for forbidden in ("last_login", "last_login_at", "last_seen",
                      "last_seen_at", "first_login_at", "login_count"):
        assert forbidden not in names, forbidden


def test_a_failed_notification_never_costs_a_teacher_their_login():
    """Without the savepoint a failed INSERT poisons the session and takes the
    token that was just issued with it -- locking a teacher out over a bell."""
    source = _src(auth._note_first_login)
    assert "begin_nested" in source
    assert "except Exception" in source

    login = _src(auth.login)
    assert login.index("_issue_token") < login.index("_note_first_login"), \
        "the token must exist before anything optional runs"


def test_the_assigned_subjects_are_captured_into_the_row():
    """An unassign afterwards must not rewrite history the admin already
    read."""
    source = _src(auth._note_first_login)
    assert "CourseTeacher" in source and '"courses": codes' in source


def test_the_first_login_summary_is_a_sentence_not_a_transitive_verb():
    """The generic path produces 'priya@x.edu signed in for the first time
    "Priya Sharma" (since removed)', which reads as a bug."""
    row = _Row("teacher.first_login", "user:12",
               {"email": "priya@example.edu", "name": "Priya Sharma",
                "courses": ["CSW2"]})
    summary = admin._audit_summary(row, "priya@example.edu", {})
    assert summary == "Priya Sharma signed in for the first time (assigned to CSW2)"
    assert "since removed" not in summary
    assert "user:12" not in summary


def test_a_first_login_with_no_assigned_subject_still_reads_as_a_sentence():
    row = _Row("teacher.first_login", "user:12", {"name": "Priya Sharma"})
    assert admin._audit_summary(row, "priya@example.edu", {}) == \
        "Priya Sharma signed in for the first time"


def test_a_first_login_row_is_labelled_so_the_ui_need_not_match_strings():
    source = _src(admin.notifications)
    assert '"teacher_first_login"' in source
    assert "FIRST_LOGIN_ACTION" in source


# ---------------------------------------------------------------------------
# The client renders this with the formatter it already has
# ---------------------------------------------------------------------------

def test_a_notification_carries_the_audit_row_unchanged():
    """Every field but kind/unread/by_you is the audit row, summary included --
    no second formatter, and no chance of the two drifting."""
    source = _src(admin.notifications)
    body = source[source.index("return {"):]
    for field in ('"id": r.id', '"action": r.action', '"target": r.target',
                  '"detail": r.detail', '"actor_email"', '"summary"',
                  '"at":'):
        assert field in body, field
    assert "_audit_summary(" in body


def test_titles_are_resolved_in_batches_here_too():
    """perf-001: a per-row lookup is a network round trip."""
    source = _src(admin.notifications)
    assert "_audit_titles(db, rows)" in source
    assert "db.get(" not in source


def test_the_page_size_is_capped():
    assert admin.MAX_NOTIFICATIONS <= 100
    assert "min(limit, MAX_NOTIFICATIONS)" in _src(admin.notifications)
