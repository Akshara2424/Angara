"""
database.py — All SQLite logic for Coal Mine Compliance Tracker

ER DIAGRAM:
──────────────────────────────────────────────────────────────────
  PROJECTS  ──< MILESTONES   (1 project has many milestones)

  ┌─────────────────────────────┐      ┌──────────────────────────────────┐
  │         PROJECTS            │      │           MILESTONES             │
  ├─────────────────────────────┤      ├──────────────────────────────────┤
  │ PK id          INTEGER      │──┐   │ PK id           INTEGER          │
  │    name        TEXT UNIQUE  │  └──►│ FK project_id   → PROJECTS(id)  │
  │    start_date  TEXT         │      │    name         TEXT             │
  │    location    TEXT         │      │    offset_days  INTEGER          │
  │    created_at  TEXT         │      │    target_date  TEXT             │
  └─────────────────────────────┘      │    actual_date  TEXT (nullable)  │
                                       │    status       TEXT CHECK(...)  │
                                       │    notes        TEXT             │
                                       │    updated_at   TEXT             │
                                       └──────────────────────────────────┘
"""

import sqlite3
import pandas as pd
from datetime import date, timedelta
import os

# ── Config ──────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "coal_compliance.db")

DEFAULT_MILESTONES = [
    ("EIA Submission",            30),
    ("Land NOC",                  60),
    ("Forest Clearance Stage 1",  90),
    ("Pollution Control NOC",    120),
    ("Mining Lease Grant",       180),
]

STATUS_OPTIONS = ["pending", "in_progress", "complete", "delayed"]


# ── Connection ───────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema ───────────────────────────────────────────────────────
def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            start_date  TEXT    NOT NULL,
            location    TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS milestones (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id   INTEGER NOT NULL,
            name         TEXT    NOT NULL,
            offset_days  INTEGER NOT NULL DEFAULT 0,
            target_date  TEXT    NOT NULL,
            actual_date  TEXT,
            status       TEXT    NOT NULL DEFAULT 'pending'
                         CHECK(status IN ('pending','in_progress','complete','delayed')),
            notes        TEXT,
            updated_at   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


# ── Projects ─────────────────────────────────────────────────────
def create_project(name: str, start_date: date, location: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name, start_date, location) VALUES (?, ?, ?)",
        (name, start_date.isoformat(), location),
    )
    project_id = cur.lastrowid
    for m_name, offset in DEFAULT_MILESTONES:
        target = start_date + timedelta(days=offset)
        cur.execute(
            """INSERT INTO milestones
               (project_id, name, offset_days, target_date, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (project_id, m_name, offset, target.isoformat()),
        )
    conn.commit()
    conn.close()
    return project_id


def get_projects() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, name, start_date, location, created_at FROM projects ORDER BY created_at DESC",
        conn,
    )
    conn.close()
    return df


def delete_project(project_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


# ── Milestones ───────────────────────────────────────────────────
def get_milestones(project_id: int) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        """SELECT id, name, offset_days, target_date, actual_date,
                  status, notes, updated_at
           FROM milestones
           WHERE project_id = ?
           ORDER BY offset_days""",
        conn,
        params=(project_id,),
    )
    conn.close()
    return df


def update_milestone(milestone_id: int, status: str, notes: str, actual_date=None):
    conn = get_conn()
    conn.execute(
        """UPDATE milestones
           SET status=?, notes=?, actual_date=?, updated_at=datetime('now')
           WHERE id=?""",
        (status, notes, actual_date, milestone_id),
    )
    conn.commit()
    conn.close()


def add_custom_milestone(project_id: int, name: str, target_date: date, notes: str):
    conn = get_conn()
    proj = conn.execute(
        "SELECT start_date FROM projects WHERE id=?", (project_id,)
    ).fetchone()
    start  = date.fromisoformat(proj[0])
    offset = (target_date - start).days
    conn.execute(
        """INSERT INTO milestones (project_id, name, offset_days, target_date, notes, status)
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (project_id, name, offset, target_date.isoformat(), notes),
    )
    conn.commit()
    conn.close()