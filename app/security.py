"""Password hashing and JWT utilities."""

from datetime import datetime, timedelta, timezone
import logging

import bcrypt
import jwt

from app.config import settings
from app.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash. Returns False on malformed hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    """Create a signed JWT for the given user ID."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> int:
    """Decode a JWT and return the user ID. Raises AuthenticationError if invalid or expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise AuthenticationError("Invalid or expired token")

    sub = payload.get("sub")
    if sub is None:
        raise AuthenticationError("Invalid or expired token")

    try:
        return int(sub)
    except (ValueError, TypeError):
        raise AuthenticationError("Invalid or expired token")
