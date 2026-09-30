"""FastAPI dependencies shared across routers."""

import logging
import sqlite3
from typing import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import get_connection
from app.exceptions import AuthenticationError
from app.repositories.user_repository import UserRepository
from app.security import decode_access_token

logger = logging.getLogger(__name__)

# auto_error=False means FastAPI will not produce its own 403 on missing credentials;
# our dependency raises AuthenticationError with our own format instead.
_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a database connection for the duration of a request."""
    conn = get_connection(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Decode the Bearer token and return the authenticated user dict."""
    if credentials is None:
        raise AuthenticationError("Not authenticated")

    try:
        user_id = decode_access_token(credentials.credentials)
    except AuthenticationError:
        logger.warning("Invalid or expired token presented")
        raise AuthenticationError("Invalid or expired token")

    user = UserRepository(conn).get_by_id(user_id)
    if user is None:
        logger.warning("Token references unknown user id=%d", user_id)
        raise AuthenticationError("Invalid or expired token")

    return user
