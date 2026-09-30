CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES categories(id),
    title        TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
    amount       REAL NOT NULL CHECK (amount > 0),
    expense_date TEXT NOT NULL,
    note         TEXT CHECK (note IS NULL OR length(note) <= 300),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date
    ON expenses (user_id, expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_user_category
    ON expenses (user_id, category_id);

INSERT OR IGNORE INTO categories (name) VALUES
    ('Food'), ('Transport'), ('Housing'), ('Utilities'),
    ('Entertainment'), ('Health'), ('Education'), ('Shopping'), ('Other');
