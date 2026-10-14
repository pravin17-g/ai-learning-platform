"""
auth.py - Password hashing and token-based login (Phase 4: uses the database).

How login works:
  1. /register  -> the password is hashed with bcrypt. Only the hash is stored.
  2. /login     -> if the password matches, we create a signed token (JWT).
  3. Protected endpoints -> the client sends "Authorization: Bearer <token>".
                            get_current_user() checks the token and loads the student.

A JWT is SIGNED, not encrypted. Never put secrets inside it.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import models
from database import get_db

# ---------- Secret key ----------
# The secret key signs the tokens. Order of choice:
#   1. the SECRET_KEY environment variable, if you set one
#   2. the key saved in backend/.secret_key (created once, so tokens survive restarts)
#   3. a temporary random key, if the file cannot be written
KEY_FILE = Path(__file__).parent / ".secret_key"


def _load_secret_key() -> str:
    from_environment = os.getenv("SECRET_KEY")
    if from_environment:
        return from_environment
    if KEY_FILE.exists():
        saved = KEY_FILE.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    new_key = secrets.token_urlsafe(32)
    try:
        KEY_FILE.write_text(new_key, encoding="utf-8")
    except OSError:
        print("NOTE: Could not save .secret_key. Using a temporary key for this run.")
    return new_key


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60
MAX_PASSWORD_BYTES = 72  # bcrypt can only use the first 72 bytes of a password

# Makes Swagger UI show an "Authorize" button
bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="JWT",
    description="Paste the access_token returned by POST /login (without the word 'Bearer').",
)


# ---------- Passwords ----------
def hash_password(password: str) -> str:
    """Turn a password into a safe hash (bcrypt adds a random salt automatically)."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a stored hash."""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


# Used when a login email does not exist, so the response time looks the same
# as for a wrong password. This stops people from guessing which emails exist.
DUMMY_HASH = hash_password("dummy-password-for-timing")


# ---------- Tokens ----------
def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),  # "subject" = who this token belongs to
        "iat": now,           # issued at
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),  # expires at
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.Student:
    """
    Use this on every student-specific endpoint:  student = Depends(auth.get_current_user)
    The student is found from the TOKEN, never from something the client sends.
    This is how we make sure a student can only reach their own records.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in first. Send your token in the Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Your login is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    student = db.get(models.Student, user_id)
    if student is None:
        raise HTTPException(
            status_code=401,
            detail="This account no longer exists. Please register or log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return student
