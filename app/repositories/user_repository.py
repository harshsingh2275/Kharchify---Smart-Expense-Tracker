"""User repository - all SQL operations for users."""

import logging
import sqlite3

from app.exceptions import ConflictError

logger = logging.getLogger(__name__)


class UserRepository:
    """Handles all database operations for the users table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, username: str, password_hash: str) -> dict:
        """Insert a new user and return the created row as a dict."""
        try:
            cursor = self.conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            self.conn.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ConflictError("Username already taken")
        except sqlite3.Error:
            self.conn.rollback()
            logger.exception("Failed to create user '%s'", username)
            raise

    def get_by_username(self, username: str) -> dict | None:
        """Return a user by username (case-insensitive), or None if not found."""
        row = self.conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None

    def get_by_id(self, user_id: int) -> dict | None:
        """Return a user by ID, or None if not found."""
        row = self.conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
