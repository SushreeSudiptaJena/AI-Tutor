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


# ---------------------------------------------------------------------------
# admin-005 -- semester, admission batches, and the term window
# ---------------------------------------------------------------------------

def test_the_new_course_fields_are_all_nullable():
    """They were added to a table that already had rows in the shared database.
    A NOT NULL here would break every course that predates them."""
    from app.models import Course

    cols = Course.__table__.columns
    for name in ("semester", "admission_batches", "term_start", "term_end"):
        assert name in cols, name
        assert cols[name].nullable, f"{name} must be nullable"


def test_a_course_with_no_dates_is_never_in_term():
    """'We do not know when this term runs' and 'this term runs all year' must
    not look the same to the admin-006 delete guard."""
    from datetime import date

    from app.models import Course

    assert Course(code="X", title="X").in_term(date(2026, 1, 1)) is False
    assert Course(code="X", title="X", term_start=date(2026, 1, 1)).in_term(
        date(2026, 1, 1)) is False


def test_in_term_is_inclusive_of_both_ends():
    from datetime import date

    from app.models import Course

    c = Course(code="X", title="X",
               term_start=date(2026, 1, 10), term_end=date(2026, 5, 20))
    assert c.in_term(date(2026, 1, 10)) is True
    assert c.in_term(date(2026, 5, 20)) is True
    assert c.in_term(date(2026, 1, 9)) is False
    assert c.in_term(date(2026, 5, 21)) is False


def test_term_input_rejects_an_impossible_window_and_bad_values():
    import pydantic
    import pytest

    from app.schemas import CourseTermIn

    CourseTermIn(semester=3, admission_batches=[2024, 2025])
    for bad in ({"semester": 0}, {"semester": 11}, {"admission_batches": [1999]},
                {"term_start": "2025-12-15", "term_end": "2025-08-01"}):
        with pytest.raises(pydantic.ValidationError):
            CourseTermIn(**bad)


def test_admission_batches_are_sorted_and_deduplicated():
    """[2025, 2024, 2024] and [2024, 2025] are the same fact; storing them
    differently makes them compare unequal."""
    from app.schemas import CourseTermIn

    assert CourseTermIn(admission_batches=[2025, 2024, 2024]).admission_batches == [2024, 2025]


def test_setting_the_term_is_a_partial_update():
    """Setting the semester must not silently wipe the dates, and a field can
    still be cleared by sending it as null."""
    source = inspect.getsource(admin.set_course_term)
    assert "model_fields_set" in source
    assert "if field not in sent" in source


def test_the_merged_window_is_validated_not_just_the_request():
    """The schema can only compare two dates that arrive together. Sending one
    that contradicts a stored one would write a window in which in_term() is
    false for every date -- quietly disabling the delete guard."""
    source = inspect.getsource(admin.set_course_term)
    assert 'if "term_start" in sent else course.term_start' in source
    assert "new_end < new_start" in source


def test_setting_the_term_writes_an_audit_row():
    assert '"course.set_term"' in inspect.getsource(admin.set_course_term)


# ---------------------------------------------------------------------------
# admin-006 -- deleting material, and the guard that makes it safe
# ---------------------------------------------------------------------------

def test_deleting_ingested_material_is_refused_mid_term():
    """Deleting a book out from under a class in week six is the thing
    archiving was invented to prevent."""
    source = inspect.getsource(admin.delete_material)
    assert "course.in_term(date.today())" in source
    assert '"mid_term"' in source
    assert "HTTP_409_CONFLICT" in source


def test_the_mid_term_guard_only_applies_to_ingested_material():
    """An upload mistake should be fixable the day it happens."""
    source = inspect.getsource(admin.delete_material)
    assert "if chunk_count and course is not None and course.in_term" in source


def test_the_audit_row_is_written_before_the_delete_and_outlives_it():
    """An audit row that vanished with its subject would make deletion the one
    act nobody could review."""
    source = inspect.getsource(admin.delete_material)
    assert source.index('"material.delete"') < source.index("db.delete(material)")
    from app.models import AuditLog
    assert not AuditLog.__table__.columns["target"].foreign_keys, (
        "target must stay a plain string, or the trail dies with the material"
    )


def test_delete_does_not_remove_the_source_file():
    """Deleting a row must not throw away the only copy of a book."""
    source = inspect.getsource(admin.delete_material)
    for banned in ("unlink", "os.remove", "shutil.rmtree", "Path.unlink"):
        assert banned not in source, f"{banned} would destroy the uploaded file"
    assert "source_path_left_on_disk" in source


def test_there_is_no_refuse_if_cited_check_because_nothing_stores_a_citation():
    """A Citation is built from live retrieval and never written down. A
    'refuse if cited' check could only be a guess dressed as a guarantee."""
    from app import models

    for name in dir(models):
        cls = getattr(models, name)
        table = getattr(cls, "__table__", None)
        if table is None or name == "Chunk":
            continue
        assert "chunk_id" not in table.columns, (
            f"{name} now stores a chunk_id -- admin-006's reasoning needs revisiting"
        )


def test_archiving_still_exists_and_is_untouched():
    """Delete is a bounded exception, not a replacement."""
    source = inspect.getsource(admin.archive_material)
    assert 'material.status = "archived"' in source
    assert "db.delete" not in source


def test_a_delete_summary_names_what_was_deleted():
    """The material row is gone by definition, so the title has to come from
    the audit detail -- and 'deleted something that has since been removed'
    states the obvious twice."""
    from app.routers.admin import _audit_summary

    row = _Row("material.delete", "material:12",
               {"title": "DLD Assignment 1", "version": 1})
    summary = _audit_summary(row, "admin@example.edu", {})
    assert "DLD Assignment 1" in summary
    assert "since removed" not in summary
    assert "material:12" not in summary
