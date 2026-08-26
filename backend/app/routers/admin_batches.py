"""admin-009 -- batches, curriculum, teacher assignment, dashboard metrics.

A restructure of the admin surface: cohorts are first-class (a major in a
department, start year to the major's fixed end), each batch carries a
curriculum document (uploaded once or reused from the previous year's batch
of the same major + department), and teachers are assigned per subject by an
admin who issues their password -- self-serve teacher signup is gone
(auth-004).

Split from admin.py rather than appended to it: that file is person-tested
history; this surface is new. The audit verb convention is shared.
"""

from __future__ import annotations

import re
import secrets
import unicodedata
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..config import MAJOR_YEARS, REPO_ROOT
from ..db import get_db
from ..deps import admin_only
from ..models import (
    AuditLog,
    Batch,
    batch_courses,
    Course,
    CourseTeacher,
    Department,
    Material,
    User,
)
from ..schemas import BatchCourseIn, BatchIn, CurriculumReuseIn, TeacherAddIn
from ..security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

UPLOAD_DIR = REPO_ROOT / "backend" / "data" / "pdfs"

MAX_CURRICULUM_BYTES = 10 * 1024 * 1024  # pdf/docx only, per the contract
CURRICULUM_SUFFIXES = {".pdf", ".docx"}


def _audit(db: OrmSession, user: User, action: str, target: str, detail: dict):
    db.add(AuditLog(actor_id=user.id, action=action, target=target, detail=detail))


def _safe_name(name: str) -> str:
    """Same normalisation as admin._safe_name: ASCII, no separators."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name).strip("-._")
    return (cleaned or "batch")[:80]


def _batch_out(b: Batch) -> dict:
    return {
        "id": b.id,
        "major": b.major,
        "department": {"id": b.department_id, "name": b.department.name},
        "start_year": b.start_year,
        "end_year": b.end_year,
        "course_count": len(b.courses),
        "curriculum": (
            {
                "name": b.curriculum_name,
                "reused_from_batch_id": b.reused_from_batch_id,
            }
            if b.curriculum_name
            else None
        ),
    }


# --- batches -----------------------------------------------------------------

@router.get("/batches")
def list_batches(
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    rows = db.scalars(
        select(Batch).order_by(Batch.start_year.desc(), Batch.id.desc())
    ).all()
    return {"items": [_batch_out(b) for b in rows]}


@router.post("/batches", status_code=status.HTTP_201_CREATED)
def create_batch(
    body: BatchIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """A cohort: major + department + start year; end year is computed.

    The duration is a property of the major (config.MAJOR_YEARS), not a
    request field -- an admin who could set it would eventually set it wrong,
    and a 3-year BTech is the kind of data error nobody notices until a
    certificate is printed.
    """
    if body.major not in MAJOR_YEARS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error",
                    "message": f"major must be one of {', '.join(MAJOR_YEARS)}."},
        )
    dept = db.get(Department, body.department_id)
    if dept is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error", "message": "No such department."},
        )
    dup = db.scalar(
        select(Batch).where(
            Batch.major == body.major,
            Batch.department_id == body.department_id,
            Batch.start_year == body.start_year,
        )
    )
    if dup is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": "That batch already exists.",
                    "detail": {"batch_id": dup.id}},
        )

    batch = Batch(
        major=body.major,
        department_id=body.department_id,
        start_year=body.start_year,
        end_year=body.start_year + MAJOR_YEARS[body.major],
        created_by_id=user.id,
        # the relationship, not just the fk: _batch_out reads department.name
        department=dept,
    )
    db.add(batch)
    db.flush()
    _audit(db, user, "batch.create", f"batch:{batch.id}",
           {"major": batch.major, "department": dept.name,
            "years": f"{batch.start_year}-{batch.end_year}"})
    return _batch_out(batch)


@router.post("/batches/{batch_id}/curriculum")
def upload_curriculum(
    batch_id: int,
    file: UploadFile = File(...),
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Attach the batch's curriculum document (pdf/docx, <=10 MB).

    Stored, not ingested: nothing in this build consumes a curriculum file,
    and handing it to the ingest queue would advertise an ingest that never
    runs. It exists so the admin can point at it and the record survives.
    """
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such batch."},
        )
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in CURRICULUM_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request",
                    "message": "Curriculum must be a .pdf or .docx file."},
        )
    try:
        data = file.file.read(MAX_CURRICULUM_BYTES + 1)
    finally:
        file.file.close()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": "That file is empty."},
        )
    if len(data) > MAX_CURRICULUM_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request",
                    "message": "Curriculum files are limited to 10 MB."},
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = (f"curriculum-{batch.major}-{_safe_name(batch.department.name)}"
            f"-{batch.start_year}{suffix}")
    (UPLOAD_DIR / name).write_bytes(data)
    batch.curriculum_name = file.filename or name
    batch.curriculum_path = str(UPLOAD_DIR / name)
    batch.reused_from_batch_id = None
    db.flush()
    _audit(db, user, "batch.curriculum", f"batch:{batch.id}",
           {"file": batch.curriculum_name, "bytes": len(data)})
    return _batch_out(batch)


