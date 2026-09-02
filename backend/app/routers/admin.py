"""Admin routes -- admin-001, admin-002, admin-003.

The provenance half of the system. Everything a student is ever told comes out
of a `Material` somebody uploaded, and these routes are where that somebody is
recorded. The claim "curriculum-aligned" is only checkable if you can get from
an answer, through its citation, to a file and the person who put it there.

Three rules:

* **Admin only.** `teacher_only` admits teachers; nothing here does. Uploading
  course material and rewriting the prerequisite graph are institutional acts.

* **Archiving, not deletion, is how material leaves the corpus.** A replaced
  textbook stays as a row with `status: "archived"`. Chunks already cite it by
  page, and deleting the material would leave a student looking at a citation
  to a book that no longer exists. Archiving keeps history readable and takes
  the material out of retrieval, which is what `retrieval.search` already
  filters on.

  `admin-006` added a bounded exception, not a reversal: `DELETE
  /admin/materials/{id}` exists for material uploaded by mistake, and refuses
  whenever the material is already in the corpus and its course is mid-term.
  If you are choosing between the two, you want `archive`.

* **Every mutation writes an audit row.** Not for tidiness -- `admin-003` is
  the only place a human can see who approved what, and `teacher-005` reads
  the reteach approval time out of the same table.

Upload by a verified admin **counts as approval** for this build. There is no
separate approval step for admin-uploaded material, per the feature plan.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..config import REPO_ROOT
from ..db import get_db
from ..deps import admin_only
from ..services import ingest
from ..models import AuditLog, Batch, Chunk, Course, Department, Material, ReteachUnit, User
from ..schemas import CourseIn, CourseTermIn, DepartmentIn
# The one place the verb is spelled. auth.py writes the row, this file reads
# it; two literals in two files is how a filter silently stops matching.
from .auth import FIRST_LOGIN_ACTION

router = APIRouter(prefix="/admin", tags=["admin"])

MATERIAL_KINDS = ("syllabus", "textbook", "notes", "assignment", "reference")

# Big enough for a real textbook. `Django 5 By Example` is 1190 pages and about
# 20 MB, and a cap that rejects the corpus we actually run on would be a cap
# chosen without looking.
MAX_MATERIAL_BYTES = 80 * 1024 * 1024

UPLOAD_DIR = REPO_ROOT / "backend" / "data" / "pdfs"


def _audit(db: OrmSession, user: User, action: str, target: str, detail: dict):
    db.add(AuditLog(actor_id=user.id, action=action, target=target, detail=detail))


# ---------------------------------------------------------------------------
# admin-002 -- departments, courses, prerequisites
# ---------------------------------------------------------------------------

def _course_out(course: Course) -> dict:
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "department_id": course.department_id,
        # The reason this feature exists. Gap detection names the prior course
        # a student should have learned something in, and it reads it from
        # here -- get this wrong and every gap is attributed to the wrong
        # place, which is worse than not attributing it at all.
        "prerequisite_courses": [
            {"id": p.id, "code": p.code, "title": p.title}
            for p in course.prerequisites
        ],
        # admin-005. Nulls and an empty list for a course that predates these,
        # never an inferred value -- "we do not know when this term runs" and
        # "this term runs all year" must not look the same to admin-006.
        "semester": course.semester,
        "admission_batches": list(course.admission_batches or []),
        # admin-010. The real cohort link, as opposed to admission_batches
        # above, which is a free list of admission YEARS.
        "batch_ids": [b.id for b in course.batches],
        "term_start": course.term_start.isoformat() if course.term_start else None,
        "term_end": course.term_end.isoformat() if course.term_end else None,
    }


@router.get("/departments")
def list_departments(
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    rows = db.scalars(select(Department).order_by(Department.name)).all()
    return {"items": [{"id": d.id, "name": d.name} for d in rows]}


@router.post("/departments", status_code=status.HTTP_201_CREATED)
def create_department(
    body: DepartmentIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    existing = db.scalar(select(Department).where(Department.name == body.name))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": "A department with that name already exists.",
                    "detail": {"id": existing.id}},
        )
    row = Department(name=body.name)
    db.add(row)
    db.flush()
    _audit(db, user, "department.create", f"department:{row.id}", {"name": row.name})
    db.flush()
    return {"id": row.id, "name": row.name}


@router.get("/courses")
def list_courses(
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    rows = db.scalars(select(Course).order_by(Course.code)).all()
    return {"items": [_course_out(c) for c in rows]}


@router.get("/courses/{course_id}")
def get_course(
    course_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such course."},
        )
    return _course_out(course)


@router.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(
    body: CourseIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    if db.scalar(select(Course).where(Course.code == body.code)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": f"Course {body.code} already exists."},
        )
    if body.department_id is not None and db.get(Department, body.department_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": "No such department."},
        )

    # admin-010: an optional cohort to file the new subject under. Resolved
    # before the insert so a bad id fails loudly rather than leaving an
    # unlinked course behind.
    batch = None
    if body.batch_id is not None:
        batch = db.get(Batch, body.batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "bad_request", "message": "No such batch."},
            )

    course = Course(code=body.code, title=body.title,
                    department_id=body.department_id)
    if batch is not None:
        course.batches.append(batch)
    db.add(course)
    db.flush()

    # Resolved before assigning, not after. A prerequisite id that does not
    # exist has to fail here; silently dropping it would produce a course whose
    # gap attribution is quietly wrong, and nothing downstream can tell the
    # difference between "no prerequisite" and "a prerequisite we lost".
    for pid in dict.fromkeys(body.prerequisite_course_ids):
        if pid == course.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "bad_request",
                        "message": "A course cannot be its own prerequisite."},
            )
        prerequisite = db.get(Course, pid)
        if prerequisite is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "bad_request",
                        "message": f"No course with id {pid} to use as a prerequisite."},
            )
        course.prerequisites.append(prerequisite)

    db.flush()
    _audit(db, user, "course.create", f"course:{course.id}",
           {"code": course.code,
            "prerequisites": [p.code for p in course.prerequisites]})
    db.flush()
    return _course_out(course)


@router.put("/courses/{course_id}/term")
def set_course_term(
    course_id: int,
    body: CourseTermIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """admin-005 -- when this course runs, and which cohorts take it.

    A partial update: only the keys actually sent are touched, so setting the
    semester cannot silently wipe the term dates. `null` clears a field,
    omitting it leaves it alone -- without that distinction a date entered
    wrongly could never be unset.

    The dates are not decoration. `admin-006` refuses to delete already-ingested
    material while a course is mid-term, and this is the window it reads.
    """
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such course."},
        )

    sent = body.model_fields_set
    changed: dict = {}

    # Validate the MERGED window, not just the request. The schema can only
    # compare two dates that arrived together; sending one that contradicts a
    # stored one would otherwise write a window in which in_term() is false for
    # every date, quietly disabling admin-006's guard.
    new_start = body.term_start if "term_start" in sent else course.term_start
    new_end = body.term_end if "term_end" in sent else course.term_end
    if new_start is not None and new_end is not None and new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "validation_error",
                "message": "Some fields are invalid.",
                "detail": {
                    "term_end": f"cannot be earlier than term_start ({new_start})"
                },
            },
        )

    for field in ("semester", "admission_batches", "term_start", "term_end"):
        if field not in sent:
            continue
        value = getattr(body, field)
        if field == "admission_batches" and value is not None:
            value = list(value)
        setattr(course, field, value)
        changed[field] = value.isoformat() if hasattr(value, "isoformat") else value

    db.flush()
    _audit(db, user, "course.set_term", f"course:{course.id}",
           {"code": course.code, **changed})
    db.flush()
    return _course_out(course)


# ---------------------------------------------------------------------------
# admin-001 -- curriculum upload and versioning
# ---------------------------------------------------------------------------

def _material_out(db: OrmSession, m: Material) -> dict:
    uploader = db.get(User, m.uploaded_by_id) if m.uploaded_by_id else None
    return {
        "id": m.id,
        "course_id": m.course_id,
        "title": m.title,
        "kind": m.kind,
        "version": m.version,
        "status": m.status,
        "page_count": m.page_count,
        # An email, not a name: the audit trail has to identify a person
        # uniquely, and two teachers can share a name. This is an admin-only
        # route, so it is not a leak of a student's identity.
        "uploaded_by": uploader.email if uploader else None,
        "uploaded_at": m.uploaded_at.isoformat().replace("+00:00", "Z")
        if m.uploaded_at else None,
        "ingest_status": m.ingest_status,
        "chunk_count": m.chunk_count,
    }


def _safe_name(name: str) -> str:
    """A filename derived from the title, not taken from the upload.

    The client-supplied filename reaches the filesystem otherwise, and
    `../../.env` is a filename. Normalising to ASCII and stripping everything
    that is not a word character removes the traversal, the separators and the
    Windows-reserved punctuation in one pass.
    """
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name).strip("-._")
    return (cleaned or "material")[:80]


@router.post("/courses/{course_id}/materials", status_code=status.HTTP_201_CREATED)
def upload_material(
    course_id: int,
    file: UploadFile = File(...),
    kind: str = Form(...),
    title: str = Form(...),
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Add material to a course, versioning any earlier copy of the same title.

    Uploading a replacement does not overwrite. The previous row is archived
    and keeps its chunks, because those chunks are what existing citations
    point at -- deleting them would turn a student's Show Source into a
    reference to a book that is not there any more. Archived material is
    excluded from retrieval by `materials.status`, so it stops being quoted
    without stopping being explicable.

    The file is written to disk and the row is created with
    `ingest_status: "pending"`. Embedding is NOT done here: it is minutes of
    CPU for a real textbook, and an HTTP request that takes minutes is a
    request that times out. `backend/scripts/ingest_pdfs.py` does the work.
    """
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such course."},
        )
    if kind not in MATERIAL_KINDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request",
                    "message": f"kind must be one of {', '.join(MATERIAL_KINDS)}.",
                    "detail": {"given": kind}},
        )
    title = title.strip()[:300]
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": "title is required."},
        )

    try:
        data = file.file.read(MAX_MATERIAL_BYTES + 1)
    finally:
        file.file.close()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request", "message": "That file is empty."},
        )
    if len(data) > MAX_MATERIAL_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_request",
                    "message": f"That file is larger than "
                               f"{MAX_MATERIAL_BYTES // (1024 * 1024)} MB."},
        )

    previous = db.scalars(
        select(Material)
        .where(Material.course_id == course_id, Material.title == title)
        .order_by(Material.version.desc())
    ).all()
    version = (previous[0].version + 1) if previous else 1
    for old in previous:
        old.status = "archived"

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # admin-007: one source of truth for what ingestion can take. This list
    # used to be its own hardcoded tuple, and it included .txt and .md that
    # ingest.to_pdf then refused -- so such an upload was stored, marked
    # pending, and silently never ingestable.
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ingest.supported_suffixes():
        suffix = ".pdf" if data[:5] == b"%PDF-" else ".bin"
    path = UPLOAD_DIR / f"{course.code}-{_safe_name(title)}-v{version}{suffix}"
    path.write_bytes(data)

    material = Material(
        course_id=course_id, title=title, kind=kind, version=version,
        status="active", page_count=0, source_path=str(path),
        uploaded_by_id=user.id, ingest_status="pending", chunk_count=0,
    )
    db.add(material)
    db.flush()

    _audit(db, user, "material.upload", f"material:{material.id}",
           {"title": title, "kind": kind, "version": version,
            "bytes": len(data),
            "archived": [m.id for m in previous]})
    db.flush()

    out = _material_out(db, material)
    out["archived_versions"] = [m.id for m in previous]
    out["note"] = (
        "Stored and marked pending. Run backend/scripts/ingest_pdfs.py to "
        "parse, chunk and embed it -- embedding a textbook takes minutes and "
        "does not belong in an HTTP request."
    )
    return out


