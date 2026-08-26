"""Every database table, in one file.

Decided early and then frozen -- after the freeze, changes go through the backend
owner. Sync SQLAlchemy 2.0 only; see the async policy in CLAUDE.md.

Four deliberate absences, all taken straight from the problem statement. Do not
"helpfully" add them back:

  * No score / grade / percentage column anywhere. The diagnostic produces a gap
    list, not a grade.
  * No time-on-task or last-seen column. Teacher dashboards are about
    misconceptions, not surveillance.
  * UncertaintyFlag has no user_id. You cannot leak what you never stored.
  * MisconceptionDiagnosis.confirmed is three-state, and only True is counted.
"""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 384  # bge-small-en-v1.5


class Base(DeclarativeBase):
    pass


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Institution structure  (admin-002)
# ---------------------------------------------------------------------------

course_prerequisites = Table(
    "course_prerequisites",
    Base.metadata,
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    Column("prerequisite_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)


# admin-010. Which cohorts take which subject. Many-to-many on purpose: one
# subject is commonly taught to several cohorts at once, and they share the
# corpus, the diagnostic and the misconception history -- a course row per
# cohort would fragment all three. Unlinking is not deleting: the row here
# goes, the subject and everything hanging off it stays.
batch_courses = Table(
    "batch_courses",
    Base.metadata,
    Column("batch_id", ForeignKey("batches.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)


# admin-009. A batch is a cohort: a major in a department, from a start year
# to the major's fixed end (btech 4, bca 3, mtech 2, mca 2 -- config, not
# request). College onboarding is deliberately not built; the standard
# department list stands in for it.
MAJORS = ("btech", "bca", "mtech", "mca")


class Batch(Base):
    """One admitted cohort, e.g. "BTech in CSE, 2026-2030" (admin-009)."""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    major: Mapped[str] = mapped_column(String(10), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    start_year: Mapped[int] = mapped_column(Integer)
    # Computed server-side from MAJOR_YEARS at creation; never client-supplied.
    end_year: Mapped[int] = mapped_column(Integer)
    # The curriculum document the batch was created with. A stored file, not
    # an ingestable Material: nothing consumes it in this build, so attaching
    # it to the courses corpus would be a lie the ingest queue would expose.
    curriculum_name: Mapped[str | None] = mapped_column(String(300))
    curriculum_path: Mapped[str | None] = mapped_column(String(500))
    reused_from_batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = _now()

    department: Mapped["Department"] = relationship()
    courses: Mapped[list["Course"]] = relationship(
        "Course", secondary=batch_courses, back_populates="batches"
    )

    @property
    def label(self) -> str:
        return f"{self.major.upper()} {self.department.name} {self.start_year}-{self.end_year}"


class CourseTeacher(Base):
    """A teacher attached to a subject (admin-009).

    No cap: one subject is commonly taught by 10-15 teachers and a limit would
    only be wrong. The join is the assignment; the account lives in users and
    outlives it, so unassigning never orphans a person.
    """

    __tablename__ = "course_teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assigned_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = _now()

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    course: Mapped["Course"] = relationship()


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))

    # admin-005. All nullable, because they were added to a table that already
    # had rows in the shared database and nothing may break for a course that
    # predates them.
    semester: Mapped[int | None] = mapped_column(Integer)
    # A list because one subject is commonly taught to more than one admission
    # year at once; they share the course, the corpus and the diagnostic. A
    # Postgres array rather than a join table: this is read as a whole, never
    # queried by element, and the stack is Postgres-only.
    admission_batches: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))
    # The teaching window, and NOT decoration: admin-006 refuses to delete
    # already-ingested material while a course is mid-term, and reads these.
    term_start: Mapped[date | None] = mapped_column(Date)
    term_end: Mapped[date | None] = mapped_column(Date)

    department: Mapped["Department | None"] = relationship()

    def in_term(self, on: date) -> bool:
        """Is `on` inside this course's teaching window?

        False when either date is missing -- a course nobody has dated has no
        protected window, and guessing one would block deletions on a course
        whose term the admin never recorded.
        """
        if self.term_start is None or self.term_end is None:
            return False
        return self.term_start <= on <= self.term_end

    # admin-010. The cohorts that take this subject. NOT the same thing as
    # `admission_batches` above, which is a free list of admission YEARS that
    # PUT /term writes and admin-006's delete guard reads; this is the real
    # foreign-key link and is what "which batches take this" means.
    batches: Mapped[list["Batch"]] = relationship(
        "Batch", secondary=batch_courses, back_populates="courses"
    )

    # Which courses must a student have done before this one. This is what lets
    # gap detection name the correct prior course.
    prerequisites: Mapped[list["Course"]] = relationship(
        "Course",
        secondary=course_prerequisites,
        primaryjoin=id == course_prerequisites.c.course_id,
        secondaryjoin=id == course_prerequisites.c.prerequisite_id,
    )


# ---------------------------------------------------------------------------
# Users and sessions  (auth-001)
# ---------------------------------------------------------------------------

ROLES = ("student", "teacher", "admin")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"))
    preferred_language: Mapped[str] = mapped_column(String(8), default="en")
    # auth-004. Enrolment details captured at student signup. Verification is
    # deliberately not built ("all are welcome"); the columns exist so the
    # data has somewhere to live when a college supplies a roll list later.
    university: Mapped[str | None] = mapped_column(String(200))
    roll_number: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = _now()

    course: Mapped["Course | None"] = relationship()


class Session(Base):
    """Opaque login token. Deliberately not a JWT -- logout deletes the row."""

    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = _now()

    user: Mapped["User"] = relationship()


# ---------------------------------------------------------------------------
# Curriculum  (admin-001, ingest-001)
# ---------------------------------------------------------------------------

# "reference" (admin-007) is supplementary study material -- quotable like a
# textbook, unlike "assignment". See retrieval.LESSON_KINDS.
MATERIAL_KINDS = ("syllabus", "textbook", "notes", "assignment", "reference")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(20), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|archived
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    source_path: Mapped[str | None] = mapped_column(String(500))
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = _now()
    ingest_status: Mapped[str] = mapped_column(String(20), default="queued")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    course: Mapped["Course"] = relationship()
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="material",
                                                 cascade="all, delete-orphan")


class Chunk(Base):
    """A piece of a source document, anchored to the page it came from.

    page_no is the field the whole citation story rests on. It is captured at
    ingestion and carried unchanged all the way to the UI -- no model is ever
    asked where a passage came from, which is why our citations cannot
    hallucinate.
    """

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), index=True
    )
    page_no: Mapped[int] = mapped_column(Integer, index=True)
    chapter: Mapped[str | None] = mapped_column(String(300))
    char_start: Mapped[int] = mapped_column(Integer, default=0)
    char_end: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))

    material: Mapped["Material"] = relationship(back_populates="chunks")


