
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parents[2] / "agentdesk.db"

MAX_HISTORY_MESSAGES = 20


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def initialize_memory():
    """Create the conversation memory table."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON conversation_messages(session_id, id)
        """)


def save_message(
    session_id: str,
    role: str,
    content: str,
) -> dict[str, Any]:
    """Save one conversation message."""

    if not session_id.strip():
        raise ValueError("session_id cannot be empty")

    if role not in {"user", "assistant"}:
        raise ValueError("Invalid message role")

    if not content.strip():
        raise ValueError("Message content cannot be empty")

    initialize_memory()

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO conversation_messages
            (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, created_at),
        )

        message_id = cursor.lastrowid

    return {
        "id": message_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": created_at,
    }


def get_history(
    session_id: str,
    limit: int = MAX_HISTORY_MESSAGES,
) -> list[dict[str, str]]:
    """Retrieve recent messages in chronological order."""

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    initialize_memory()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT role, content
            FROM conversation_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in reversed(rows)
    ]


def clear_history(session_id: str) -> dict[str, Any]:
    """Delete saved conversation messages for a session."""

    initialize_memory()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM conversation_messages
            WHERE session_id = ?
            """,
            (session_id,),
        )

    return {
        "session_id": session_id,
        "deleted_messages": cursor.rowcount,
    }


initialize_memory()
