"""Teacher routes -- teacher-001 and teacher-004.

Two rules, and they are the same rule twice:

* **Every response here is anonymised.** No student id, no name, no email, in
  any field. Not "not rendered by the frontend" -- not present in the payload.
  The heatmap joins through attempts to reach a diagnosis and deliberately
  drops the student on the way; `uncertainty_flags` never had a `user_id`
  column to drop.

* **Only confirmed diagnoses count.** `confirmed` is three-state: `None` means
  the student was asked and has not answered, `False` means they disagreed.
  Only `True` is aggregated. That is what makes the number on a teacher's
  screen mean "students who agreed this was their reasoning" rather than "times
  the algorithm guessed".

Denied diagnoses are kept, not deleted. Throwing them away would make the
system look more accurate than it is.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from ..db import get_db
from ..deps import teacher_only
from ..models import (
    Attempt,
    AuditLog,
    Concept,
    Course,
    Gap,
    Misconception,
    MisconceptionDiagnosis,
    PracticeItem,
    ReteachUnit,
    SourcedContent,
    Topic,
    UncertaintyFlag,
    User,
    CourseTeacher,
)
from ..providers import AllProvidersFailed
from ..services import reteach
from ..schemas import (
    PatchReteachIn,
    RejectSourcedIn,
    ResolveFlagIn,
    SuggestReteachIn,
    ActiveSubjectIn,
    UserOut,
)

router = APIRouter(prefix="/teacher", tags=["teacher"])


def _class_size(db: OrmSession, course_id: int | None) -> int:
    stmt = select(func.count()).select_from(User).where(User.role == "student")
    if course_id is not None:
        stmt = stmt.where(User.course_id == course_id)
    return int(db.scalar(stmt) or 0)


# ---------------------------------------------------------------------------
# teacher-001 -- the misconception heatmap
# ---------------------------------------------------------------------------

@router.get("/misconceptions/heatmap")
def heatmap(
    course_id: int | None = None,
    topic_id: int | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """The class's most common confirmed wrong mental models, ranked.

    Polled by the frontend on an interval -- there are no websockets anywhere
    in this build. It is a plain aggregate query, so "live" costs nothing: a
    student confirming a diagnosis on another laptop changes the number on the
    next poll.
    """
    course_id = course_id if course_id is not None else user.course_id

    counts = (
        select(
            MisconceptionDiagnosis.misconception_id.label("misconception_id"),
            func.count().label("confirmed_count"),
            func.max(MisconceptionDiagnosis.at).label("latest"),
        )
        .join(Attempt, Attempt.id == MisconceptionDiagnosis.attempt_id)
        .join(PracticeItem, PracticeItem.id == Attempt.practice_item_id)
        .where(MisconceptionDiagnosis.confirmed.is_(True))
        .group_by(MisconceptionDiagnosis.misconception_id)
    )
    # The join above passes through `attempts`, which is the only place a
    # student id exists in this query -- and it is grouped away rather than
    # selected. There is no field here for a name to appear in.

    counts = counts.subquery()

    stmt = (
        select(Misconception, counts.c.confirmed_count, counts.c.latest)
        .join(counts, counts.c.misconception_id == Misconception.id)
        .order_by(counts.c.confirmed_count.desc(), Misconception.id)
    )

    # Scoped to the course, the same way retrieval is. Several courses'
    # misconceptions share this table, and an unscoped heatmap shows a physics
    # teacher the Django class's numbers -- which does not look like a bug, it
    # looks like a surprising result. A misconception with no topic is excluded
    # here, because there is nothing to scope it by.
    if course_id is not None:
        stmt = stmt.join(Topic, Topic.id == Misconception.topic_id).where(
            Topic.course_id == course_id
        )
    if topic_id is not None:
        stmt = stmt.where(Misconception.topic_id == topic_id)

    rows = db.execute(stmt).all()
    size = _class_size(db, course_id)

    topic_name = None
    if topic_id is not None:
        topic = db.get(Topic, topic_id)
        topic_name = topic.name if topic else None

    latest = max((r[2] for r in rows if r[2] is not None), default=None)

    return {
        "topic": topic_name,
        "class_size": size,
        "updated_at": latest.isoformat().replace("+00:00", "Z") if latest else None,
        "items": [
            {
                "misconception_id": m.id,
                "label": m.label,
                "confirmed_count": int(count),
                # Share of the class, not of the diagnoses: "11 of 40 students"
                # is what a teacher acts on.
                "share": round(int(count) / size, 4) if size else 0.0,
                "problem_type": m.problem_type,
            }
            for m, count, _ in rows
        ],
    }


# ---------------------------------------------------------------------------
# teacher-004 -- uncertainty flags
# ---------------------------------------------------------------------------

@router.get("/uncertainty-flags")
def uncertainty_flags(
    # The wire name is `status`, as documented. The local name cannot be, because
    # `status` here is fastapi.status. Naming the parameter `status_filter`
    # without an alias meant a frontend following the contract sent `?status=`
    # and was silently ignored -- and since the default is already "open", the
    # only visible symptom was that `?status=all` did nothing.
    status_filter: str = Query("open", alias="status"),
    limit: int = 50,
    offset: int = 0,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """What the tutor refused to answer, for a human to look at.

    This panel is populated entirely by rag-003 and by gap lessons that could
    not be taught. Nothing writes to it on the teacher's behalf -- one feature,
    two dashboards.

    `alignment_percent` is derived here rather than stored, so it can never
    disagree with the score the student was shown.
    """
    stmt = select(UncertaintyFlag)
    if status_filter and status_filter != "all":
        stmt = stmt.where(UncertaintyFlag.status == status_filter)

    total = int(db.scalar(
        select(func.count()).select_from(stmt.subquery())
    ) or 0)

    rows = db.scalars(
        stmt.order_by(UncertaintyFlag.occurred_at.desc())
        .limit(max(1, min(limit, 200)))
        .offset(max(0, offset))
    ).all()

    return {
        "items": [
            {
                "id": f.id,
                "question": f.question,
                "alignment_percent": round((f.alignment_score or 0.0) * 100),
                "reason": f.reason,
                "topic_id": f.topic_id,
                "occurred_at": f.occurred_at.isoformat().replace("+00:00", "Z")
                if f.occurred_at else None,
                "status": f.status,
                # No student id, because the row never had one. See
                # models.UncertaintyFlag -- you cannot leak what you never
                # stored.
            }
            for f in rows
        ],
        "total": total,
    }


@router.post("/uncertainty-flags/{flag_id}/resolve",
             status_code=status.HTTP_204_NO_CONTENT)
def resolve_flag(
    flag_id: int,
    body: ResolveFlagIn | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> Response:
    """Mark a flag dealt with. The note is accepted and deliberately not
    stored -- there is no column for it, and inventing one to hold free text
    nobody reads is not worth a migration during a hackathon."""
    flag = db.get(UncertaintyFlag, flag_id)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such flag."},
        )
    flag.status = "resolved"
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# teacher-003 -- the prerequisite gap map
# ---------------------------------------------------------------------------

@router.get("/gap-map")
def gap_map(
    course_id: int | None = None,
    topic_id: int | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """Which prerequisites this class arrived without, and how many are missing
    each one.

    The companion to the heatmap. The heatmap says what students get *wrong
    now*; this says what they never learned in the first place, and names the
    earlier course it should have come from -- which is the difference between
    "reteach this" and "the prior course has a problem".

    Counted per student, not per gap row: `gaps` is unique on
    (user_id, concept_id), so a re-taken diagnostic re-opens a row rather than
    adding one, and a student cannot be counted twice.

    Closed gaps are excluded. A gap that has been closed is no longer missing,
    and leaving it in would make a class look permanently broken no matter how
    much of it got fixed.
    """
    counts = (
        select(
            Gap.concept_id.label("concept_id"),
            func.count(func.distinct(Gap.user_id)).label("students_missing"),
        )
        .where(Gap.status != "closed")
        .group_by(Gap.concept_id)
        .subquery()
    )

    stmt = (
        select(Concept, counts.c.students_missing, Topic, Course)
        .join(counts, counts.c.concept_id == Concept.id)
        .join(Topic, Topic.id == Concept.topic_id)
        .outerjoin(Course, Course.id == Concept.prerequisite_course_id)
        .order_by(counts.c.students_missing.desc(), Concept.id)
    )
    if course_id is not None:
        stmt = stmt.where(Topic.course_id == course_id)
    if topic_id is not None:
        stmt = stmt.where(Concept.topic_id == topic_id)

    rows = db.execute(stmt).all()
    size = _class_size(db, course_id)

    topic_name = None
    if topic_id is not None:
        topic = db.get(Topic, topic_id)
        topic_name = topic.name if topic else None

    return {
        "topic": topic_name,
        "class_size": size,
        "items": [
            {
                "concept": concept.name,
                "concept_id": concept.id,
                "topic": topic.name,
                # Named, not just counted. "11 students never learned this, and
                # it was supposed to come from CSW1" is a different conversation
                # from "11 students are struggling".
                "prerequisite_course": prerequisite.title if prerequisite else None,
                "students_missing": int(missing),
                "share": round(int(missing) / size, 4) if size else 0.0,
            }
            for concept, missing, topic, prerequisite in rows
        ],
    }


# ---------------------------------------------------------------------------
# teacher-002 -- reasoning paths behind one kind of problem
# ---------------------------------------------------------------------------

@router.get("/problems/{problem_type}/reasoning-paths")
def reasoning_paths(
    problem_type: str,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """The distinct wrong routes students took through one kind of problem.

    A heatmap cell says "14 students got this wrong". This says *how* -- which
    is the only version a teacher can actually teach against, because two
    students with the same wrong answer for different reasons need different
    lessons.

    `example.given_answer` is a real answer a real student typed, taken from a
    confirmed diagnosis. It arrives here with the student stripped: the query
    walks Attempt to reach the answer text and selects nothing else from it.
    """
    counts = (
        select(
            MisconceptionDiagnosis.misconception_id.label("misconception_id"),
            func.count().label("confirmed_count"),
        )
        .where(MisconceptionDiagnosis.confirmed.is_(True))
        .group_by(MisconceptionDiagnosis.misconception_id)
        .subquery()
    )

    rows = db.execute(
        select(Misconception, counts.c.confirmed_count)
        .join(counts, counts.c.misconception_id == Misconception.id)
        .where(Misconception.problem_type == problem_type)
        .order_by(counts.c.confirmed_count.desc(), Misconception.id)
    ).all()

    items = []
    for misconception, count in rows:
        # One real answer, and only the answer column. Selecting the Attempt
        # row itself would put user_id in this function's scope, one careless
        # edit away from the response.
        given = db.scalar(
            select(Attempt.answer)
            .join(MisconceptionDiagnosis,
                  MisconceptionDiagnosis.attempt_id == Attempt.id)
            .where(MisconceptionDiagnosis.misconception_id == misconception.id,
                   MisconceptionDiagnosis.confirmed.is_(True))
            .order_by(Attempt.id.desc())
            .limit(1)
        )
        items.append({
            "misconception_id": misconception.id,
            "label": misconception.label,
            "confirmed_count": int(count),
            "example": {
                "given_answer": given,
                "reasoning": misconception.description,
            } if given is not None else None,
        })

    return {"problem_type": problem_type, "items": items}


# ---------------------------------------------------------------------------
# teacher-005 -- did the reteach work?
# ---------------------------------------------------------------------------

def _reteach_approved_at(db: OrmSession, misconception_id: int):
    """When a reteach unit for this misconception was approved.

    Read from the audit log rather than from a column on `reteach_units`.
    There is no `approved_at` field, adding one means a schema change, and a
    schema change here means `reset_db.py` -- which drops `chunks` and costs
    forty minutes of re-embedding. The audit row already records the moment and
    the actor, so the information exists; it just lives somewhere else.
    """
    return db.scalar(
        select(func.min(AuditLog.at)).where(
            AuditLog.action == "reteach.approve",
            AuditLog.target.in_([
                f"reteach:{r}" for r in db.scalars(
                    select(ReteachUnit.id).where(
                        ReteachUnit.misconception_id == misconception_id
                    )
                ).all()
            ] or ["reteach:-1"]),
        )
    )


@router.get("/misconceptions/{misconception_id}/before-after")
def before_after(
    misconception_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """Confirmed counts either side of the moment a reteach was approved.

    The one panel in this dashboard that can say the intervention did not work,
    which is the only reason the rest of it is worth trusting. `delta_share`
    is reported whatever its sign, and a reteach that made no difference shows
    a delta of zero rather than being quietly omitted.

    `after` is null until a reteach has actually been approved -- not zero. A
    zero would read as "we taught it and nobody improved", which is a claim
    about teaching that has not happened yet.
    """
    misconception = db.get(Misconception, misconception_id)
    if misconception is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such misconception."},
        )

    course_id = None
    if misconception.topic_id is not None:
        topic = db.get(Topic, misconception.topic_id)
        course_id = topic.course_id if topic else None
    size = _class_size(db, course_id)

    def count_between(start, end) -> int:
        stmt = (
            select(func.count(func.distinct(Attempt.user_id)))
            .select_from(MisconceptionDiagnosis)
            .join(Attempt, Attempt.id == MisconceptionDiagnosis.attempt_id)
            .where(MisconceptionDiagnosis.misconception_id == misconception_id,
                   MisconceptionDiagnosis.confirmed.is_(True))
        )
        if start is not None:
            stmt = stmt.where(Attempt.at >= start)
        if end is not None:
            stmt = stmt.where(Attempt.at < end)
        return int(db.scalar(stmt) or 0)

    def attempts_since(start) -> int:
        """How many attempts on this KIND of problem happened in the window.

        Without this the panel lies by arithmetic. A reteach approved ten
        seconds ago has a confirmed count of zero after it, which divides into
        a share of zero, which subtracts into a triumphant negative delta --
        "the intervention removed the misconception entirely" -- when what
        actually happened is that nobody has been asked yet. Zero evidence and
        zero occurrences are not the same measurement, and only this number
        tells them apart.
        """
        stmt = (
            select(func.count())
            .select_from(Attempt)
            .join(PracticeItem, PracticeItem.id == Attempt.practice_item_id)
            .where(PracticeItem.problem_type == misconception.problem_type)
        )
        if start is not None:
            stmt = stmt.where(Attempt.at >= start)
        return int(db.scalar(stmt) or 0)

    def window(count: int, label: str, tested: int | None = None) -> dict:
        out = {
            "window": label,
            "confirmed_count": count,
            "share": round(count / size, 4) if size else 0.0,
        }
        if tested is not None:
            out["attempts_in_window"] = tested
            out["measured"] = tested > 0
        return out

    reteach_at = _reteach_approved_at(db, misconception_id)
    if reteach_at is None:
        return {
            "misconception_id": misconception.id,
            "label": misconception.label,
            "before": window(count_between(None, None), "all time"),
            "after": None,
            "reteach_at": None,
            "delta_share": None,
        }

    stamp = reteach_at.isoformat().replace("+00:00", "Z")
    before = window(count_between(None, reteach_at), f"before {stamp}")
    tested = attempts_since(reteach_at)
    after = window(count_between(reteach_at, None), f"since {stamp}", tested=tested)
    return {
        "misconception_id": misconception.id,
        "label": misconception.label,
        "before": before,
        "after": after,
        "reteach_at": stamp,
        # Null until somebody has actually been asked since the reteach. A
        # number here before then would be a claim about teaching that has not
        # been tested, and it would always be flattering.
        "delta_share": (round(after["share"] - before["share"], 4)
                        if tested else None),
        "note": None if tested else (
            "Nobody has attempted this kind of problem since the reteach was "
            "approved, so there is nothing to compare yet."
        ),
    }


# ---------------------------------------------------------------------------
# teacher-007 -- the AI-sourced content verification queue
# ---------------------------------------------------------------------------

def _sourced_out(row: SourcedContent) -> dict:
    return {
        "id": row.id,
        "source_url": row.source_url,
        "title": row.title,
        "excerpt": row.excerpt,
        "found_for_gap": row.found_for_gap,
        "status": row.status,
        "reject_reason": row.reject_reason,
        "found_at": row.found_at.isoformat().replace("+00:00", "Z")
        if row.found_at else None,
    }


@router.get("/verification-queue")
def verification_queue(
    status_filter: str = Query("pending", alias="status"),
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """Material the AI found outside the approved corpus, awaiting a human.

    Seeded for this build -- there is no live web search, and the queue is the
    feature. The point being made is that nothing from outside the knowledge
    base reaches a student without a teacher saying yes, which is exactly the
    property that makes "curriculum-aligned" mean anything.

    A `pending` row is unreachable from every student endpoint. That is not
    enforced here by being careful; it is enforced by `sourced_content` having
    no relationship to any table a student route reads.
    """
    stmt = select(SourcedContent)
    if status_filter and status_filter != "all":
        stmt = stmt.where(SourcedContent.status == status_filter)
    rows = db.scalars(stmt.order_by(SourcedContent.found_at.desc(),
                                    SourcedContent.id.desc())).all()
    return {"items": [_sourced_out(r) for r in rows]}


def _decide_sourced(db: OrmSession, item_id: int, user: User,
                    new_status: str, reason: str | None) -> dict:
    row = db.get(SourcedContent, item_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such queue item."},
        )
    row.status = new_status
    row.reject_reason = reason
    # The action name is the VERB from docs/api-contract.md, not the resulting
    # status. Deriving it from new_status wrote "sourced_content.approved",
    # which reads fine and does not match the documented filter an admin would
    # type into /admin/audit-log?action=.
    verb = {"approved": "approve", "rejected": "reject"}[new_status]
    db.add(AuditLog(actor_id=user.id, action=f"sourced_content.{verb}",
                    target=f"sourced_content:{row.id}",
                    detail={"title": row.title, "reason": reason}))
    db.flush()
    return _sourced_out(row)


@router.post("/verification-queue/{item_id}/approve")
def approve_sourced(
    item_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    return _decide_sourced(db, item_id, user, "approved", None)


@router.post("/verification-queue/{item_id}/reject")
def reject_sourced(
    item_id: int,
    body: RejectSourcedIn | None = None,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """A rejection keeps its reason, unlike a resolved uncertainty flag.

    The difference is that this one has somewhere to put it: `sourced_content`
    already has a `reject_reason` column, so storing it costs nothing. The
    reason is also the more useful of the two -- "this blog is wrong about
    QuerySets" is a judgement worth keeping next to the thing it judges.
    """
    return _decide_sourced(db, item_id, user, "rejected",
                           (body.reason if body else None) or None)



# ---------------------------------------------------------------------------
# teacher-006 -- auto-suggested reteach, with a human gate
# ---------------------------------------------------------------------------

def _reteach_out(db: OrmSession, unit: ReteachUnit, *,
                 citations: list | None = None) -> dict:
    """`practice_items` are the seeded items that exercise this misconception.

    They are found through `problem_type` rather than stored on the unit,
    because that is the same route `practice.diagnose()` uses to decide which
    misconceptions a wrong answer could mean. A unit and the items that detect
    it stay in step by construction instead of by remembering to update both.
    """
    misconception = (
        db.get(Misconception, unit.misconception_id)
        if unit.misconception_id is not None else None
    )
    concept = db.get(Concept, unit.concept_id) if unit.concept_id is not None else None

    items = []
    if misconception is not None and misconception.problem_type:
        items = db.scalars(
            select(PracticeItem)
            .where(PracticeItem.is_seed.is_(True),
                   PracticeItem.problem_type == misconception.problem_type)
            .order_by(PracticeItem.id)
        ).all()
    # A concept unit has none, and that is not an oversight: practice items are
    # found through `problem_type`, which is a property of a wrong answer. A
    # prerequisite nobody was taught has no error pattern to exercise yet.

    return {
        "id": unit.id,
        "misconception_id": unit.misconception_id,
        "concept_id": unit.concept_id,
        # So a frontend reads a kind instead of inferring one from a null.
        "target": unit.target,
        "label": (misconception.label if misconception
                  else concept.name if concept else None),
        "title": unit.title,
        "body": unit.body,
        "practice_items": [
            {
                "id": i.id,
                "prompt": i.prompt,
                "kind": i.kind,
                "options": (i.options or {}).get("choices"),
                "problem_type": i.problem_type,
                # correct_answer is absent, exactly as it is everywhere else.
                # A teacher-facing screen is still a screen, and this payload
                # is one shoulder-surf away from a student.
            }
            for i in items
        ],
        "citations": citations if citations is not None else [],
        "status": unit.status,
        "approved_by": unit.approved_by_id,
        "created_at": unit.created_at.isoformat().replace("+00:00", "Z")
        if unit.created_at else None,
    }


@router.get("/reteach")
def list_reteach(
    status_filter: str = Query("all", alias="status"),
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """Not in the frozen contract, and added anyway: without it there is no way
    to reach a unit that already exists, including the seeded draft. Suggest
    returns a unit once and PATCH needs an id, so a teacher who reloaded the
    page had lost it."""
    stmt = select(ReteachUnit)
    if status_filter and status_filter != "all":
        stmt = stmt.where(ReteachUnit.status == status_filter)
    rows = db.scalars(stmt.order_by(ReteachUnit.id.desc())).all()
    return {"items": [_reteach_out(db, r) for r in rows]}


def _existing_unit(db: OrmSession, *, misconception_id=None, concept_id=None):
    """Any unit already covering this target, draft or assigned."""
    stmt = select(ReteachUnit)
    if misconception_id is not None:
        stmt = stmt.where(ReteachUnit.misconception_id == misconception_id)
    else:
        stmt = stmt.where(ReteachUnit.concept_id == concept_id)
    return db.scalars(stmt.order_by(ReteachUnit.id.desc())).first()


def _concepts_for_problem_type(db: OrmSession, problem_type: str | None) -> set[int]:
    """Which concepts a misconception's error pattern exercises.

    misconception.problem_type -> the seeded practice items carrying it ->
    their concept. The same join `practice.diagnose()` uses, which is why a
    unit and the items that detect it stay in step by construction.
    """
    if not problem_type:
        return set()
    return {
        cid
        for (cid,) in db.execute(
            select(PracticeItem.concept_id)
            .where(PracticeItem.problem_type == problem_type,
                   PracticeItem.concept_id.is_not(None))
            .distinct()
        ).all()
    }


def _draft_and_store(db: OrmSession, user: User, *, misconception=None, concept=None):
    """Draft one unit and upsert it. Returns `(unit, citations, report)`.

    Raises `reteach.NotSupported` / `AllProvidersFailed` for the caller to turn
    into a 422/503 or -- in the batch path -- into a skip reason. Shared so the
    single and batch routes cannot drift on the thing that matters: a unit is
    always written as `draft`, never assigned.
    """
    if misconception is not None:
        title, text, citations, report = reteach.draft(db, misconception)
        unit = db.scalar(
            select(ReteachUnit).where(
                ReteachUnit.misconception_id == misconception.id,
                ReteachUnit.status == "draft",
            )
        )
        if unit is None:
            unit = ReteachUnit(misconception_id=misconception.id)
            db.add(unit)
        detail = {"misconception": misconception.slug}
    else:
        title, text, citations, report = reteach.draft_for_concept(db, concept)
        unit = db.scalar(
            select(ReteachUnit).where(
                ReteachUnit.concept_id == concept.id,
                ReteachUnit.status == "draft",
            )
        )
        if unit is None:
            unit = ReteachUnit(concept_id=concept.id)
            db.add(unit)
        detail = {"concept": concept.slug}

    unit.title = title
    unit.body = text
    unit.status = "draft"          # never assigned, on either path
    unit.approved_by_id = None
    db.flush()

    db.add(AuditLog(actor_id=user.id, action="reteach.suggest",
                    target=f"reteach:{unit.id}", detail=detail))
    db.flush()
    return unit, citations, report


@router.post("/reteach/suggest", status_code=status.HTTP_201_CREATED)
def suggest_reteach(
    body: SuggestReteachIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """Draft a unit against one misconception or one prerequisite concept.
    Always `draft`, never assigned.

    Re-suggesting for a target that already has an unapproved draft replaces
    that draft rather than stacking another one up. A teacher pressing the
    button twice means "try again", not "give me two".
    """
    misconception = concept = None
    if body.misconception_id is not None:
        misconception = db.get(Misconception, body.misconception_id)
        if misconception is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "No such misconception."},
            )
    else:
        concept = db.get(Concept, body.concept_id)
        if concept is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "not_found", "message": "No such concept."},
            )

    try:
        unit, citations, report = _draft_and_store(
            db, user, misconception=misconception, concept=concept)
    except reteach.NotSupported as exc:
        # exc.report, not report -- `report` is only bound on the success path,
        # so reading it here raised UnboundLocalError and turned an honest 422
        # into a 500. The refusal branch is not rare: it fired on the second
        # misconception tried.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "insufficient_evidence",
                "message": (
                    "The approved course material does not cover this well "
                    "enough to build a reteach unit from. Writing one anyway "
                    "would put invented content behind your name."
                ),
                "detail": {
                    "alignment_percent": exc.report.to_dict()["alignment_percent"],
                },
            },
        )
    except AllProvidersFailed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "provider_unavailable",
                    "message": "Could not draft a unit just now. Try again shortly."},
        )

    out = _reteach_out(db, unit, citations=citations)
    out["evidence"] = report.to_dict()
    return out


TOP_N_PER_RANKING = 3
# How far down each ranking to keep looking when the top rows refuse or
# duplicate. Bounded so a barren corpus cannot turn one press into 40 model calls.
MAX_CANDIDATES_PER_RANKING = 8


@router.post("/reteach/suggest-top")
def suggest_top_reteach(
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """teacher-008 -- draft the whole panel: top 3 misconceptions + top 3 gaps.

    So a teacher opening the page finds it populated instead of finding a
    button they must press once per misconception, having first worked out
    which misconceptions are worth pressing it for.

    **Partial success is the normal case, not the error case.** The corpus
    genuinely cannot support a unit on every target -- that refusal is a
    feature, and it fires on real rows. One target refusing must never cost the
    other five, so every failure becomes a `skipped` entry with a reason and
    the loop carries on. That is also why this returns 200 and not 201.

    Nothing here is ever assigned. A batch button must not become a way around
    the approval gate.
    """
    created: list[dict] = []
    skipped: list[dict] = []

    def note(target, obj_id, label, reason, **extra):
        skipped.append({"target": target, "id": obj_id, "label": label,
                        "reason": reason, **extra})

    # Read the two panels through their own endpoints rather than reimplementing
    # their ranking here. If the heatmap ever changes what "top" means, this
    # follows it instead of quietly disagreeing with the screen beside it.
    heat = heatmap(db=db, user=user)["items"][:MAX_CANDIDATES_PER_RANKING]
    gaps = gap_map(db=db, user=user)["items"][:MAX_CANDIDATES_PER_RANKING]

    # Which concepts the misconception half already covers, via problem_type ->
    # the practice items that exercise it -> their concept. The top gap and the
    # top heatmap row are very often the same subject seen from two directions,
    # and two near-identical units read as padding.
    covered: dict[int, int] = {}

    def take(rows, want, handle):
        """Walk a ranking until `want` of its rows have a unit behind them.

        Strictly "the top three" filled the panel with two units on the real
        corpus: one target refused for lack of evidence and two gaps were
        already covered by a misconception unit. Those are correct decisions
        that still leave a teacher with an empty-looking screen, so a
        non-productive row advances to the next candidate instead of consuming
        a slot. A row that already HAS a unit does consume one -- the panel
        shows it, which is what the teacher actually cares about.
        """
        got = 0
        for row in rows:
            if got >= want:
                break
            if handle(row):
                got += 1
        return got

    def do_misconception(row) -> bool:
        misconception = db.get(Misconception, row["misconception_id"])
        if misconception is None:
            return False
        existing = _existing_unit(db, misconception_id=misconception.id)
        if existing is not None:
            # Skip, do not redraft. A batch button that overwrote drafts would
            # silently destroy a teacher's edits the second time they pressed
            # it -- and would spend model calls to do it. `suggest` is the
            # deliberate "try again" for one target.
            note("misconception", misconception.id, misconception.label,
                 "already_assigned" if existing.status != "draft" else "already_drafted",
                 unit_id=existing.id)
            # Coverage is a fact about the unit EXISTING, not about having made
            # it just now. When this was only recorded on the create path, a
            # second run skipped the covering misconception, forgot the
            # overlap, and drafted the duplicate gap unit the first run had
            # correctly declined.
            for cid in _concepts_for_problem_type(db, misconception.problem_type):
                covered[cid] = existing.id
            return True
        try:
            unit, citations, _ = _draft_and_store(db, user, misconception=misconception)
        except reteach.NotSupported as exc:
            note("misconception", misconception.id, misconception.label,
                 "insufficient_evidence",
                 alignment_percent=exc.report.to_dict()["alignment_percent"])
            return False
        except AllProvidersFailed:
            note("misconception", misconception.id, misconception.label,
                 "provider_unavailable")
            return False
        created.append(_reteach_out(db, unit, citations=citations))
        for cid in _concepts_for_problem_type(db, misconception.problem_type):
            covered[cid] = unit.id
        return True

    def do_concept(row) -> bool:
        concept = db.get(Concept, row["concept_id"])
        if concept is None:
            return False
        if concept.id in covered:
            note("concept", concept.id, concept.name,
                 "covered_by_misconception", unit_id=covered[concept.id])
            return False
        existing = _existing_unit(db, concept_id=concept.id)
        if existing is not None:
            note("concept", concept.id, concept.name,
                 "already_assigned" if existing.status != "draft" else "already_drafted",
                 unit_id=existing.id)
            return True
        try:
            unit, citations, _ = _draft_and_store(db, user, concept=concept)
        except reteach.NotSupported as exc:
            note("concept", concept.id, concept.name, "insufficient_evidence",
                 alignment_percent=exc.report.to_dict()["alignment_percent"])
            return False
        except AllProvidersFailed:
            note("concept", concept.id, concept.name, "provider_unavailable")
            return False
        created.append(_reteach_out(db, unit, citations=citations))
        return True

    # Misconceptions first, deliberately: they are what establishes `covered`,
    # so running the gap half first would draft the duplicate before knowing it
    # was one.
    from_heatmap = take(heat, TOP_N_PER_RANKING, do_misconception)
    from_gap_map = take(gaps, TOP_N_PER_RANKING, do_concept)

    return {
        "created": created,
        "skipped": skipped,
        # How many of each ranking's slots ended up with a unit behind them.
        # Below `requested` means the corpus could not support more, not that
        # the endpoint stopped early.
        "coverage": {
            "requested_per_ranking": TOP_N_PER_RANKING,
            "from_heatmap": from_heatmap,
            "from_gap_map": from_gap_map,
        },
    }


@router.patch("/reteach/{unit_id}")
def patch_reteach(
    unit_id: int,
    body: PatchReteachIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """Edit before approving. An approved unit is frozen.

    Letting a teacher edit after approval would mean the thing they approved
    and the thing students received could differ, with nothing recording that
    they ever diverged. Un-approve and re-approve is the honest path, and it
    leaves two audit rows.
    """
    unit = db.get(ReteachUnit, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such reteach unit."},
        )
    if unit.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "conflict",
                    "message": "This unit has been approved and can no longer be "
                               "edited. Students may already have it."},
        )

    if body.title is not None:
        unit.title = body.title.strip()[:300]
    if body.body is not None:
        unit.body = body.body.strip()
    db.add(AuditLog(actor_id=user.id, action="reteach.edit",
                    target=f"reteach:{unit.id}",
                    detail={"fields": [f for f in ("title", "body")
                                       if getattr(body, f) is not None]}))
    db.flush()
    return _reteach_out(db, unit)


@router.post("/reteach/{unit_id}/approve")
def approve_reteach(
    unit_id: int,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """The gate. Draft becomes assigned, and only a person can do this.

    The audit row is not decoration: `reteach_units` has no `approved_at`
    column, and teacher-005 reads the approval time from here to decide where
    its before/after boundary falls. Adding a column would mean a schema
    change, and a schema change means reset_db.py, which drops 3,000+
    embeddings. The moment is recorded; it just lives in the audit log.
    """
    unit = db.get(ReteachUnit, unit_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "No such reteach unit."},
        )
    if unit.status == "assigned":
        return _reteach_out(db, unit)

    unit.status = "assigned"
    unit.approved_by_id = user.id
    db.add(AuditLog(actor_id=user.id, action="reteach.approve",
                    target=f"reteach:{unit.id}",
                    detail={"title": unit.title}))
    db.flush()
    return _reteach_out(db, unit)



# ---------------------------------------------------------------------------
# teacher-009 -- which subject this console is showing
# ---------------------------------------------------------------------------

@router.get("/subjects")
def my_subjects(
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> dict:
    """The subjects this teacher is assigned to, each naming its cohorts.

    Assignment comes from `course_teachers` (admin-009) -- a teacher never
    picks their own subjects, an admin assigns them.
    """
    rows = db.scalars(
        select(CourseTeacher)
        .where(CourseTeacher.user_id == user.id)
        .order_by(CourseTeacher.id)
    ).all()

    items = []
    for ct in rows:
        c = ct.course
        if c is None:
            continue
        items.append({
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "semester": c.semester,
            "is_current": c.id == user.course_id,
            "batches": [
                {
                    "id": b.id,
                    "major": b.major,
                    "department": b.department.name,
                    "start_year": b.start_year,
                    "end_year": b.end_year,
                }
                for b in c.batches
            ],
        })
    return {"items": items}


@router.patch("/active-subject")
def set_active_subject(
    body: ActiveSubjectIn,
    db: OrmSession = Depends(get_db),
    user: User = Depends(teacher_only),
) -> UserOut:
    """Point the whole console at another of this teacher's subjects.

    Every panel here scopes by the signed-in teacher's course_id, so this one
    field moves the heatmap, the gap map, the reasoning paths, the flags, the
    tracking and the reteach queue together. Refused for a subject the
    teacher is not assigned to: the switcher must not become a way to read a
    colleague's class.
    """
    assigned = db.scalar(
        select(CourseTeacher).where(
            CourseTeacher.user_id == user.id,
            CourseTeacher.course_id == body.course_id,
        )
    )
    if assigned is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden",
                    "message": "You are not assigned to that subject."},
        )
    user.course_id = body.course_id
    db.flush()
    return UserOut.model_validate(user)
