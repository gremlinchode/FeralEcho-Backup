"""Client-side local store: conversations, drafts, saved prompts, recent files.

This is Echo Studio's own UI-level state — separate from FeralEcho's
memory/ directory, which stays exclusively owned by the Flask server (all
actual conversation persistence goes through POST /memory/conversation, not
through this file). SQLite, single file, no server dependency, no schema
migration framework needed at this size.
"""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DEFAULT_DB_PATH = Path.home() / ".echo_studio" / "echo_studio.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New conversation',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,          -- 'user' | 'echo'
    text TEXT NOT NULL,
    task_type TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS drafts (
    conversation_id TEXT PRIMARY KEY,
    text TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS saved_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recent_files (
    path TEXT PRIMARY KEY,
    opened_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalStore:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------
    def create_conversation(self, conversation_id: str, title: str = "New conversation") -> None:
        now = _now()
        self._conn.execute(
            "INSERT OR IGNORE INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conversation_id, title, now, now),
        )
        self._conn.commit()

    def touch_conversation(self, conversation_id: str) -> None:
        self._conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?", (_now(), conversation_id)
        )
        self._conn.commit()

    def rename_conversation(self, conversation_id: str, title: str) -> None:
        self._conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id)
        )
        self._conn.commit()

    def list_conversations(self) -> list:
        rows = self._conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_conversation(self, conversation_id: str) -> None:
        # with self._conn: commits all three on success or rolls back all
        # three on any exception — previously three independent statements
        # sharing one commit() at the end, so a failure partway through
        # left whichever DELETEs had already run sitting in an uncommitted
        # transaction on the shared connection (check_same_thread=False).
        with self._conn:
            self._conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            self._conn.execute("DELETE FROM drafts WHERE conversation_id = ?", (conversation_id,))
            self._conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    # ------------------------------------------------------------------
    # Messages (for the sidebar transcript + search — the durable FAISS
    # copy lives server-side; this is the fast local render cache)
    # ------------------------------------------------------------------
    def add_message(self, conversation_id: str, role: str, text: str, task_type: str = "") -> None:
        # Both statements share one transaction (with self._conn: commits on
        # success, rolls back on exception) — previously the INSERT and
        # touch_conversation()'s own separate UPDATE+commit were two
        # independent transactions, so a failure in the second left the
        # first's INSERT sitting uncommitted on the shared connection until
        # some later, unrelated write's commit() flushed it in.
        with self._conn:
            self._conn.execute(
                "INSERT INTO messages (conversation_id, role, text, task_type, timestamp) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, role, text, task_type, _now()),
            )
            self._conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?", (_now(), conversation_id)
            )

    def delete_last_message(self, conversation_id: str) -> None:
        """Used by regenerate: remove the most recent stored message (the
        echo response being replaced) so the local transcript doesn't end up
        with both the old and new answer to the same turn."""
        row = self._conn.execute(
            "SELECT id FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()
        if row is not None:
            self._conn.execute("DELETE FROM messages WHERE id = ?", (row["id"],))
            self._conn.commit()

    def get_messages(self, conversation_id: str) -> list:
        rows = self._conn.execute(
            "SELECT role, text, task_type, timestamp FROM messages "
            "WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_conversations(self, query: str) -> list:
        """Client-side substring search over titles + message text.
        Returns matching conversation ids/titles, most recently updated first."""
        like = f"%{query}%"
        rows = self._conn.execute(
            """
            SELECT DISTINCT c.id, c.title, c.updated_at
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.title LIKE ? OR m.text LIKE ?
            ORDER BY c.updated_at DESC
            """,
            (like, like),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Drafts (autosaved composer text per conversation)
    # ------------------------------------------------------------------
    def save_draft(self, conversation_id: str, text: str) -> None:
        self._conn.execute(
            "INSERT INTO drafts (conversation_id, text, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(conversation_id) DO UPDATE SET text = excluded.text, updated_at = excluded.updated_at",
            (conversation_id, text, _now()),
        )
        self._conn.commit()

    def get_draft(self, conversation_id: str) -> str:
        row = self._conn.execute(
            "SELECT text FROM drafts WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()
        return row["text"] if row else ""

    def clear_draft(self, conversation_id: str) -> None:
        self._conn.execute("DELETE FROM drafts WHERE conversation_id = ?", (conversation_id,))
        self._conn.commit()

    # ------------------------------------------------------------------
    # Saved prompts / templates
    # ------------------------------------------------------------------
    def save_prompt(self, title: str, text: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO saved_prompts (title, text, created_at) VALUES (?, ?, ?)",
            (title, text, _now()),
        )
        self._conn.commit()
        return cur.lastrowid

    def list_saved_prompts(self) -> list:
        rows = self._conn.execute(
            "SELECT id, title, text, created_at FROM saved_prompts ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_saved_prompt(self, prompt_id: int) -> None:
        self._conn.execute("DELETE FROM saved_prompts WHERE id = ?", (prompt_id,))
        self._conn.commit()

    # ------------------------------------------------------------------
    # Recent files (project explorer)
    # ------------------------------------------------------------------
    def record_recent_file(self, path: str, limit: int = 20) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO recent_files (path, opened_at) VALUES (?, ?) "
                "ON CONFLICT(path) DO UPDATE SET opened_at = excluded.opened_at",
                (path, _now()),
            )
            self._conn.execute(
                "DELETE FROM recent_files WHERE path NOT IN "
                "(SELECT path FROM recent_files ORDER BY opened_at DESC LIMIT ?)",
                (limit,),
            )

    def list_recent_files(self) -> list:
        rows = self._conn.execute(
            "SELECT path, opened_at FROM recent_files ORDER BY opened_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()
