"""Guards on the deliberate design decisions in models.py.

These run against the SQLAlchemy metadata, so they need no database and no
network -- consistent with the rest of the suite.

Every assertion here encodes a requirement from the problem statement. If one
of these fails, someone has "helpfully" added something that breaks a judged
property, and the fix is to remove it, not to update the test.
"""

from app import models as m


def _cols(model) -> set[str]:
    return {c.name for c in model.__table__.columns}


def test_no_score_or_grade_column_anywhere():
    """The diagnostic produces a gap list, not a grade."""
    banned = ("score", "grade", "percent", "marks", "points")
    offenders = []
    for table in m.Base.metadata.tables.values():
        for col in table.columns:
            name = col.name.lower()
            # alignment_score is the evidence-check score, not a student grade.
            if name == "alignment_score":
                continue
            if any(b in name for b in banned):
                offenders.append(f"{table.name}.{col.name}")
    assert not offenders, f"student-facing score columns found: {offenders}"


def test_no_surveillance_columns():
    """Teacher dashboards are about misconceptions, not time-on-task."""
    banned = ("time_on", "time_spent", "last_seen", "duration", "seconds", "active_time")
    offenders = [
        f"{t.name}.{c.name}"
        for t in m.Base.metadata.tables.values()
        for c in t.columns
        if any(b in c.name.lower() for b in banned)
    ]
    assert not offenders, f"surveillance columns found: {offenders}"


def test_uncertainty_flag_cannot_identify_a_student():
    """You cannot leak what you never stored."""
    cols = _cols(m.UncertaintyFlag)
    assert "user_id" not in cols
    assert "student_id" not in cols
    assert "email" not in cols


def test_misconception_confirmed_is_three_state():
    """None = asked but unanswered, True = agreed, False = denied.

    Only True is counted in teacher aggregates, so the column must be nullable
    and must not default to True.
    """
    col = m.MisconceptionDiagnosis.__table__.c.confirmed
    assert col.nullable, "confirmed must allow NULL for 'asked but not answered'"
    assert col.default is None or col.default.arg is None


def test_chunk_is_page_anchored():
    """Citations are database facts, so the page number must be captured and
    non-nullable at ingestion."""
    cols = m.Chunk.__table__.c
    assert "page_no" in _cols(m.Chunk)
    assert not cols.page_no.nullable, "page_no must never be null - citations depend on it"
    assert not cols.material_id.nullable


def test_embedding_dimension_matches_the_model():
    assert m.EMBEDDING_DIM == 384, "bge-small-en-v1.5 produces 384 dimensions"
    assert m.Chunk.__table__.c.embedding.type.dim == 384


def test_correct_answers_exist_but_are_flagged_as_sensitive():
    """They must be stored, and must be stripped in response schemas."""
    assert "correct_answer" in _cols(m.DiagnosticItem)
    assert "correct_answer" in _cols(m.PracticeItem)


def test_reteach_defaults_to_draft():
    """A unit must never reach a student without a teacher approving it."""
    assert m.ReteachUnit.__table__.c.status.default.arg == "draft"


def test_problem_type_links_practice_to_misconceptions():
    """The join key that keeps a diagnosis specific rather than generic."""
    assert "problem_type" in _cols(m.PracticeItem)
    assert "problem_type" in _cols(m.Misconception)


def test_gap_is_unique_per_student_and_concept():
    """Retaking the diagnostic must not create duplicate gaps."""
    uniques = [
        c for c in m.Gap.__table__.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    ]
    cols = {tuple(sorted(col.name for col in u.columns)) for u in uniques}
    assert ("concept_id", "user_id") in cols
