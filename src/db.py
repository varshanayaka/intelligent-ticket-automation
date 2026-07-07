"""
Database connection layer.

Defaults to SQLite (zero setup, great for demo/GitHub).
Switch to MySQL by setting DB_BACKEND=mysql and filling in the
MYSQL_* environment variables -- no other code changes required.

This dual-backend design mirrors real AM projects, where the same
automation logic often needs to run against different client DB stacks.
"""
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")  # 'sqlite' or 'mysql'
SQLITE_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets.db"

MYSQL_CONFIG = dict(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    database=os.getenv("MYSQL_DATABASE", "ticket_automation"),
)


@contextmanager
def get_connection():
    """Yields a DB connection. Caller is responsible for commit(); connection auto-closes."""
    if DB_BACKEND == "mysql":
        import mysql.connector  # pip install mysql-connector-python
        conn = mysql.connector.connect(**MYSQL_CONFIG)
    else:
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Creates tables from schema.sql if they don't already exist."""
    schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
    schema_sql = schema_path.read_text()

    with get_connection() as conn:
        cur = conn.cursor()
        if DB_BACKEND == "mysql":
            # MySQL needs AUTOINCREMENT -> AUTO_INCREMENT and separate statements
            statements = schema_sql.replace(
                "INTEGER PRIMARY KEY AUTOINCREMENT",
                "INT AUTO_INCREMENT PRIMARY KEY",
            ).split(";")
            for stmt in statements:
                if stmt.strip():
                    cur.execute(stmt)
        else:
            cur.executescript(schema_sql)
        conn.commit()


def run_query(query, params=None, fetch=False):
    """Convenience helper for simple queries used across the demo scripts."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params or [])
        result = cur.fetchall() if fetch else None
        conn.commit()
        return result


if __name__ == "__main__":
    init_db()
    print(f"Database initialized ({DB_BACKEND}) at "
          f"{SQLITE_PATH if DB_BACKEND == 'sqlite' else MYSQL_CONFIG['database']}")
