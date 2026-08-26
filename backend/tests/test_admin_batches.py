"""admin-009 / auth-004 tests. No network, no database.

The rules worth locking:
  * a batch's length is a property of its major, never a request field
  * curriculum reuse only crosses years, never majors or departments
  * a teacher password is issued exactly once, in exactly one response
  * teacher accounts are born here and nowhere else -- signup is student-only
"""

from __future__ import annotations

import inspect

import pytest
from fastapi import HTTPException

from app.models import Batch, Course, Department, User
from app.routers import admin_batches
from app.schemas import BatchCourseIn, BatchIn, CurriculumReuseIn, SignupIn, TeacherAddIn, UserOut


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeDB:
    """Just enough Session for the admin_batches endpoints: get/add/flush and
    a scalar() the test can point at one canned row."""

    def __init__(self, get_map=None, scalar_row=None):
        self.get_map = get_map or {}
        self.scalar_row = scalar_row
        self.added = []
        self.deleted = []
        self._next = 900

    def get(self, model, pk):
        return self.get_map.get((model, pk))

    def scalar(self, stmt):
        return self.scalar_row

    def scalars(self, stmt):
        return []

    def add(self, obj):
        self.added.append(obj)
        # The endpoint reads ct.user when serialising; a real CourseTeacher
        # would lazy-load it, which no fake can do, so attach the account the
        # endpoint just created/found.
        if isinstance(obj, User):
            self._last_user = obj
        if obj.__class__ is CourseTeacher:
            obj.user = getattr(self, "_last_user", None)
            from datetime import datetime, timezone
            obj.assigned_at = datetime(2026, 8, 26, tzinfo=timezone.utc)

    def delete(self, obj):
        self.deleted.append(obj)

    def flush(self):
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = self._next
                self._next += 1


from app.models import CourseTeacher  # noqa: E402

class FakeAdmin:
    id = 1
    email = "admin@example.edu"


def dept(pk=3):
    d = Department(name="Computer Science & Engineering")
    d.id = pk
    return d


def make_batch(bid, major="btech", dept_id=3, start=2026, with_curriculum=False):
    b = Batch(major=major, department_id=dept_id, start_year=start,
              end_year=start + {"btech": 4, "bca": 3, "mtech": 2, "mca": 2}[major])
    b.id = bid
    b.department = dept(dept_id)
    if with_curriculum:
        b.curriculum_name = "syllabus-2025.pdf"
        b.curriculum_path = "/somewhere/syllabus-2025.pdf"
    return b


def a_course(cid=5):
    c = Course(code="CSW2", title="Workshop")
    c.id = cid
    return c


def a_user(uid, email, role="teacher", name="T. Eacher"):
    u = User(email=email, password_hash="x", full_name=name, role=role)
    u.id = uid
    return u


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

def test_every_batch_route_requires_an_admin():
    routes = [r for r in admin_batches.router.routes if hasattr(r, "endpoint")]
    assert routes
    for route in routes:
        src = inspect.getsource(route.endpoint)
        assert "admin_only" in src, f"{route.path} does not require an admin"
        assert "teacher_only" not in src


# ---------------------------------------------------------------------------
# Batches: the duration is the major's, not the request's
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("major,years", [("btech", 4), ("bca", 3), ("mtech", 2), ("mca", 2)])
def test_end_year_is_computed_from_the_major(major, years):
    db = FakeDB(get_map={(Department, 3): dept()})
    out = admin_batches.create_batch(
        BatchIn(major=major, department_id=3, start_year=2026), db, FakeAdmin()
    )
    assert out["end_year"] == 2026 + years


def test_an_unknown_major_is_rejected_not_guessed():
    with pytest.raises(HTTPException) as e:
        admin_batches.create_batch(
            BatchIn(major="phd", department_id=3, start_year=2026),
            FakeDB(get_map={(Department, 3): dept()}), FakeAdmin(),
        )
    assert e.value.status_code == 422


def test_an_unknown_department_is_rejected():
    with pytest.raises(HTTPException) as e:
        admin_batches.create_batch(
            BatchIn(major="btech", department_id=99, start_year=2026),
            FakeDB(), FakeAdmin(),
        )
    assert e.value.status_code == 422


def test_the_same_cohort_cannot_be_created_twice():
    db = FakeDB(get_map={(Department, 3): dept()}, scalar_row=make_batch(1))
    with pytest.raises(HTTPException) as e:
        admin_batches.create_batch(
            BatchIn(major="btech", department_id=3, start_year=2026), db, FakeAdmin()
        )
    assert e.value.status_code == 409


