"""Expense repository - all SQL operations for expenses."""

import logging
import sqlite3
from datetime import date

logger = logging.getLogger(__name__)


class ExpenseRepository:
    """Handles all database operations for the expenses table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def _fetch_joined(self, expense_id: int) -> dict:
        """Fetch a full joined expense row by id (internal helper after write)."""
        row = self.conn.execute(
            """
            SELECT e.id, e.title, e.amount, e.category_id, c.name AS category_name,
                   e.expense_date, e.note, e.created_at, e.updated_at
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            WHERE e.id = ?
            """,
            (expense_id,),
        ).fetchone()
        return dict(row)

    def create(self, user_id: int, data) -> dict:
        """Insert a new expense and return the full joined row."""
        try:
            cursor = self.conn.execute(
                """
                INSERT INTO expenses (user_id, category_id, title, amount, expense_date, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data.category_id,
                    data.title,
                    data.amount,
                    data.expense_date.isoformat(),
                    data.note,
                ),
            )
            self.conn.commit()
            return self._fetch_joined(cursor.lastrowid)
        except sqlite3.Error:
            self.conn.rollback()
            logger.exception("Failed to create expense for user %d", user_id)
            raise

    def get(self, user_id: int, expense_id: int) -> dict | None:
        """Return one expense by ID scoped to the given user, or None."""
        row = self.conn.execute(
            """
            SELECT e.id, e.title, e.amount, e.category_id, c.name AS category_name,
                   e.expense_date, e.note, e.created_at, e.updated_at
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            WHERE e.id = ? AND e.user_id = ?
            """,
            (expense_id, user_id),
        ).fetchone()
        return dict(row) if row else None

    def list(
        self,
        user_id: int,
        category_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Return filtered expenses and the total matching count (before pagination)."""
        # Build WHERE clause from fixed SQL fragments only — no user input interpolated
        where = "WHERE e.user_id = ?"
        params: list = [user_id]

        if category_id is not None:
            where += " AND e.category_id = ?"
            params.append(category_id)
        if start_date is not None:
            where += " AND e.expense_date >= ?"
            params.append(start_date.isoformat())
        if end_date is not None:
            where += " AND e.expense_date <= ?"
            params.append(end_date.isoformat())

        total = self.conn.execute(
            f"SELECT COUNT(*) FROM expenses e {where}", params
        ).fetchone()[0]

        rows = self.conn.execute(
            f"""
            SELECT e.id, e.title, e.amount, e.category_id, c.name AS category_name,
                   e.expense_date, e.note, e.created_at, e.updated_at
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            {where}
            ORDER BY e.expense_date DESC, e.id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()

        return [dict(r) for r in rows], total

    def update(self, user_id: int, expense_id: int, data) -> dict | None:
        """Update an expense and return the updated joined row, or None if not found."""
        try:
            cursor = self.conn.execute(
                """
                UPDATE expenses
                SET title = ?, amount = ?, category_id = ?, expense_date = ?, note = ?,
                    updated_at = datetime('now')
                WHERE id = ? AND user_id = ?
                """,
                (
                    data.title,
                    data.amount,
                    data.category_id,
                    data.expense_date.isoformat(),
                    data.note,
                    expense_id,
                    user_id,
                ),
            )
            self.conn.commit()
            if cursor.rowcount == 0:
                return None
            return self.get(user_id, expense_id)
        except sqlite3.Error:
            self.conn.rollback()
            logger.exception("Failed to update expense %d for user %d", expense_id, user_id)
            raise

    def delete(self, user_id: int, expense_id: int) -> bool:
        """Delete a user's expense. Returns True if deleted, False if not found."""
        try:
            cursor = self.conn.execute(
                "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                (expense_id, user_id),
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            self.conn.rollback()
            logger.exception("Failed to delete expense %d for user %d", expense_id, user_id)
            raise

    def monthly_summary(self, user_id: int, month: str) -> dict:
        """Return total spent, count, and per-category breakdown for a given month."""
        rows = self.conn.execute(
            """
            SELECT c.id AS category_id, c.name AS category_name,
                   COUNT(*) AS count, ROUND(SUM(e.amount), 2) AS total
            FROM expenses e
            JOIN categories c ON c.id = e.category_id
            WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
            GROUP BY c.id, c.name
            ORDER BY total DESC
            """,
            (user_id, month),
        ).fetchall()

        by_category = [dict(r) for r in rows]
        total_spent = round(sum(r["total"] for r in by_category), 2)
        expense_count = sum(r["count"] for r in by_category)

        return {
            "total_spent": total_spent,
            "expense_count": expense_count,
            "by_category": by_category,
        }
