"""SQLite storage for tasks."""
import json
import sqlite3
from pathlib import Path

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    due TEXT,
    priority TEXT NOT NULL DEFAULT 'medium',
    tags TEXT NOT NULL DEFAULT '',
    done INTEGER NOT NULL DEFAULT 0
)
"""

PRIORITIES = ("high", "medium", "low")


def connect(path=":memory:", seed=True):
    """Open the database, creating the table and adding the sample tasks if it is empty."""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    if seed and conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
        with open(SEED_FILE, encoding="utf-8") as fh:
            for task in json.load(fh):
                add_task(conn, **task)
    return conn


def _row(row):
    return dict(row) if row is not None else None


def add_task(conn, title, description="", due=None, priority="medium", tags="", done=False):
    cursor = conn.execute(
        "INSERT INTO tasks (title, description, due, priority, tags, done) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, due, priority, tags, int(done)),
    )
    conn.commit()
    return get_task(conn, cursor.lastrowid)


def get_task(conn, task_id):
    return _row(conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone())


def list_tasks(conn, tag=None):
    tasks = [_row(row) for row in conn.execute("SELECT * FROM tasks ORDER BY id")]
    if tag:
        tasks = [task for task in tasks if tag in task["tags"].split(",")]
    return tasks


def search_tasks(conn, query):
    """Tasks whose title contains the query."""
    sql = f"SELECT * FROM tasks WHERE title LIKE '%{query}%' ORDER BY id"
    return [_row(row) for row in conn.execute(sql)]


def set_done(conn, task_id, done=True):
    conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(done), task_id))
    conn.commit()


def delete_task(conn, task_id):
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()


def progress(conn):
    """How many tasks are done, as a count and a percentage."""
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    return {"total": total, "done": done, "percent": done // total * 100}