@router.post("/batches/{batch_id}/curriculum/reuse")
def reuse_curriculum(
    batch_id: int,
    body: CurriculumReuseIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Carry an earlier batch's curriculum forward.

    Only from the same major AND department -- a CSE 2025 syllabus is last
    year's curriculum for CSE 2026, not for Robotics, however similar the
    office thinks they are.
    """
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such batch."},
        )
    src = db.get(Batch, body.from_batch_id)
    if src is None or src.major != batch.major or src.department_id != batch.department_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error",
                    "message": "Reuse needs an earlier batch of the same major and department."},
        )
    if not src.curriculum_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error",
                    "message": "That batch has no curriculum to reuse."},
        )

    batch.curriculum_name = src.curriculum_name
    batch.curriculum_path = src.curriculum_path
    batch.reused_from_batch_id = src.id
    db.flush()
    _audit(db, user, "batch.curriculum.reuse", f"batch:{batch.id}",
           {"from_batch_id": src.id, "file": src.curriculum_name})
    return _batch_out(batch)


# --- which subjects a batch takes (admin-010) --------------------------------

def _course_brief(c: Course) -> dict:
    """The subject as a batch view needs it.

    Deliberately not admin._course_out: that carries the prerequisite graph
    and the term window, which this list does not use and would pay for on
    every row.
    """
    return {
        "id": c.id,
        "code": c.code,
        "title": c.title,
        "department_id": c.department_id,
        "semester": c.semester,
        "batch_ids": [b.id for b in c.batches],
    }


@router.get("/batches/{batch_id}/courses")
def list_batch_courses(
    batch_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such batch."},
        )
    # Semester order, then code: that is the order a curriculum is read in,
    # and an unset semester sorts last rather than first.
    rows = sorted(batch.courses, key=lambda c: (c.semester is None, c.semester or 0, c.code))
    return {"items": [_course_brief(c) for c in rows]}


@router.post("/batches/{batch_id}/courses", status_code=status.HTTP_201_CREATED)
def add_batch_course(
    batch_id: int,
    body: BatchCourseIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Link an existing subject to this cohort, or create one and link it.

    Exactly one form: `course_id` OR (`code` + `title`). A new subject is
    created in the BATCH's department -- the admin picked the cohort, so
    asking them to repeat its department would be a question with one right
    answer.
    """
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such batch."},
        )

    if body.course_id is not None:
        course = db.get(Course, body.course_id)
        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "No such subject."},
            )
    else:
        code = (body.code or "").strip().upper()
        title = (body.title or "").strip()
        if not code or not title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "validation_error",
                        "message": "Send course_id, or code and title to create a subject."},
            )
        if db.scalar(select(Course).where(Course.code == code)) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "conflict",
                        "message": f"A subject with code {code} already exists."},
            )
        course = Course(
            code=code,
            title=title,
            department_id=batch.department_id,
            semester=body.semester,
        )
        db.add(course)
        db.flush()

    if any(b.id == batch.id for b in course.batches):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": "That subject is already in this batch."},
        )

    course.batches.append(batch)
    db.flush()
    _audit(db, user, "batch.course.add", f"batch:{batch.id}",
           {"course_id": course.id, "code": course.code})
    return _course_brief(course)


@router.delete(
    "/batches/{batch_id}/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_batch_course(
    batch_id: int,
    course_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> Response:
    """Unlink, never delete.

    The subject keeps its materials, its chunks and its whole misconception
    history, and any other cohort taking it is untouched. Deleting a course
    because one cohort stopped taking it would destroy citations students
    still hold.
    """
    batch = db.get(Batch, batch_id)
    course = db.get(Course, course_id)
    if batch is None or course is None or not any(b.id == batch_id for b in course.batches):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found",
                    "message": "That subject is not in this batch."},
        )
    course.batches = [b for b in course.batches if b.id != batch_id]
    db.flush()
    _audit(db, user, "batch.course.remove", f"batch:{batch_id}",
           {"course_id": course_id, "code": course.code})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- teachers per subject ----------------------------------------------------

