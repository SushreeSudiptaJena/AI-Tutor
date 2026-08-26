"""student-010 / teacher-009 tests. No network, no database.

The rules worth locking:
  * batch_id decides what is OFFERED; course_id is the ACTIVE subject and is
    what every scoped route reads
  * a student can only switch to a subject their own cohort offers
  * a teacher can only switch to a subject they are assigned to
  * enrolling never wipes gaps, mastery or practice history
"""

from __future__ import annotations

import inspect

import pytest
from fastapi import HTTPException

from app.models import Batch, Course, CourseTeacher, Department, User
from app.routers import student as student_router
from app.routers import teacher as teacher_router
from app.schemas import ActiveSubjectIn, EnrollIn, UserOut


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeDB:
    def __init__(self, get_map=None, scalar_row=None, scalars_rows=()):
        self.get_map = get_map or {}
        self.scalar_row = scalar_row
        self.scalars_rows = list(scalars_rows)
        self.flushed = 0

    def get(self, model, pk):
        return self.get_map.get((model, pk))

    def scalar(self, stmt):
        return self.scalar_row

    def scalars(self, stmt):
        rows = self.scalars_rows

        class _R:
            def all(self_inner):
                return rows

        return _R()

    def flush(self):
        self.flushed += 1


def dept(pk=3, name="Computer Science & Engineering"):
    d = Department(name=name)
    d.id = pk
    return d


def a_course(cid, code, title="Subject", semester=None, batches=None):
    c = Course(code=code, title=title, semester=semester)
    c.id = cid
    c.department_id = 3
    c.batches = list(batches or [])
    return c


def a_batch(bid=7, start=2026, courses=()):
    b = Batch(major="btech", department_id=3, start_year=start, end_year=start + 4)
    b.id = bid
    b.department = dept()
    b.courses = list(courses)
    return b


def a_student(uid=9, course_id=None, batch_id=None):
    u = User(email="asha@example.edu", password_hash="x", full_name="Asha R",
             role="student", preferred_language="en")
    u.id = uid
    u.course_id = course_id
    u.batch_id = batch_id
    return u


def a_teacher(uid=2, course_id=None):
    u = User(email="ravi@example.edu", password_hash="x", full_name="Ravi Menon",
             role="teacher", preferred_language="en")
    u.id = uid
    u.course_id = course_id
    u.batch_id = None
    return u


# ---------------------------------------------------------------------------
# student-010 -- enrolment
# ---------------------------------------------------------------------------

def test_enrolling_sets_the_cohort_and_picks_the_earliest_subject():
    batch = a_batch(courses=[a_course(2, "CS201", semester=3),
                             a_course(1, "CS101", semester=1)])
    user = a_student()
    db = FakeDB(get_map={(Batch, 7): batch})
    out = student_router.enroll(EnrollIn(batch_id=7), db, user)
    assert out.batch_id == 7
    assert out.course_id == 1, "the earliest semester is the sensible default"


def test_enrolling_honours_an_explicit_subject():
    batch = a_batch(courses=[a_course(1, "CS101", semester=1),
                             a_course(2, "CS201", semester=3)])
    user = a_student()
    db = FakeDB(get_map={(Batch, 7): batch})
    out = student_router.enroll(EnrollIn(batch_id=7, course_id=2), db, user)
    assert out.course_id == 2


def test_enrolling_in_a_batch_with_no_subjects_is_refused_not_half_done():
    """A cohort with nothing to study would leave a student enrolled and
    stuck on an empty dashboard."""
    user = a_student()
    db = FakeDB(get_map={(Batch, 7): a_batch(courses=[])})
    with pytest.raises(HTTPException) as e:
        student_router.enroll(EnrollIn(batch_id=7), db, user)
    assert e.value.status_code == 422
    assert user.batch_id is None, "nothing may be written on the refused path"


def test_a_subject_from_another_cohort_cannot_be_chosen_at_enrolment():
    batch = a_batch(courses=[a_course(1, "CS101", semester=1)])
    db = FakeDB(get_map={(Batch, 7): batch})
    with pytest.raises(HTTPException) as e:
        student_router.enroll(EnrollIn(batch_id=7, course_id=99), db, a_student())
    assert e.value.status_code == 422


def test_enrolment_touches_only_the_two_fields():
    """Gaps, mastery and practice are per-subject rows; enrolment must not
    delete or reset any of them -- it changes what is offered, not what
    happened."""
    src = inspect.getsource(student_router.enroll)
    for forbidden in ("delete(", "Gap)", "Mastery)", "PracticeSet)", "Attempt)"):
        assert forbidden not in src, f"enrol path must not touch {forbidden}"


