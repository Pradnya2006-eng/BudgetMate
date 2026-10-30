"""MySQL access: one connection per request, plus a few small helpers."""

from flask import current_app, g


def make_mysql_factory(config):
    """Returns a function that opens a new MySQL connection."""

    def factory():
        import pymysql  # imported here so tests can run without it installed

        return pymysql.connect(
            host=config["DB_HOST"],
            port=config["DB_PORT"],
            user=config["DB_USER"],
            password=config["DB_PASSWORD"],
            database=config["DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
            connect_timeout=10,
        )

    return factory


def get_db():
    if "db" not in g:
        g.db = current_app.config["DB_FACTORY"]()
    return g.db


def close_db(exc=None):
    conn = g.pop("db", None)
    if conn is None:
        return
    try:
        if exc is not None:
            conn.rollback()
    finally:
        conn.close()


def query_all(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def query_one(sql, params=()):
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=()):
    """Runs a write. Returns (last inserted id, number of rows changed)."""
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid, cur.rowcount


def commit():
    get_db().commit()


def is_duplicate_error(exc):
    """True for a UNIQUE-key violation (MySQL error 1062 / sqlite IntegrityError)."""
    return type(exc).__name__ == "IntegrityError"


def describe_connection_error(exc):
    """A plain-English hint for the common MySQL setup mistakes, or None."""
    if type(exc).__name__ != "OperationalError" or not exc.args:
        return None

    code = exc.args[0]
    if code == 1045:
        return "MySQL rejected the login. Check DB_USER and DB_PASSWORD in backend/.env."
    if code == 1049:
        return "The database doesn't exist yet. Run backend/schema.sql in MySQL first."
    if code in (2002, 2003, 2006, 2013):
        return "Can't reach MySQL. Is the MySQL server running, and are DB_HOST and DB_PORT right?"
    return None
