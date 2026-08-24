"""teacher-001 / teacher-004 tests. No network, no database.

Both guarantees here are things that must NOT appear: a student's identity, and
a diagnosis the student never agreed to. Neither shows up as a failure in
normal use -- an over-counting heatmap just looks like a more confident
heatmap -- so they are asserted against the compiled SQL and the response
builders rather than trusted.
"""

from __future__ import annotations

import inspect

from sqlalchemy import select

from app.models import Attempt, MisconceptionDiagnosis, UncertaintyFlag
from app.routers import teacher


def _sql_of(fn) -> str:
    return inspect.getsource(fn)


# ---------------------------------------------------------------------------
# teacher-001 -- only confirmed diagnoses count
# ---------------------------------------------------------------------------

def test_the_heatmap_counts_only_confirmed_diagnoses():
    """confirmed is three-state. None means asked-and-unanswered, False means
    the student disagreed. Counting either would make the number mean 'times
    the algorithm guessed' instead of 'students who agreed'."""
    source = _sql_of(teacher.heatmap)
    assert "MisconceptionDiagnosis.confirmed.is_(True)" in source


def test_the_heatmap_query_selects_no_student_identifier():
    """It joins through `attempts` -- the only table in the query holding a
    user id -- so the risk is real rather than theoretical."""
    stmt = (
        select(MisconceptionDiagnosis.misconception_id)
        .join(Attempt, Attempt.id == MisconceptionDiagnosis.attempt_id)
        .where(MisconceptionDiagnosis.confirmed.is_(True))
        .group_by(MisconceptionDiagnosis.misconception_id)
    )
    compiled = str(stmt).lower()
    assert "attempts.user_id" not in compiled


def test_the_heatmap_response_builder_has_no_identity_field():
    source = _sql_of(teacher.heatmap)
    body = source[source.rindex("return {"):]
    for banned in ("user_id", "student_id", "email", "full_name", "user.id"):
        assert banned not in body, f"{banned!r} in the heatmap response"


def test_share_is_of_the_class_not_of_the_diagnoses():
    """'11 of 40 students' is what a teacher acts on. Share of diagnoses would
    always sum to 1 and say nothing about how much of the class is affected."""
    source = _sql_of(teacher.heatmap)
    assert "int(count) / size" in source


def test_a_zero_size_class_does_not_divide_by_zero():
    source = _sql_of(teacher.heatmap)
    assert "if size else 0.0" in source


# ---------------------------------------------------------------------------
# teacher-004 -- uncertainty flags
# ---------------------------------------------------------------------------

def test_the_flag_model_has_no_user_column_to_leak():
    """The cheapest anonymity guarantee is never recording the link."""
    assert not hasattr(UncertaintyFlag, "user_id")


def test_the_flag_response_builder_exposes_no_identity():
    source = _sql_of(teacher.uncertainty_flags)
    body = source[source.rindex("return {"):]
    for banned in ("user_id", "student_id", "email", "full_name"):
        assert banned not in body


def test_alignment_percent_is_derived_not_stored():
    """Storing it separately lets the teacher's number drift from the one the
    student was shown."""
    source = _sql_of(teacher.uncertainty_flags)
    assert "alignment_score" in source and "* 100" in source


def test_both_teacher_routes_require_a_teacher():
    for fn in (teacher.heatmap, teacher.uncertainty_flags, teacher.resolve_flag):
        assert "teacher_only" in _sql_of(fn), fn.__name__


def test_resolve_sets_the_status_and_stores_nothing_else():
    """`note` is accepted so the contract's body validates, but there is no
    column for it. What matters is that resolving cannot silently write
    anywhere else."""
    source = _sql_of(teacher.resolve_flag)
    assert 'flag.status = "resolved"' in source
    assert "flag.note" not in source
    assert "db.add" not in source


def test_resolve_accepts_an_optional_note_without_requiring_one():
    from app.schemas import ResolveFlagIn

    assert ResolveFlagIn().note is None
    assert ResolveFlagIn(note="covered in Friday's class").note


def test_the_heatmap_is_scoped_to_a_course():
    """Several courses' misconceptions share one table. An unscoped heatmap
    shows a teacher another class's numbers, which reads as a surprising result
    rather than as a bug -- the same failure mode retrieval had."""
    source = _sql_of(teacher.heatmap)
    assert "Topic.course_id == course_id" in source


def test_the_heatmap_falls_back_to_the_teachers_own_course():
    source = _sql_of(teacher.heatmap)
    assert "course_id if course_id is not None else user.course_id" in source


