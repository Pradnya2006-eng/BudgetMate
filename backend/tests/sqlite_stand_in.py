"""A SQLite database that quacks like a PyMySQL connection.

The tests use it so they can run on any computer without a MySQL server. The
app's SQL is written to work on both. The real MySQL schema is backend/schema.sql;
this file only has a simplified copy of it.
"""

import sqlite3

SCHEMA = """
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  amount NUMERIC NOT NULL CHECK (amount > 0),
  category TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  tx_date TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE budgets (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  monthly_budget NUMERIC NOT NULL DEFAULT 0 CHECK (monthly_budget >= 0),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE password_resets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TEXT NOT NULL,
  used_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class _Cursor:
    def __init__(self, raw):
        self._cur = raw.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._cur.close()

    def execute(self, sql, params=()):
        self._cur.execute(sql.replace("%s", "?"), tuple(params))

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(row) for row in self._cur.fetchall()]

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    @property
    def rowcount(self):
        return self._cur.rowcount


class Connection:
    def __init__(self, path):
        self._raw = sqlite3.connect(path)
        self._raw.row_factory = sqlite3.Row
        self._raw.execute("PRAGMA foreign_keys = ON")

    def cursor(self):
        return _Cursor(self._raw)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


def create_database(path):
    raw = sqlite3.connect(path)
    raw.executescript(SCHEMA)
    raw.commit()
    raw.close()


def factory_for(path):
    return lambda: Connection(path)