# ---------------------------------------------------------------------------
# Curriculum reuse: across years, never across majors or departments
# ---------------------------------------------------------------------------

def _reuse(src, target=None):
    target = target or make_batch(41, start=2026)
    db = FakeDB(get_map={(Batch, target.id): target, (Batch, src.id): src})
    return admin_batches.reuse_curriculum(
        target.id, CurriculumReuseIn(from_batch_id=src.id), db, FakeAdmin()
    )


def test_reuse_carries_the_reference_and_records_where_from():
    out = _reuse(make_batch(40, start=2025, with_curriculum=True))
    assert out["curriculum"]["name"] == "syllabus-2025.pdf"
    assert out["curriculum"]["reused_from_batch_id"] == 40


def test_reuse_from_a_different_department_is_refused():
    with pytest.raises(HTTPException) as e:
        _reuse(make_batch(40, start=2025, dept_id=5, with_curriculum=True))
    assert e.value.status_code == 422


def test_reuse_from_a_different_major_is_refused():
    with pytest.raises(HTTPException) as e:
        _reuse(make_batch(40, major="mtech", start=2025, with_curriculum=True))
    assert e.value.status_code == 422


def test_reuse_from_a_batch_with_no_curriculum_is_refused():
    """The UI keeps that button disabled for exactly this reason; the API
    enforcing it too is what makes the disabled state honest."""
    with pytest.raises(HTTPException) as e:
        _reuse(make_batch(40, start=2025, with_curriculum=False))
    assert e.value.status_code == 422


# ---------------------------------------------------------------------------
# Teachers: issued once, by an admin, with no cap
# ---------------------------------------------------------------------------

def _add_teacher(db, email="new.teacher@example.edu", existing=None):
    if existing is not None:
        db.get_map[(User, existing.id)] = existing
        # no User row is added in this path, but the CourseTeacher still
        # serialises its .user -- that is the existing teacher.
        db._last_user = existing
    db.get_map[(Course, 5)] = a_course()
    # The endpoint runs two scalar() lookups in order: first "does this email
    # exist" (the teacher, or None), then "are they already assigned" (None in
    # these tests). A single canned return would conflate them.
    calls = {"n": 0}

    def scalar(stmt):
        calls["n"] += 1
        if calls["n"] == 1:
            return existing
        return None

    db.scalar = scalar
    return admin_batches.add_course_teacher(5, TeacherAddIn(email=email), db, FakeAdmin())


def test_a_new_teacher_gets_a_password_exactly_once():
    db = FakeDB()
    out = _add_teacher(db)
    assert out["password"], "a newly issued account must carry its password"
    assert len(out["password"]) >= 10
    assert out["teacher"]["email"] == "new.teacher@example.edu"
    assert out["already_assigned"] is False
    # and the account was born a teacher, with a one-way hash
    born = [o for o in db.added if isinstance(o, User)][0]
    assert born.role == "teacher"
    assert out["password"] not in born.password_hash


def test_an_existing_teacher_is_linked_without_a_new_password():
    db = FakeDB()
    out = _add_teacher(db, existing=a_user(2, "ravi@example.edu"))
    assert out["password"] is None
    assert not any(isinstance(o, User) for o in db.added), \
        "no second account may be created for an existing teacher"


def test_a_student_email_cannot_be_turned_into_a_teacher():
    with pytest.raises(HTTPException) as e:
        _add_teacher(FakeDB(), existing=a_user(9, "asha@example.edu", role="student"))
    assert e.value.status_code == 409


def test_removing_someone_not_assigned_is_a_404_not_a_silent_ok():
    with pytest.raises(HTTPException) as e:
        admin_batches.remove_course_teacher(5, 2, FakeDB(), FakeAdmin())
    assert e.value.status_code == 404


# ---------------------------------------------------------------------------
# auth-004: signup is student-only
# ---------------------------------------------------------------------------

def test_signup_has_no_role_field_to_set():
    """The only way to be a teacher is to be issued one by an admin."""
    assert "role" not in SignupIn.model_fields
    assert "university" in SignupIn.model_fields
    assert "roll_number" in SignupIn.model_fields


def test_signup_body_declares_the_role_in_code_not_in_the_request():
    src = inspect.getsource(__import__("app.routers.auth", fromlist=["signup"]).signup)
    assert 'role="student"' in src


def test_user_out_carries_the_enrolment_fields():
    assert "university" in UserOut.model_fields
    assert "roll_number" in UserOut.model_fields


# ---------------------------------------------------------------------------
# admin-010: subjects belong to batches
# ---------------------------------------------------------------------------

