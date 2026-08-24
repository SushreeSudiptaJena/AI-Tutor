"""admin-001 / admin-002 / admin-003 tests. No network, no database.

The guarantees here are about provenance and about not losing things: material
is archived rather than deleted, a bad prerequisite fails loudly rather than
being dropped, and every mutation leaves an audit row somebody can read.
"""

from __future__ import annotations

import inspect

import pytest

from app.routers import admin
from app.schemas import CourseIn, DepartmentIn


def _src(fn) -> str:
    return inspect.getsource(fn)


# ---------------------------------------------------------------------------
# Who is allowed in
# ---------------------------------------------------------------------------

def test_every_admin_route_requires_an_admin_not_a_teacher():
    """`teacher_only` admits teachers. Uploading course material and rewriting
    the prerequisite graph are institutional acts, not teaching ones."""
    routes = [r for r in admin.router.routes if hasattr(r, "endpoint")]
    assert routes, "no admin routes registered"
    for route in routes:
        source = _src(route.endpoint)
        assert "admin_only" in source, f"{route.path} does not require an admin"
        assert "teacher_only" not in source


# ---------------------------------------------------------------------------
# admin-002 -- structure
# ---------------------------------------------------------------------------

def test_a_missing_prerequisite_is_an_error_not_a_silent_drop():
    """Dropping it produces a course whose gap attribution is quietly wrong,
    and nothing downstream can tell 'no prerequisite' from 'one we lost'."""
    source = _src(admin.create_course)
    assert "to use as a prerequisite" in source
    assert "HTTP_400_BAD_REQUEST" in source


def test_a_course_cannot_be_its_own_prerequisite():
    assert "its own prerequisite" in _src(admin.create_course)


def test_duplicate_course_codes_conflict():
    assert "HTTP_409_CONFLICT" in _src(admin.create_course)


def test_course_output_carries_the_prerequisite_courses():
    """This is the field gap detection reads to name the prior course."""
    assert "prerequisite_courses" in _src(admin._course_out)


def test_course_code_is_normalised_and_required():
    assert CourseIn(code=" csw2 ", title="x").code == "CSW2"
    with pytest.raises(ValueError):
        CourseIn(code="  ", title="x")
    with pytest.raises(ValueError):
        DepartmentIn(name="   ")


# ---------------------------------------------------------------------------
# admin-001 -- upload and versioning
# ---------------------------------------------------------------------------

def test_uploading_a_replacement_archives_rather_than_deletes():
    """Chunks cite a material by page. Deleting it leaves a student looking at
    a citation to a book that no longer exists."""
    source = _src(admin.upload_material)
    assert 'old.status = "archived"' in source
    assert "delete(" not in source


def test_a_new_version_is_numbered_from_the_previous_one():
    assert "previous[0].version + 1" in _src(admin.upload_material)


def test_the_upload_filename_is_derived_not_taken_from_the_client():
    """`../../.env` is a filename. The stored name comes from the title."""
    assert "_safe_name(title)" in _src(admin.upload_material)
    assert admin._safe_name("../../.env") == "env"
    assert admin._safe_name("Django 5 By Example!") == "Django-5-By-Example"
    assert "/" not in admin._safe_name("a/b/c")
    assert "\\" not in admin._safe_name("a\\b\\c")
    assert admin._safe_name("") == "material"


def test_only_the_documented_material_kinds_are_accepted():
    assert admin.MATERIAL_KINDS == ("syllabus", "textbook", "notes", "assignment")
    assert "kind not in MATERIAL_KINDS" in _src(admin.upload_material)


def test_upload_does_not_embed_inline():
    """Embedding a textbook is minutes of CPU, and an HTTP request that takes
    minutes is a request that times out."""
    source = _src(admin.upload_material)
    # The word "embed" appears in the response note telling the admin what to
    # run next; what must be absent is a CALL into the embedding path.
    assert "embed_documents" not in source
    assert "services.ingest" not in source
    assert 'ingest_status="pending"' in source


def test_archiving_is_idempotent_and_keeps_the_row():
    source = _src(admin.archive_material)
    assert 'material.status != "archived"' in source
    assert "delete(" not in source


def test_version_history_is_derived_from_course_and_title():
    """A `replaces_id` column would be one more thing to keep truthful."""
    source = _src(admin.material_versions)
    assert "Material.title == material.title" in source
    assert "Material.version.desc()" in source


# ---------------------------------------------------------------------------
# admin-003 -- the audit log
# ---------------------------------------------------------------------------

def test_every_mutating_admin_route_writes_an_audit_row():
    for fn in (admin.create_department, admin.create_course,
               admin.upload_material, admin.archive_material):
        assert "_audit(" in _src(fn), f"{fn.__name__} writes no audit row"


def test_the_audit_log_resolves_an_actor_email():
    source = _src(admin.audit_log)
    assert "actor_email" in source