@router.get("/courses/{course_id}/materials")
def list_materials(
    course_id: int,
    include_archived: bool = False,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    if db.get(Course, course_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such course."},
        )
    stmt = select(Material).where(Material.course_id == course_id)
    if not include_archived:
        stmt = stmt.where(Material.status == "active")
    rows = db.scalars(stmt.order_by(Material.title, Material.version.desc())).all()
    return {"items": [_material_out(db, m) for m in rows]}


@router.get("/materials/{material_id}")
def get_material(
    material_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    material = db.get(Material, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such material."},
        )
    return _material_out(db, material)


@router.get("/materials/{material_id}/versions")
def material_versions(
    material_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Every version of this title in this course, newest first.

    Version history is derived from (course, title) rather than from a chain of
    ids. A `replaces_id` column would be one more thing to keep truthful, and
    it would disagree with reality the first time somebody uploaded a
    replacement without setting it.
    """
    material = db.get(Material, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such material."},
        )
    rows = db.scalars(
        select(Material)
        .where(Material.course_id == material.course_id,
               Material.title == material.title)
        .order_by(Material.version.desc())
    ).all()
    return {"items": [_material_out(db, m) for m in rows]}


@router.post("/materials/{material_id}/archive")
def archive_material(
    material_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Take material out of retrieval without destroying what cites it.

    Archiving is not a soft delete standing in for a real one. `retrieval`
    filters on `status == "active"`, so an archived book stops being quoted
    immediately, while its chunks stay addressable for any citation already
    shown to a student.
    """
    material = db.get(Material, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such material."},
        )
    if material.status != "archived":
        material.status = "archived"
        _audit(db, user, "material.archive", f"material:{material.id}",
               {"title": material.title, "version": material.version})
        db.flush()
    return _material_out(db, material)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> Response:
    """admin-006 -- remove material uploaded by mistake.

    **Archiving is still the normal path.** This module's rule -- nothing is
    deleted, only archived -- is not dropped here, it is bounded. The rule
    exists because a citation must always resolve, and the escape hatch is for
    material that was never part of the corpus, or whose course is not currently
    being taught.

    One guard, and it is the term window:

    * never ingested (no chunks) -- always deletable. An upload mistake should
      be fixable the day it happens.
    * ingested, and the course is mid-term -- refused. Deleting a book out from
      under a class in week six is the thing archiving was invented to prevent.
    * ingested, outside the term (or the course has no dates) -- deletable.

    There is deliberately **no** "refuse if it is cited" check. Nothing in the
    schema persists a `chunk_id` -- a Citation is built from live retrieval at
    request time and never written down -- so such a check could only ever be a
    guess dressed as a guarantee. The term window is the honest guard.

    The source file on disk is left alone: deleting a row must not throw away
    the only copy of a book.
    """
    material = db.get(Material, material_id)
    if material is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such material."},
        )

    chunk_count = int(db.scalar(
        select(func.count()).select_from(Chunk).where(Chunk.material_id == material.id)
    ) or 0)

    course = db.get(Course, material.course_id)
    if chunk_count and course is not None and course.in_term(date.today()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "mid_term",
                "message": (
                    f"{course.title} is mid-term until {course.term_end}. "
                    "Material already in the corpus can only be deleted between "
                    "terms — archive it instead."
                ),
                "detail": {
                    "course": course.code,
                    "term_start": course.term_start.isoformat(),
                    "term_end": course.term_end.isoformat(),
                    "chunk_count": chunk_count,
                },
            },
        )

    # Written BEFORE the delete and keyed by string, not by foreign key, so the
    # trail outlives what it describes. An audit row that vanished with its
    # subject would make deletion the one act nobody could review.
    _audit(db, user, "material.delete", f"material:{material.id}",
           {"title": material.title, "kind": material.kind,
            "version": material.version, "chunk_count": chunk_count,
            "course": course.code if course else None,
            "source_path_left_on_disk": material.source_path})

    db.delete(material)      # chunks cascade -- Material.chunks is delete-orphan
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# admin-003 -- the audit log
# ---------------------------------------------------------------------------

# Written by seed.py, which is a developer script. It is not curriculum
# governance, and on a rehearsal day it outnumbered every real row put together
# -- an admin looking for "who changed the syllabus" scrolled past twenty
# re-seeds first. Hidden by default, never deleted.
SYSTEM_ACTIONS = ("seed.run",)

# Present tense reads wrong in a log; these are all things that already happened.
_ACTION_PHRASE = {
    "material.upload": "uploaded",
    "material.archive": "archived",
    "material.ingest": "ingested",
    "course.create": "created the course",
    "course.set_term": "set the term details for",
    "material.delete": "deleted",
    "department.create": "created the department",
    "reteach.suggest": "drafted a reteach unit for",
    "reteach.edit": "edited the reteach unit",
    "reteach.approve": "approved and assigned the reteach unit",
    "sourced_content.approve": "approved the web source",
    "sourced_content.reject": "rejected the web source",
    "seed.run": "re-seeded",
}


def _audit_titles(db: OrmSession, rows) -> dict[str, str]:
    """Resolve `material:12` / `reteach:39` to the titles they name.

    Batched by kind -- two queries for the whole page, not one per row. See
    perf-001: a per-row lookup is a network round trip.
    """
    wanted: dict[str, set[int]] = {}
    for r in rows:
        kind, _, ident = (r.target or "").partition(":")
        if ident.isdigit():
            wanted.setdefault(kind, set()).add(int(ident))

    titles: dict[str, str] = {}
    if wanted.get("material"):
        for m in db.scalars(
            select(Material).where(Material.id.in_(wanted["material"]))
        ).all():
            titles[f"material:{m.id}"] = m.title
    if wanted.get("reteach"):
        for u in db.scalars(
            select(ReteachUnit).where(ReteachUnit.id.in_(wanted["reteach"]))
        ).all():
            titles[f"reteach:{u.id}"] = u.title
    return titles


def _audit_summary(row, actor_email: str | None, titles: dict[str, str]) -> str:
    """One readable sentence. Never raises, never returns empty.

    A verb with no phrase here still has to render: a new action appearing as a
    blank row would look like corrupted data rather than like an unmapped verb.
    """
    who = actor_email or "system"
    phrase = _ACTION_PHRASE.get(row.action)
    target = row.target or ""
    name = titles.get(target)

    detail = row.detail if isinstance(row.detail, dict) else {}

    if row.action == FIRST_LOGIN_ACTION:
        # "signed in" takes no object, and the actor IS the subject. Running
        # this through the generic path below produces "priya@x.edu signed in
        # for the first time “Priya Sharma” (since removed)", which reads as
        # a bug rather than as a sentence.
        codes = [str(c) for c in (detail.get("courses") or [])]
        where = f" (assigned to {', '.join(codes)})" if codes else ""
        return f"{detail.get('name') or who} signed in for the first time{where}"

    if name:
        what = f"“{name}”"
    elif target.startswith("course:"):
        # Prefer the code the row recorded: "course DLD" is what an admin
        # recognises, "course 9" is an internal id they have to go look up.
        what = f"course {detail.get('code') or target.split(':', 1)[1]}"
    elif (detail.get("title") or detail.get("concept")
          or detail.get("misconception") or detail.get("name")):
        # The row outlives what it points at -- a reteach unit can be pruned,
        # and printing the raw `reteach:32` back is the exact technical noise
        # this field exists to remove. The detail dict still names the subject.
        subject = (detail.get("title") or detail.get("concept")
                   or detail.get("misconception") or detail["name"])
        what = f"“{str(subject).replace('-', ' ')}”"
        # ...but not on a deletion. "deleted X (since removed)" states the
        # obvious twice; the row IS the record that X is gone.
        if not row.action.endswith(".delete"):
            what += " (since removed)"
    elif target:
        what = "something that has since been removed"
    else:
        what = ""

    extras = []
    if "version" in detail:
        extras.append(f"version {detail['version']}")
    if detail.get("reason"):
        extras.append(f"reason: {detail['reason']}")
    tail = f" ({', '.join(extras)})" if extras else ""

    if phrase is None:
        # Unmapped verb. Still a sentence, and it names the raw action so an
        # admin can search for it.
        return f"{who} performed {row.action}{(' on ' + what) if what else ''}{tail}"
    return f"{who} {phrase} {what}".strip() + tail


@router.get("/audit-log")
def audit_log(
    limit: int = 50,
    offset: int = 0,
    actor: str | None = None,
    action: str | None = None,
    include_system: bool = False,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Who did what, and when.

    The human-in-the-loop trail. Every approval in this system -- a reteach
    unit assigned to a class, a web source let into the corpus, a textbook
    uploaded -- is an act by a named person, and this is where that is
    legible. It is also load-bearing rather than decorative: `teacher-005`
    reads the reteach approval time from these rows, because `reteach_units`
    has no `approved_at` column.

    `actor` filters on email substring, which is the identifier an admin
    actually has to hand.
    """
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    elif not include_system:
        # Only when no explicit action was asked for: `?action=seed.run` must
        # still return seed rows, or the filter would silently lie.
        stmt = stmt.where(AuditLog.action.notin_(SYSTEM_ACTIONS))
    if actor:
        stmt = stmt.join(User, User.id == AuditLog.actor_id).where(
            User.email.ilike(f"%{actor.strip().lower()}%")
        )

    total = int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = db.scalars(
        stmt.order_by(AuditLog.at.desc(), AuditLog.id.desc())
        .limit(max(1, min(limit, 200)))
        .offset(max(0, offset))
    ).all()

    actors = {
        u.id: u.email
        for u in db.scalars(
            select(User).where(User.id.in_([r.actor_id for r in rows if r.actor_id]
                                           or [-1]))
        ).all()
    }

    titles = _audit_titles(db, rows)

    return {
        "items": [
            {
                "id": r.id,
                "actor_email": actors.get(r.actor_id),
                # The machine fields stay exactly as they were: `?action=`
                # filters on these verbs and the contract is what an admin
                # types them from. `summary` is added, not a replacement.
                "action": r.action,
                "target": r.target,
                "at": r.at.isoformat().replace("+00:00", "Z") if r.at else None,
                "detail": r.detail,
                "summary": _audit_summary(r, actors.get(r.actor_id), titles),
            }
            for r in rows
        ],
        "total": total,
    }


# ---------------------------------------------------------------------------
# admin-011 -- the notification bell
# ---------------------------------------------------------------------------

# There is no notifications table, and there should not be one. Every event
# worth a notification here is already an audit row written by the act itself,
# so a second store would be a copy that can disagree with the original -- and
# the one it would disagree with is the one an admin trusts. This endpoint is a
# read over `audit_log` with two derived fields on top.
#
# The two sources, both audit rows:
#   * governance changes -- uploads, deletions, course and cohort edits,
#     teacher assignment, reteach approvals; and
#   * `teacher.first_login`, written once per teacher by auth.py, which is how
#     an admin learns the password they generated and handed over worked.

MAX_NOTIFICATIONS = 100


def _notifications_base():
    """Rows eligible to be a notification.

    `seed.run` is excluded for the same reason `admin-004` hides it from the
    audit log -- it is a developer script's output -- and there is deliberately
    no `?include_system=` here: a notification about a re-seed is not a
    notification. The audit log remains the place to see everything.
    """
    return select(AuditLog).where(AuditLog.action.notin_(SYSTEM_ACTIONS))


@router.get("/notifications")
def notifications(
    limit: int = 20,
    offset: int = 0,
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """What the admin has not seen yet, newest first.

    Every field but `kind`, `unread` and `by_you` is the audit row unchanged,
    `summary` included -- a client that already renders the audit log renders
    this with no second formatter.

    **`unread` deliberately does not count the admin's own actions.** An admin
    who uploads a textbook does not need to be told they uploaded a textbook,
    and counting it leaves the badge permanently lit, which is a badge that
    means nothing. The row is still listed -- it is history -- it just does not
    ring. The count is over the whole table, not over this page: a bell that
    says "3" because you asked for 3 rows is lying.
    """
    limit = max(1, min(limit, MAX_NOTIFICATIONS))
    offset = max(0, offset)

    seen_at = user.notifications_seen_at

    total = int(db.scalar(
        select(func.count()).select_from(_notifications_base().subquery())
    ) or 0)

    # `is_distinct_from` rather than `!=`: a row with a null actor (a system
    # write with nobody attached) is not "mine", and `actor_id != 3` is NULL --
    # therefore false -- for exactly those rows, which would silently drop them
    # from the count.
    unread_stmt = (
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action.notin_(SYSTEM_ACTIONS),
               AuditLog.actor_id.is_distinct_from(user.id))
    )
    if seen_at is not None:
        unread_stmt = unread_stmt.where(AuditLog.at > seen_at)
    unread_count = int(db.scalar(unread_stmt) or 0)

    rows = db.scalars(
        _notifications_base()
        .order_by(AuditLog.at.desc(), AuditLog.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    actors = {
        u.id: u.email
        for u in db.scalars(
            select(User).where(User.id.in_([r.actor_id for r in rows if r.actor_id]
                                           or [-1]))
        ).all()
    }
    titles = _audit_titles(db, rows)

    def _is_unread(r) -> bool:
        if r.actor_id == user.id:
            return False
        if seen_at is None:
            return True
        return bool(r.at and r.at > seen_at)

    return {
        "items": [
            {
                "id": r.id,
                # Switch icons on this, not on string-matching `summary`.
                "kind": ("teacher_first_login"
                         if r.action == FIRST_LOGIN_ACTION else "audit"),
                "actor_email": actors.get(r.actor_id),
                "action": r.action,
                "target": r.target,
                "at": r.at.isoformat().replace("+00:00", "Z") if r.at else None,
                "detail": r.detail,
                "summary": _audit_summary(r, actors.get(r.actor_id), titles),
                "unread": _is_unread(r),
                "by_you": r.actor_id == user.id,
            }
            for r in rows
        ],
        "unread": unread_count,
        "seen_at": (seen_at.isoformat().replace("+00:00", "Z")
                    if seen_at else None),
        "total": total,
    }


@router.post("/notifications/read")
def notifications_read(
    db: OrmSession = Depends(get_db),
    user: User = Depends(admin_only),
) -> dict:
    """Dismiss the bell: everything up to now counts as seen.

    The marker is read from the DATABASE clock, not this process's clock. Every
    `audit_log.at` is a `server_default=func.now()` stamp, so a marker taken
    from a laptop running a few seconds fast would mark rows read that had not
    been written yet -- and they would never ring. One extra round trip, on an
    action that happens when a human clicks a bell.
    """
    now = db.scalar(select(func.now()))
    user.notifications_seen_at = now
    db.flush()
    return {
        "seen_at": now.isoformat().replace("+00:00", "Z") if now else None,
        "unread": 0,
    }