# ---------------------------------------------------------------------------
# Curriculum map
# ---------------------------------------------------------------------------

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    slug: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(200))

    __table_args__ = (UniqueConstraint("course_id", "slug"),)


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    # Which earlier course this concept should have been learned in.
    prerequisite_course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"))

    topic: Mapped["Topic"] = relationship()
    prerequisite_course: Mapped["Course | None"] = relationship()


# ---------------------------------------------------------------------------
# Diagnostic, gaps, mastery  (student-002, student-007)
# ---------------------------------------------------------------------------

ITEM_KINDS = ("mcq", "numeric", "short_text")


class DiagnosticItem(Base):
    __tablename__ = "diagnostic_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    prompt: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default="mcq")
    options: Mapped[dict | None] = mapped_column(JSON)
    # Never serialise this to a client. Strip it in the response schema.
    correct_answer: Mapped[str] = mapped_column(String(300))

    concept: Mapped["Concept"] = relationship()


class DiagnosticResponse(Base):
    """What a student picked for one diagnostic item -- student-009.

    **The answer text, and deliberately nothing else.** There is no `correct`
    column here and there must not be one. `submit_diagnostic` judges
    correctness in memory and writes only Gap and Mastery rows, precisely so
    that no count of right answers exists anywhere to be serialised by
    accident; storing correctness per item would hand that count straight back.
    A client that reads every row still cannot mark one of them, because
    `DiagnosticItem.correct_answer` never leaves the server.

    One row per (student, item), overwritten on re-submit. Not an attempt log:
    the diagnostic is a starting point, not a performance record.
    """

    __tablename__ = "diagnostic_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    diagnostic_item_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_items.id", ondelete="CASCADE"), index=True
    )
    answer: Mapped[str] = mapped_column(String(300))
    at: Mapped[datetime] = _now()

    __table_args__ = (UniqueConstraint("user_id", "diagnostic_item_id"),)


