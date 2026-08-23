"""Password hashing and session tokens.

pbkdf2_sha256 from the standard library, not bcrypt. bcrypt needs a native
build that regularly fails on Windows, and passlib has a known incompatibility
with bcrypt 4.1+. Losing an hour to that during a 36-hour build buys nothing:
pbkdf2 with 260k iterations is entirely adequate here.

Format stored in users.password_hash:

    pbkdf2_sha256$<iterations>$<salt>$<hex digest>

Self-describing, so the iteration count can be raised later without
invalidating existing hashes.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16


def hash_password(plain: str, *, salt: str | None = None,
                  iterations: int = ITERATIONS) -> str:
    """Hash a password. A random salt is generated unless one is supplied.

    `salt` is a parameter only so seeding can produce deterministic hashes;
    never pass it from request-handling code.
    """
    salt = salt or secrets.token_hex(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), iterations)
    return f"{ALGORITHM}${iterations}${salt}${dk.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    """Constant-time verification. Never raises on a malformed hash."""
    try:
        algorithm, iterations, salt, digest = stored.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256", plain.encode(), salt.encode(), int(iterations)
        ).hex()
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(expected, digest)


def new_session_token() -> str:
    """Opaque login token. Deliberately not a JWT: nothing is encoded inside it,
    and logging out deletes the row, so revocation actually works."""
    return secrets.token_hex(32)
