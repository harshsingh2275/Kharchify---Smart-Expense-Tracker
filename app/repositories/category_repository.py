"""Category repository - all SQL operations for categories."""

import sqlite3


class CategoryRepository:
    """Handles all database operations for the categories table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_all(self) -> list[dict]:
        """Return all categories ordered by id."""
        rows = self.conn.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]

    def exists(self, category_id: int) -> bool:
        """Return True if the given category id exists."""
        row = self.conn.execute(
            "SELECT 1 FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        return row is not None
