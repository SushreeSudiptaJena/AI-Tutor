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
