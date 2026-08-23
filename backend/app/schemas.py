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