# ---------------------------------------------------------------------------
# student-010 -- the subject list and the switcher
# ---------------------------------------------------------------------------

def test_subjects_are_listed_in_curriculum_order_with_the_active_one_flagged():
    batch = a_batch(courses=[
        a_course(3, "CS400", semester=6),
        a_course(1, "CS101", semester=1),
        a_course(4, "CS999", semester=None),
        a_course(2, "CS102", semester=1),
    ])
    user = a_student(course_id=2, batch_id=7)
    db = FakeDB(get_map={(Batch, 7): batch})
    out = student_router.list_my_subjects(db, user)
    assert [c["code"] for c in out["items"]] == ["CS101", "CS102", "CS400", "CS999"]
    assert [c["is_current"] for c in out["items"]] == [False, True, False, False]
    assert out["batch"]["id"] == 7


def test_a_student_who_has_not_enrolled_gets_an_empty_list_not_an_error():
    out = student_router.list_my_subjects(FakeDB(), a_student())
    assert out == {"batch": None, "items": []}


def test_switching_to_a_subject_the_cohort_offers_moves_the_whole_surface():
    batch = a_batch(courses=[a_course(1, "CS101"), a_course(2, "CS201")])
    user = a_student(course_id=1, batch_id=7)
    db = FakeDB(get_map={(Batch, 7): batch})
    out = student_router.set_active_subject(ActiveSubjectIn(course_id=2), db, user)
    assert out.course_id == 2
    assert out.batch_id == 7, "switching subject never changes the cohort"


def test_switching_outside_the_cohort_is_forbidden():
    """Every student route scopes by course_id, so an unchecked switcher
    would be a way to read another cohort's material."""
    batch = a_batch(courses=[a_course(1, "CS101")])
    user = a_student(course_id=1, batch_id=7)
    db = FakeDB(get_map={(Batch, 7): batch})
    with pytest.raises(HTTPException) as e:
        student_router.set_active_subject(ActiveSubjectIn(course_id=42), db, user)
    assert e.value.status_code == 403
    assert user.course_id == 1, "the refused switch must not have happened"


def test_a_student_with_no_cohort_cannot_switch_at_all():
    with pytest.raises(HTTPException) as e:
        student_router.set_active_subject(
            ActiveSubjectIn(course_id=1), FakeDB(), a_student())
    assert e.value.status_code == 403


# ---------------------------------------------------------------------------
# teacher-009 -- the console's subject
# ---------------------------------------------------------------------------

def _assignment(course, user_id=2):
    ct = CourseTeacher(course_id=course.id, user_id=user_id)
    ct.id = course.id
    ct.course = course
    return ct


def test_a_teacher_sees_their_assigned_subjects_with_the_cohorts_that_take_them():
    batch = a_batch(bid=7, start=2026)
    course = a_course(5, "CSW2", "Workshop", semester=3, batches=[batch])
    user = a_teacher(course_id=5)
    db = FakeDB(scalars_rows=[_assignment(course)])
    out = teacher_router.my_subjects(db, user)
    assert len(out["items"]) == 1
    item = out["items"][0]
    assert item["code"] == "CSW2" and item["is_current"] is True
    assert item["batches"][0]["start_year"] == 2026
    assert item["batches"][0]["department"] == "Computer Science & Engineering"


def test_a_teacher_switches_only_to_a_subject_they_are_assigned_to():
    user = a_teacher(course_id=5)
    db = FakeDB(scalar_row=_assignment(a_course(6, "DLD")))
    out = teacher_router.set_active_subject(ActiveSubjectIn(course_id=6), db, user)
    assert out.course_id == 6


def test_a_teacher_cannot_switch_to_a_colleagues_subject():
    user = a_teacher(course_id=5)
    db = FakeDB(scalar_row=None)  # no assignment row
    with pytest.raises(HTTPException) as e:
        teacher_router.set_active_subject(ActiveSubjectIn(course_id=99), db, user)
    assert e.value.status_code == 403
    assert user.course_id == 5


def test_the_teacher_switcher_is_teacher_only():
    src = inspect.getsource(teacher_router.set_active_subject)
    assert "teacher_only" in src
    src2 = inspect.getsource(teacher_router.my_subjects)
    assert "teacher_only" in src2


def test_user_out_carries_batch_id():
    assert "batch_id" in UserOut.model_fields