def a_course_row(cid=5, code="CSW2", title="Workshop", semester=3, batches=None):
    c = Course(code=code, title=title, semester=semester)
    c.id = cid
    c.department_id = 3
    c.batches = list(batches or [])
    return c


def test_linking_an_existing_subject_puts_it_in_the_batch():
    batch = make_batch(40)
    course = a_course_row()
    db = FakeDB(get_map={(Batch, 40): batch, (Course, 5): course})
    out = admin_batches.add_batch_course(40, BatchCourseIn(course_id=5), db, FakeAdmin())
    assert out["batch_ids"] == [40]
    assert course.batches == [batch]


def test_creating_a_subject_inherits_the_batch_department():
    """The admin already picked the cohort; asking for its department again
    would be a question with exactly one right answer."""
    batch = make_batch(40, dept_id=3)
    db = FakeDB(get_map={(Batch, 40): batch})
    db.scalar = lambda stmt: None  # no code collision
    out = admin_batches.add_batch_course(
        40, BatchCourseIn(code="cs301", title="Operating Systems", semester=5),
        db, FakeAdmin())
    created = [o for o in db.added if isinstance(o, Course)][0]
    assert created.department_id == 3
    assert created.code == "CS301", "codes are normalised upper-case"
    assert out["semester"] == 5


def test_the_same_subject_cannot_be_added_to_one_batch_twice():
    batch = make_batch(40)
    course = a_course_row(batches=[batch])
    db = FakeDB(get_map={(Batch, 40): batch, (Course, 5): course})
    with pytest.raises(HTTPException) as e:
        admin_batches.add_batch_course(40, BatchCourseIn(course_id=5), db, FakeAdmin())
    assert e.value.status_code == 409


def test_a_duplicate_course_code_is_refused_rather_than_silently_linked():
    batch = make_batch(40)
    db = FakeDB(get_map={(Batch, 40): batch}, scalar_row=a_course_row())
    with pytest.raises(HTTPException) as e:
        admin_batches.add_batch_course(
            40, BatchCourseIn(code="CSW2", title="Workshop"), db, FakeAdmin())
    assert e.value.status_code == 409


def test_one_subject_can_serve_several_cohorts():
    """Many-to-many is the point: cohorts share the corpus, the diagnostic and
    the misconception history, so a row per cohort would fragment all three."""
    b1, b2 = make_batch(40, start=2025), make_batch(41, start=2026)
    course = a_course_row(batches=[b1])
    db = FakeDB(get_map={(Batch, 41): b2, (Course, 5): course})
    out = admin_batches.add_batch_course(41, BatchCourseIn(course_id=5), db, FakeAdmin())
    assert sorted(out["batch_ids"]) == [40, 41]


def test_unlinking_leaves_the_subject_and_the_other_cohorts_alone():
    b1, b2 = make_batch(40), make_batch(41, start=2027)
    course = a_course_row(batches=[b1, b2])
    db = FakeDB(get_map={(Batch, 40): b1, (Course, 5): course})
    admin_batches.remove_batch_course(40, 5, db, FakeAdmin())
    assert [b.id for b in course.batches] == [41]
    assert course not in db.deleted, "unlink must never delete the subject"


def test_unlinking_something_not_in_the_batch_is_a_404():
    b1 = make_batch(40)
    course = a_course_row(batches=[])
    db = FakeDB(get_map={(Batch, 40): b1, (Course, 5): course})
    with pytest.raises(HTTPException) as e:
        admin_batches.remove_batch_course(40, 5, db, FakeAdmin())
    assert e.value.status_code == 404


def test_the_link_body_demands_exactly_one_form():
    with pytest.raises(Exception):
        BatchCourseIn()  # neither
    with pytest.raises(Exception):
        BatchCourseIn(course_id=5, code="CS301", title="OS")  # both


def test_batch_courses_are_listed_by_semester_then_code():
    batch = make_batch(40)
    batch.courses = [
        a_course_row(1, "CS400", "Later", 6),
        a_course_row(2, "CS101", "Early", 1),
        a_course_row(3, "CS999", "Undated", None),
        a_course_row(4, "CS102", "Also early", 1),
    ]
    db = FakeDB(get_map={(Batch, 40): batch})
    codes = [c["code"] for c in admin_batches.list_batch_courses(40, db, FakeAdmin())["items"]]
    # semester order, ties by code, and an unset semester sorts LAST rather
    # than pretending to be semester 0
    assert codes == ["CS101", "CS102", "CS400", "CS999"]
