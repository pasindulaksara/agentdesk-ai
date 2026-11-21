
import json
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "agentdesk.db"

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "in_progress", "completed"}


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending',
                due_date TEXT,
                created_at TEXT NOT NULL
            )
        """)


def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = "",
) -> dict:
    """
    Create a task and save it permanently.

    Args:
        title: Short name of the task.
        description: Optional task details.
        priority: Task priority: low, medium, or high.
        due_date: Optional due date in YYYY-MM-DD format.

    Returns:
        The newly created task.
    """
    initialize_database()

    title = title.strip()
    priority = priority.lower().strip()

    if not title:
        return {"error": "Task title cannot be empty"}

    if priority not in VALID_PRIORITIES:
        return {"error": "Priority must be low, medium, or high"}

    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Due date must use YYYY-MM-DD format"}

    created_at = datetime.now().isoformat(timespec="seconds")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks
            (title, description, priority, status, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                priority,
                "pending",
                due_date or None,
                created_at,
            ),
        )

        task_id = cursor.lastrowid

    return {
        "id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "due_date": due_date or None,
        "created_at": created_at,
    }


def list_tasks(status: str = "all") -> dict:
    """
    List saved tasks, optionally filtered by status.

    Args:
        status: all, pending, in_progress, or completed.

    Returns:
        A dictionary containing the tasks.
    """
    initialize_database()

    if status != "all" and status not in VALID_STATUSES:
        return {"error": "Invalid task status"}

    with get_connection() as connection:
        if status == "all":
            rows = connection.execute(
                "SELECT * FROM tasks ORDER BY id DESC"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()

    return {
        "count": len(rows),
        "tasks": [dict(row) for row in rows],
    }


def update_task(
    task_id: int,
    status: str,
) -> dict:
    """
    Update the status of an existing task.

    Args:
        task_id: Numeric ID of the task.
        status: pending, in_progress, or completed.

    Returns:
        The updated task or an error.
    """
    initialize_database()

    if status not in VALID_STATUSES:
        return {"error": "Invalid task status"}

    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )

        if cursor.rowcount == 0:
            return {"error": f"Task {task_id} not found"}

        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return dict(row)


initialize_database()
