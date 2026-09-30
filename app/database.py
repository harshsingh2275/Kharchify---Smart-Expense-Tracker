"""Database connection and initialization helpers."""

from pathlib import Path
import logging
import sqlite3

from app.config import settings

logger = logging.getLogger(__name__)


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    """Create and return a configured SQLite connection."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str) -> None:
    """Initialize the database schema and seed data from db/schema.sql."""
    schema_path = settings.base_dir / "db" / "schema.sql"
    conn = get_connection(db_path)
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Database initialized successfully at %s", db_path)
    except Exception:
        logger.exception("Failed to initialize database at %s", db_path)
        raise
    finally:
        conn.close()