def _teacher_out(ct: CourseTeacher) -> dict:
    u = ct.user
    return {
        "user_id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "assigned_at": ct.assigned_at.isoformat().replace("+00:00", "Z")
        if ct.assigned_at
        else None,
    }


@router.get("/courses/{course_id}/teachers")
def list_course_teachers(
    course_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    if db.get(Course, course_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such course."},
        )
    rows = db.scalars(
        select(CourseTeacher)
        .where(CourseTeacher.course_id == course_id)
        .order_by(CourseTeacher.id)
    ).all()
    return {"items": [_teacher_out(ct) for ct in rows]}


@router.post("/courses/{course_id}/teachers", status_code=status.HTTP_201_CREATED)
def add_course_teacher(
    course_id: int,
    body: TeacherAddIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Assign a teacher to a subject by email, issuing an account if needed.

    The generated password is returned ONCE, in this response. It is not
    stored in any recoverable form -- hash_password is one-way -- so it must
    be shared with the teacher immediately. Teachers do not sign themselves
    up (auth-004); this route is the only way a teacher account is born.
    """
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such course."},
        )

    teacher = db.scalar(select(User).where(User.email == body.email))
    password: str | None = None
    if teacher is None:
        password = secrets.token_urlsafe(9)
        teacher = User(
            email=body.email,
            password_hash=hash_password(password),
            full_name=body.full_name or body.email.split("@")[0].title(),
            role="teacher",
            preferred_language="en",
        )
        db.add(teacher)
        db.flush()
    elif teacher.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": f"That email belongs to a {teacher.role} account."},
        )

    existing = db.scalar(
        select(CourseTeacher).where(
            CourseTeacher.course_id == course_id,
            CourseTeacher.user_id == teacher.id,
        )
    )
    if existing is not None:
        return {"teacher": _teacher_out(existing), "password": None,
                "already_assigned": True}

    ct = CourseTeacher(course_id=course_id, user_id=teacher.id, assigned_by_id=user.id)
    db.add(ct)
    db.flush()
    _audit(db, user, "course.teacher.add", f"course:{course_id}",
           {"email": teacher.email, "issued_password": password is not None})
    return {"teacher": _teacher_out(ct), "password": password,
            "already_assigned": False}


@router.delete(
    "/courses/{course_id}/teachers/{teacher_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_course_teacher(
    course_id: int,
    teacher_user_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> Response:
    ct = db.scalar(
        select(CourseTeacher).where(
            CourseTeacher.course_id == course_id,
            CourseTeacher.user_id == teacher_user_id,
        )
    )
    if ct is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found",
                    "message": "That teacher is not assigned to this course."},
        )
    db.delete(ct)
    db.flush()
    _audit(db, user, "course.teacher.remove", f"course:{course_id}",
           {"user_id": teacher_user_id})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- dashboard overview --------------------------------------------------------

@router.get("/overview")
def overview(
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """The admin dashboard's metrics tile (admin-009).

    Every number is a live count: an admin opening the dashboard is asking
    "what is the state of the institution right now", and a stale answer to
    that question is worse than a slow one.
    """
    batches = int(db.scalar(select(func.count()).select_from(Batch)) or 0)
    departments = int(db.scalar(select(func.count()).select_from(Department)) or 0)
    materials = int(db.scalar(select(func.count()).select_from(Material)) or 0)
    courses = int(db.scalar(select(func.count()).select_from(Course)) or 0)
    teachers_assigned = int(
        db.scalar(select(func.count()).select_from(CourseTeacher)) or 0
    )
    teacher_accounts = int(
        db.scalar(
            select(func.count()).select_from(User).where(User.role == "teacher")
        ) or 0
    )
    courses_without_teachers = int(
        db.scalar(
            select(func.count())
            .select_from(Course)
            .where(
                ~Course.id.in_(
                    select(CourseTeacher.course_id).distinct()
                )
            )
        ) or 0
    )
    courses_without_batch = int(
        db.scalar(
            select(func.count())
            .select_from(Course)
            .where(~Course.id.in_(select(batch_courses.c.course_id).distinct()))
        ) or 0
    )
    by_status = db.execute(
        select(Material.ingest_status, func.count()).group_by(Material.ingest_status)
    ).all()
    return {
        "batches": batches,
        "departments": departments,
        "materials": materials,
        "courses": courses,
        "teachers_assigned": teachers_assigned,
        "teacher_accounts": teacher_accounts,
        "courses_without_teachers": courses_without_teachers,
        "courses_without_batch": courses_without_batch,
        "ingest_summary": {s: n for s, n in by_status},
    }
