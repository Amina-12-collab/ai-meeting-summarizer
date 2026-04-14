"""
Module 7: History & Storage Management
Simple SQLite-based persistence for processed file records.
"""
 
import os
import json
import sqlite3
from typing import Any
 
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "whitetrack.db")
 
 
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
 
def _init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id          TEXT PRIMARY KEY,
                filename    TEXT NOT NULL,
                size_kb     REAL,
                type        TEXT,
                date        TEXT,
                status      TEXT,
                transcript  TEXT,
                summary     TEXT,
                key_points  TEXT,   -- JSON array
                action_items TEXT,  -- JSON array
                decisions   TEXT    -- JSON array
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.commit()
 
 
_init_db()
 
 
def save_record(record: dict[str, Any]):
    """Insert a new processing record into the database."""
    with _get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO records
            (id, filename, size_kb, type, date, status,
             transcript, summary, key_points, action_items, decisions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["id"],
            record["filename"],
            record.get("size_kb"),
            record.get("type"),
            record.get("date"),
            record.get("status", "Complete"),
            record.get("transcript", ""),
            record.get("summary", ""),
            json.dumps(record.get("key_points", [])),
            json.dumps(record.get("action_items", [])),
            json.dumps(record.get("decisions", [])),
        ))
        conn.commit()
 
 
def get_all_records() -> list[dict]:
    """Return all records ordered oldest first."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM records ORDER BY rowid ASC"
        ).fetchall()
    return [_deserialise(dict(row)) for row in rows]
 
 
def get_record_by_id(job_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM records WHERE id = ?", (job_id,)
        ).fetchone()
    return _deserialise(dict(row)) if row else None
 
 
def _deserialise(row: dict) -> dict:
    """Parse JSON-stored list fields back into Python lists."""
    for field in ("key_points", "action_items", "decisions"):
        if isinstance(row.get(field), str):
            try:
                row[field] = json.loads(row[field])
            except (json.JSONDecodeError, TypeError):
                row[field] = []
    return row

def create_user(username, password):
    with _get_conn() as conn:
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def authenticate_user(username, password):
    with _get_conn() as conn:
        row = conn.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        if row:
            return row["id"]
        return None