class Gap(Base):
    """A prerequisite concept this student is missing.

    Persisted, not ephemeral: written when the diagnostic is submitted and
    readable forever after, so the dashboard, the mastery view and chat prompt
    suggestions all read the same rows.
    """

    __tablename__ = "gaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    detected_from: Mapped[str] = mapped_column(String(30))  # diagnostic|syllabus_upload|practice
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|improving|closed
    created_at: Mapped[datetime] = _now()

    concept: Mapped["Concept"] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)


class Mastery(Base):
    __tablename__ = "mastery"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    state: Mapped[str] = mapped_column(String(20), default="untested")  # solid|shaky|untested
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    concept: Mapped["Concept"] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)


# ---------------------------------------------------------------------------
# Practice and attempts  (student-005, student-006)
# ---------------------------------------------------------------------------

class PracticeSet(Base):
    __tablename__ = "practice_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    gap_id: Mapped[int | None] = mapped_column(ForeignKey("gaps.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = _now()

    items: Mapped[list["PracticeItem"]] = relationship(back_populates="practice_set",
                                                       cascade="all, delete-orphan")


class PracticeItem(Base):
    __tablename__ = "practice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    practice_set_id: Mapped[int | None] = mapped_column(
        ForeignKey("practice_sets.id", ondelete="CASCADE"), index=True
    )
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"))
    # The join key to misconceptions. A wrong answer is only matched against
    # misconceptions carrying the SAME problem_type -- that is what keeps a
    # diagnosis specific instead of generic.
    problem_type: Mapped[str] = mapped_column(String(60), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default="mcq")
    options: Mapped[dict | None] = mapped_column(JSON)
    correct_answer: Mapped[str] = mapped_column(String(300))  # never sent to a client
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)

    practice_set: Mapped["PracticeSet | None"] = relationship(back_populates="items")
    concept: Mapped["Concept | None"] = relationship()


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    practice_item_id: Mapped[int] = mapped_column(ForeignKey("practice_items.id"), index=True)
    answer: Mapped[str] = mapped_column(String(300))
    correct: Mapped[bool] = mapped_column(Boolean)
    at: Mapped[datetime] = _now()

    item: Mapped["PracticeItem"] = relationship()


# ---------------------------------------------------------------------------
# Misconceptions  (student-006, teacher-001, teacher-002)
# ---------------------------------------------------------------------------

class Misconception(Base):
    __tablename__ = "misconceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    problem_type: Mapped[str] = mapped_column(String(60), index=True)
    label: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    # Seeded signature of the wrong answer this misconception produces.
    # A match here diagnoses with no LLM call at all -- fast and deterministic.
    wrong_answer_pattern: Mapped[str | None] = mapped_column(String(300))

    topic: Mapped["Topic | None"] = relationship()


