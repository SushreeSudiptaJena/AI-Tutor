"""Request and response shapes. Mirrors docs/api-contract.md.

Response models exist partly to *omit* things: DiagnosticItem and PracticeItem
both carry correct_answer in the database, and it must never reach a client.
Serialising the ORM object directly would leak the answer key into the network
tab, so every item goes out through an explicit model here.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Role = Literal["student", "teacher", "admin"]

# Deliberately permissive. Real address validation needs `email-validator`, and
# a hackathon signup form does not justify the dependency.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class _ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth -------------------------------------------------------------------

class SignupIn(BaseModel):
    email: str
    password: str
    full_name: str
    role: Role = "student"
    course_id: int | None = None

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("not a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full name is required")
        return v


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class PreferencesIn(BaseModel):
    preferred_language: str

    @field_validator("preferred_language")
    @classmethod
    def _lang(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z]{2}$", v):
            raise ValueError("language must be a two-letter code")
        return v


class UserOut(_ORM):
    id: int
    email: str
    full_name: str
    role: Role
    course_id: int | None = None
    preferred_language: str
    # password_hash is absent on purpose. Do not add it.


class TokenOut(BaseModel):
    token: str
    user: UserOut


# --- shared response pieces -------------------------------------------------

class CitationOut(BaseModel):
    chunk_id: int
    material_id: int
    book_title: str
    page_no: int
    chapter: str | None = None
    snippet: str


class EvidenceOut(BaseModel):
    alignment_score: float
    alignment_percent: int
    top_similarity: float
    threshold: float
    sufficient: bool
    reason: str | None = None


class GapOut(_ORM):
    id: int
    concept: str
    prerequisite_course: str | None = None
    detected_from: str
    status: str
    suggested_prompts: list[str] = []


class ItemOut(BaseModel):
    """A question as the client sees it. correct_answer is NOT a field here."""

    id: int
    prompt: str
    kind: str
    options: list[str] | None = None
    concept: str | None = None
    problem_type: str | None = None


# --- tutor (rag-003) --------------------------------------------------------

class TutorAskIn(BaseModel):
    """`course_id` is deliberately absent: the course comes from the signed-in
    user, so nobody can read another course's material by editing the body."""

    question: str
    # None, not "en": the fallback is the student's saved preference, and the
    # router is the only place that knows it.
    language: str | None = None
    topic_id: int | None = None

    @field_validator("question")
    @classmethod
    def _question(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("ask a question of at least a few characters")
        return v[:2000]

    @field_validator("language")
    @classmethod
    def _lang(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if not v:
            return None
        if not re.match(r"^[a-z]{2}$", v):
            raise ValueError("language must be a two-letter code")
        return v


# --- student diagnostic (student-002) ---------------------------------------

class AnswerIn(BaseModel):
    item_id: int
    answer: str

    @field_validator("answer")
    @classmethod
    def _answer(cls, v: str) -> str:
        return v.strip()[:300]


class DiagnosticSubmitIn(BaseModel):
    """No score comes back from this, so none is accepted into it either --
    there is no 'time_taken' or 'confidence' field to grow one out of."""

    answers: list[AnswerIn]

    @field_validator("answers")
    @classmethod
    def _answers(cls, v: list[AnswerIn]) -> list[AnswerIn]:
        if not v:
            raise ValueError("submit at least one answer")
        seen = {a.item_id for a in v}
        if len(seen) != len(v):
            raise ValueError("the same item was answered more than once")
        return v


# --- practice (student-005, student-006) ------------------------------------

class PracticeGenerateIn(BaseModel):
    """`gap_id` is required. Practice that is not scoped to a gap is just a
    quiz, and the scoping is the whole claim of student-005."""

    gap_id: int
    count: int | None = None

    @field_validator("count")
    @classmethod
    def _count(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 8:
            raise ValueError("count must be between 1 and 8")
        return v


class PracticeAnswerIn(BaseModel):
    item_id: int
    answer: str

    @field_validator("answer")
    @classmethod
    def _answer(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("answer is required")
        return v[:300]


class ConfirmDiagnosisIn(BaseModel):
    """Three-state on the way in too: the student either agrees or disagrees.
    There is no 'skip' -- an unanswered diagnosis simply stays `confirmed=None`
    because this endpoint was never called."""

    confirmed: bool


# --- teacher (teacher-004) --------------------------------------------------

class ResolveFlagIn(BaseModel):
    note: str | None = None


# --- teacher-006 / teacher-007 -------------------------------------------

class RejectSourcedIn(BaseModel):
    reason: str | None = None


class SuggestReteachIn(BaseModel):
    misconception_id: int


class PatchReteachIn(BaseModel):
    """Both optional: a teacher who only fixes the title should not have to
    resend the body they did not touch."""

    title: str | None = None
    body: str | None = None


# --- admin (admin-001, admin-002) -------------------------------------------

class DepartmentIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("department name is required")
        return v[:200]


class CourseIn(BaseModel):
    code: str
    title: str
    department_id: int | None = None
    prerequisite_course_ids: list[int] = []

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("course code is required")
        return v[:20]

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("course title is required")
        return v[:200]
