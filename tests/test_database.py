"""Tests for database layer: init_db, get_connection, repositories, and constraints."""

import sqlite3

import pytest

from app.database import get_connection, init_db
from app.exceptions import ConflictError
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.user_repository import UserRepository


# ─── init_db ────────────────────────────────────────────────────────────────


def test_init_db_creates_users_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "users" in tables


def test_init_db_creates_categories_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "categories" in tables


def test_init_db_creates_expenses_table(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "expenses" in tables


def test_init_db_seeds_9_categories(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    conn.close()
    assert count == 9


def test_init_db_idempotent_does_not_duplicate_categories(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    init_db(db)  # run twice
    conn = get_connection(db)
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    conn.close()
    assert count == 9


# ─── get_connection ─────────────────────────────────────────────────────────


def test_get_connection_enables_foreign_keys(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.close()
    assert result == 1


# ─── Foreign key / integrity constraints ────────────────────────────────────


def test_insert_expense_with_nonexistent_user_id_raises_integrity_error(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, title, amount, expense_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (99999, 1, "X", 1.0, "2026-01-01"),
        )
        conn.commit()
    conn.close()


def test_insert_expense_with_nonexistent_category_id_raises_integrity_error(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    # Insert a real user first
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)", ("u1", "$2b$hash")
    )
    conn.commit()
    user_id = conn.execute("SELECT id FROM users WHERE username='u1'").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, title, amount, expense_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, 99999, "X", 1.0, "2026-01-01"),
        )
        conn.commit()
    conn.close()


def test_check_constraint_amount_zero_or_negative_raises_integrity_error(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("u2", "$2b$h"))
    conn.commit()
    uid = conn.execute("SELECT id FROM users WHERE username='u2'").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, title, amount, expense_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, 1, "T", 0.0, "2026-01-01"),
        )
        conn.commit()
    conn.close()


def test_check_constraint_empty_title_raises_integrity_error(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("u3", "$2b$h"))
    conn.commit()
    uid = conn.execute("SELECT id FROM users WHERE username='u3'").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, title, amount, expense_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid, 1, "", 10.0, "2026-01-01"),
        )
        conn.commit()
    conn.close()


# ─── UserRepository ──────────────────────────────────────────────────────────


def test_user_repository_duplicate_username_raises_conflict_error(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    repo = UserRepository(conn)
    repo.create("dup_user", "$2b$hash")
    with pytest.raises(ConflictError):
        repo.create("dup_user", "$2b$hash2")
    conn.close()


def test_user_repository_duplicate_different_case_raises_conflict_error(tmp_path):
    """Username uniqueness is case-insensitive due to the COLLATE NOCASE index."""
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    repo = UserRepository(conn)
    repo.create("CaseDup", "$2b$hash")
    with pytest.raises(ConflictError):
        repo.create("casedup", "$2b$hash2")
    conn.close()


# ─── Cascade delete ──────────────────────────────────────────────────────────


def test_deleting_user_cascades_removes_expenses(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("todelete", "$2b$h"))
    conn.commit()
    uid = conn.execute("SELECT id FROM users WHERE username='todelete'").fetchone()[0]
    conn.execute(
        "INSERT INTO expenses (user_id, category_id, title, amount, expense_date) "
        "VALUES (?, ?, ?, ?, ?)",
        (uid, 1, "Expense", 10.0, "2026-01-01"),
    )
    conn.commit()
    # Confirm expense exists
    count_before = conn.execute("SELECT COUNT(*) FROM expenses WHERE user_id=?", (uid,)).fetchone()[0]
    assert count_before == 1

    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit()

    count_after = conn.execute("SELECT COUNT(*) FROM expenses WHERE user_id=?", (uid,)).fetchone()[0]
    conn.close()
    assert count_after == 0


# ─── ExpenseRepository scoping ───────────────────────────────────────────────


def _setup_two_users(conn):
    """Insert two users and return (uid_a, uid_b)."""
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("repo_a", "$2b$h"))
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("repo_b", "$2b$h"))
    conn.commit()
    uid_a = conn.execute("SELECT id FROM users WHERE username='repo_a'").fetchone()[0]
    uid_b = conn.execute("SELECT id FROM users WHERE username='repo_b'").fetchone()[0]
    return uid_a, uid_b


def _insert_expense(conn, user_id):
    """Insert a raw expense for the given user_id and return its id."""
    conn.execute(
        "INSERT INTO expenses (user_id, category_id, title, amount, expense_date) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, 1, "repo_expense", 10.0, "2026-01-01"),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_expense_repository_get_with_wrong_user_returns_none(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    uid_a, uid_b = _setup_two_users(conn)
    expense_id = _insert_expense(conn, uid_a)

    repo = ExpenseRepository(conn)
    result = repo.get(user_id=uid_b, expense_id=expense_id)
    conn.close()
    assert result is None


def test_expense_repository_update_with_wrong_user_returns_none(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    uid_a, uid_b = _setup_two_users(conn)
    expense_id = _insert_expense(conn, uid_a)

    import datetime

    class _Data:
        category_id = 1
        title = "Hijacked"
        amount = 99.0
        expense_date = datetime.date(2026, 1, 1)
        note = None

    repo = ExpenseRepository(conn)
    result = repo.update(user_id=uid_b, expense_id=expense_id, data=_Data())
    conn.close()
    assert result is None


def test_expense_repository_delete_with_wrong_user_returns_false(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    uid_a, uid_b = _setup_two_users(conn)
    expense_id = _insert_expense(conn, uid_a)

    repo = ExpenseRepository(conn)
    deleted = repo.delete(user_id=uid_b, expense_id=expense_id)
    conn.close()
    assert deleted is False


def test_expense_repository_wrong_user_actions_leave_data_unchanged(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    conn = get_connection(db)
    uid_a, uid_b = _setup_two_users(conn)
    expense_id = _insert_expense(conn, uid_a)

    import datetime

    class _Data:
        category_id = 1
        title = "Hijacked"
        amount = 99.0
        expense_date = datetime.date(2026, 1, 1)
        note = None

    repo = ExpenseRepository(conn)
    repo.update(user_id=uid_b, expense_id=expense_id, data=_Data())
    repo.delete(user_id=uid_b, expense_id=expense_id)

    # Original expense must still exist with original values
    row = conn.execute("SELECT title, amount FROM expenses WHERE id=?", (expense_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row["title"] == "repo_expense"
    assert row["amount"] == 10.0