class MisconceptionDiagnosis(Base):
    """confirmed is three-state on purpose.

    None  = the student was asked but has not answered yet
    True  = the student agreed this was their reasoning
    False = the student disagreed

    ONLY True is counted in teacher aggregates. Denied diagnoses are kept for
    honesty but excluded everywhere, which is what makes the teacher's number
    mean "students who agreed" rather than "the algorithm's guesses".
    """

    __tablename__ = "misconception_diagnoses"

    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"))
    misconception_id: Mapped[int] = mapped_column(ForeignKey("misconceptions.id"), index=True)
    source: Mapped[str] = mapped_column(String(20), default="pattern")  # pattern|llm
    confirmed: Mapped[bool | None] = mapped_column(Boolean, default=None, index=True)
    at: Mapped[datetime] = _now()

    attempt: Mapped["Attempt"] = relationship()
    misconception: Mapped["Misconception"] = relationship()


class TutorMessage(Base):
    """One turn of a student's Ask Tutor chat -- tutor-002.

    The transcript exists so a page reload does not wipe a conversation, and
    for nothing else. It is keyed to the student, readable only through
    GET /tutor/history as the signed-in user, and deliberately carries no
    analysis columns -- no time-on-task, no sentiment, nothing a teacher
    dashboard could aggregate into surveillance (see the rules at the top of
    this file). Refused turns are stored too: a refusal is part of the
    conversation, and the general-knowledge fallback answer lives inside the
    stored response dict rather than out here where it might look quotable.
    """

    __tablename__ = "tutor_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), index=True)
    # "student" = what they typed, in the language they typed it.
    # "tutor"   = the full TutorResponse dict, verbatim, in `response`.
    role: Mapped[str] = mapped_column(String(10))
    text: Mapped[str | None] = mapped_column(Text)        # student turns only
    response: Mapped[dict | None] = mapped_column(JSON)   # tutor turns only
    created_at: Mapped[datetime] = _now()


# ---------------------------------------------------------------------------
# Teacher-facing  (teacher-004, teacher-006, teacher-007, admin-003)
# ---------------------------------------------------------------------------

class UncertaintyFlag(Base):
    """Written whenever the tutor refuses for lack of evidence.

    No user_id, by design. Teacher views must be anonymous, and the cheapest
    guarantee is to never record the link in the first place.
    """

    __tablename__ = "uncertainty_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    alignment_score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(100))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), index=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    occurred_at: Mapped[datetime] = _now()


class ReteachUnit(Base):
    __tablename__ = "reteach_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    # teacher-008: a unit targets a misconception OR a prerequisite concept,
    # never both and never neither. The gap map ranks concepts, not wrong
    # beliefs, so a NOT NULL misconception_id left it nothing to hang a unit on.
    #
    # Two columns rather than a (kind, target_id) pair on purpose: these are
    # real foreign keys to different tables, and a polymorphic id would give up
    # referential integrity to save one column.
    misconception_id: Mapped[int | None] = mapped_column(
        ForeignKey("misconceptions.id"), index=True
    )
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    # draft is invisible to every student query. The approval gate is the
    # human-in-the-loop story -- never auto-assign.
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = _now()

    misconception: Mapped["Misconception | None"] = relationship()
    concept: Mapped["Concept | None"] = relationship()

    @property
    def target(self) -> str:
        """Which of the two this unit is about. The API returns this so a
        frontend never has to infer a kind from which field happens to be null."""
        return "misconception" if self.misconception_id is not None else "concept"


class SourcedContent(Base):
    """Material the AI found outside the knowledge base, awaiting teacher approval.

    Seeded for this build -- no live web search is implemented. The queue itself
    is the feature.
    """

    __tablename__ = "sourced_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(300))
    excerpt: Mapped[str] = mapped_column(Text)
    found_for_gap: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    reject_reason: Mapped[str | None] = mapped_column(String(300))
    found_at: Mapped[datetime] = _now()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60), index=True)
    target: Mapped[str] = mapped_column(String(120))
    detail: Mapped[dict | None] = mapped_column(JSON)
    at: Mapped[datetime] = _now()

    actor: Mapped["User | None"] = relationship()
