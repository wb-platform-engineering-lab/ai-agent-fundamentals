"""
memory.py — SQLite episodic memory for standup-bot.

Stores daily work entries and loads them as context for Claude.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path("standup.db")


@dataclass
class DayEntry:
    date: str
    plan: str = ""
    notes: str = ""
    completed: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            date       TEXT PRIMARY KEY,
            plan       TEXT DEFAULT '',
            notes      TEXT DEFAULT '',
            completed  TEXT DEFAULT '[]',
            blockers   TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    return conn


def save_entry(entry: DayEntry):
    """Insert or update a day entry."""
    conn = _connect()
    conn.execute(
        """
        INSERT INTO entries (date, plan, notes, completed, blockers)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            plan      = excluded.plan,
            notes     = excluded.notes,
            completed = excluded.completed,
            blockers  = excluded.blockers
        """,
        (
            entry.date,
            entry.plan,
            entry.notes,
            json.dumps(entry.completed),
            json.dumps(entry.blockers),
        ),
    )
    conn.commit()
    conn.close()


def load_entry(day: str) -> DayEntry | None:
    """Load a specific day's entry. Returns None if not found."""
    conn = _connect()
    row = conn.execute(
        "SELECT date, plan, notes, completed, blockers FROM entries WHERE date = ?",
        (day,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return DayEntry(
        date=row[0],
        plan=row[1],
        notes=row[2],
        completed=json.loads(row[3]),
        blockers=json.loads(row[4]),
    )


def load_recent(days_back: int = 5) -> list[DayEntry]:
    """Load the last N days of entries."""
    conn = _connect()
    rows = conn.execute(
        "SELECT date, plan, notes, completed, blockers FROM entries ORDER BY date DESC LIMIT ?",
        (days_back,),
    ).fetchall()
    conn.close()
    return [
        DayEntry(
            date=r[0],
            plan=r[1],
            notes=r[2],
            completed=json.loads(r[3]),
            blockers=json.loads(r[4]),
        )
        for r in reversed(rows)
    ]


def build_context(days_back: int = 3) -> str:
    """
    Build a context string from recent entries.
    This is what gets injected into Claude's system prompt.
    """
    entries = load_recent(days_back)
    if not entries:
        return "No previous standup entries found."

    lines = ["Recent work history:"]
    for entry in entries:
        lines.append(f"\n{entry.date}:")
        if entry.plan:
            lines.append(f"  Planned: {entry.plan}")
        if entry.completed:
            lines.append(f"  Completed: {', '.join(entry.completed)}")
        if entry.blockers:
            lines.append(f"  Blockers: {', '.join(entry.blockers)}")
        if entry.notes:
            lines.append(f"  Notes: {entry.notes}")

    return "\n".join(lines)


def today() -> str:
    return date.today().isoformat()


def yesterday() -> str:
    return (date.today() - timedelta(days=1)).isoformat()