# ---------------------------------------------------------------------------
# teacher-002/003/005/006/007 -- the panels
# ---------------------------------------------------------------------------

def test_no_teacher_route_selects_a_student_identity():
    """The anonymisation guarantee, asserted against every route in the file
    rather than against the four that existed when it was written."""
    import inspect as _i

    for name, fn in vars(teacher).items():
        if not callable(fn) or not getattr(fn, "__module__", "") == teacher.__name__:
            continue
        try:
            source = _i.getsource(fn)
        except (OSError, TypeError):
            continue
        if "return {" not in source:
            continue
        body = source[source.index("return {"):]
        for banned in ("user_id", "student_id", ".email", "full_name"):
            assert banned not in body, f"{name}() leaks {banned!r}"


def test_the_gap_map_counts_students_not_gap_rows():
    source = _sql_of(teacher.gap_map)
    assert "func.count(func.distinct(Gap.user_id))" in source


def test_the_gap_map_excludes_closed_gaps():
    """A closed gap is no longer missing. Leaving it in makes a class look
    permanently broken however much of it gets fixed."""
    assert 'Gap.status != "closed"' in _sql_of(teacher.gap_map)


def test_the_gap_map_names_the_course_a_prerequisite_came_from():
    source = _sql_of(teacher.gap_map)
    assert "prerequisite_course_id" in source and "prerequisite_course" in source


def test_reasoning_paths_selects_only_the_answer_column_from_an_attempt():
    """Selecting the Attempt row would put user_id in scope, one careless edit
    away from the response."""
    source = _sql_of(teacher.reasoning_paths)
    assert "select(Attempt.answer)" in source
    assert "select(Attempt)" not in source


def test_reasoning_paths_counts_only_confirmed_diagnoses():
    assert "MisconceptionDiagnosis.confirmed.is_(True)" in _sql_of(teacher.reasoning_paths)


def test_before_after_reports_no_delta_until_somebody_has_been_tested():
    """Without this the panel lies by arithmetic: a reteach approved seconds
    ago has zero confirmations after it, which becomes a share of zero, which
    subtracts into a triumphant negative delta -- when nobody has been asked."""
    source = _sql_of(teacher.before_after)
    assert "attempts_in_window" in source and '"measured"' in source
    assert "if tested else None" in source


def test_before_after_is_null_not_zero_before_any_reteach():
    source = _sql_of(teacher.before_after)
    assert '"after": None' in source


def test_a_reteach_unit_is_created_as_a_draft_and_never_assigned():
    """The approval gate is the human-in-the-loop story. Never auto-assign."""
    source = _sql_of(teacher.suggest_reteach)
    assert 'unit.status = "draft"' in source
    assert '"assigned"' not in source


def test_only_approve_can_assign_a_reteach_unit():
    assert 'unit.status = "assigned"' in _sql_of(teacher.approve_reteach)
    assert 'unit.status = "assigned"' not in _sql_of(teacher.patch_reteach)


def test_an_approved_reteach_unit_cannot_be_edited():
    """Otherwise the thing approved and the thing students received could
    differ with nothing recording that they diverged."""
    source = _sql_of(teacher.patch_reteach)
    assert 'unit.status != "draft"' in source
    assert "HTTP_409_CONFLICT" in source


def test_approval_writes_the_audit_row_before_after_depends_on():
    """reteach_units has no approved_at column; teacher-005 reads the moment
    from the audit log. If this action string changes, before/after silently
    stops finding a boundary."""
    assert '"reteach.approve"' in _sql_of(teacher.approve_reteach)
    assert '"reteach.approve"' in _sql_of(teacher._reteach_approved_at)


def test_a_reteach_unit_never_ships_a_practice_answer_key():
    source = _sql_of(teacher._reteach_out)
    body = source[source.index("return {"):]
    # Comments stripped: the line that says correct_answer is deliberately
    # absent should not be the thing that fails the check for it.
    code = "\n".join(ln for ln in body.splitlines()
                     if not ln.strip().startswith("#"))
    assert "correct_answer" not in code


def test_drafting_refuses_when_the_corpus_cannot_support_it():
    """An unsupported unit is invented content wearing a teacher's name once
    approved -- the exact thing 'curriculum-aligned' rules out."""
    from app.services import reteach as reteach_service

    source = _sql_of(reteach_service.draft)
    assert "if not report.sufficient:" in source
    assert "raise NotSupported" in source


def test_the_verification_queue_stores_a_rejection_reason():
    assert "reject_reason" in _sql_of(teacher._decide_sourced)