def test_the_audit_log_can_be_filtered_by_action_and_actor():
    source = _src(admin.audit_log)
    assert "AuditLog.action == action" in source
    assert "User.email.ilike" in source


def test_audit_actions_match_the_names_the_contract_documents():
    """An admin filters with ?action=, so these strings are an API surface.
    Deriving one from a resulting status wrote 'sourced_content.approved',
    which reads fine and matches nothing anybody would type."""
    from app.routers import teacher

    documented = {
        "material.upload", "material.archive", "course.create",
        "reteach.approve", "sourced_content.approve", "sourced_content.reject",
    }
    written = set()
    for module in (admin, teacher):
        for name, fn in vars(module).items():
            if not callable(fn) or getattr(fn, "__module__", "") != module.__name__:
                continue
            try:
                source = inspect.getsource(fn)
            except (OSError, TypeError):
                continue
            for action in documented:
                if f'"{action}"' in source:
                    written.add(action)

    # The two sourced_content actions are composed from a verb map rather than
    # written as literals. Read the map out of the AST and check what it
    # actually produces -- matching a repr against source text would fail on
    # nothing worse than a change of quote style.
    import ast
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(teacher._decide_sourced)))
    maps = [
        ast.literal_eval(node) for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        # Values must be constants too: the audit `detail=` dict in the same
        # function holds `row.title`, which literal_eval refuses outright.
        and all(isinstance(n, ast.Constant) for n in [*node.keys, *node.values])
    ]
    verbs = next((m for m in maps if set(m) == {"approved", "rejected"}), None)
    assert verbs is not None, (
        "the verb map that builds the sourced_content audit action is gone; "
        "deriving the action from the resulting status writes "
        "'sourced_content.approved', which matches nothing an admin would type"
    )
    written |= {f"sourced_content.{v}" for v in verbs.values()}

    missing = documented - written - {"material.ingest"}
    assert not missing, f"documented audit actions never written: {sorted(missing)}"


# ---------------------------------------------------------------------------
# admin-004 -- the audit log reads as a sentence
# ---------------------------------------------------------------------------

class _Row:
    def __init__(self, action, target=None, detail=None):
        self.action, self.target, self.detail = action, target, detail
        self.id, self.actor_id, self.at = 1, 1, None


def test_every_audit_row_gets_a_readable_summary():
    from app.routers.admin import _audit_summary

    cases = [
        _Row("material.archive", "material:12", {"version": 1}),
        _Row("reteach.approve", "reteach:7", {}),
        _Row("course.create", "course:5", {"code": "CSW2"}),
        _Row("sourced_content.reject", "sourced:3", {"reason": "not peer reviewed"}),
    ]
    for row in cases:
        summary = _audit_summary(row, "priya@example.edu", {"material:12": "Django 5"})
        assert summary and summary[0].isalnum(), summary
        assert row.action not in summary, "the dotted verb must not leak into prose"


def test_an_unmapped_action_still_renders_a_sentence():
    """A new verb appearing as a blank row would look like corrupted data."""
    from app.routers.admin import _audit_summary

    summary = _audit_summary(_Row("something.new", "thing:1"), "a@b.c", {})
    assert "something.new" in summary and summary.startswith("a@b.c")


def test_a_summary_never_prints_a_raw_prefixed_id_when_it_can_avoid_it():
    """The row outlives what it points at. Printing `reteach:32` back is the
    exact technical noise this field exists to remove."""
    from app.routers.admin import _audit_summary

    summary = _audit_summary(
        _Row("reteach.suggest", "reteach:32", {"concept": "one-to-many"}), "a@b.c", {})
    assert "reteach:32" not in summary
    assert "one to many" in summary


def test_the_machine_fields_survive_alongside_the_summary():
    """?action= filters on the dotted verbs and the contract is what an admin
    types them from. Renaming them would break the filter and the contract."""
    source = inspect.getsource(admin.audit_log)
    body = source[source.index("return {"):]
    for field in ('"action": r.action', '"target": r.target',
                  '"detail": r.detail', '"summary"'):
        assert field in body, field


def test_seed_runs_are_hidden_by_default_but_not_deleted():
    from app.routers.admin import SYSTEM_ACTIONS

    assert "seed.run" in SYSTEM_ACTIONS
    source = inspect.getsource(admin.audit_log)
    assert "notin_(SYSTEM_ACTIONS)" in source
    assert "delete" not in source.lower()


def test_asking_for_a_system_action_explicitly_still_returns_it():
    """Otherwise ?action=seed.run would come back empty and the filter would be
    silently lying."""
    source = inspect.getsource(admin.audit_log)
    assert "elif not include_system" in source, (
        "the system filter must not apply when an explicit action was requested"
    )


def test_audit_titles_are_resolved_in_batches():
    """perf-001: a per-row lookup is a network round trip."""
    source = inspect.getsource(admin._audit_titles)
    assert source.count(".in_(") == 2
    assert "db.get(" not in source
