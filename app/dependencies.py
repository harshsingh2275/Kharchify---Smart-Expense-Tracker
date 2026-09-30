"""FastAPI dependencies shared across routers."""

import sqlite3
from typing import Generator

from app.config import settings
from app.database import get_connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a database connection for the duration of a request."""
    conn = get_connection(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


# TODO (T5.2): Replace this placeholder with the real JWT-based implementation.
def get_current_user() -> dict:
    """Temporary placeholder — always returns user id 1. Replaced in T5.2."""
    return {"id": 1}
