
from datetime import datetime
from typing import Any

from app.tools.task_tools import list_tasks, update_task


def get_priority_tasks() -> dict[str, Any]:
    """
    Retrieve pending and in-progress tasks,
    prioritizing high-priority work.
    """
    result = list_tasks()

    if "error" in result:
        return result

    active_tasks = [
        task
        for task in result["tasks"]
        if task["status"] in ("pending", "in_progress")
    ]

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    active_tasks.sort(
        key=lambda task: (
            priority_order.get(task["priority"], 3),
            task["due_date"] or "9999-12-31",
            task["id"],
        )
    )

    return {
        "count": len(active_tasks),
        "tasks": active_tasks,
    }


def generate_daily_plan(max_tasks: int = 5) -> dict[str, Any]:
    """
    Generate a structured daily plan using saved tasks.

    Args:
        max_tasks: Maximum number of tasks to include.
    """
    if not 1 <= max_tasks <= 20:
        return {"error": "max_tasks must be between 1 and 20"}

    result = get_priority_tasks()

    if "error" in result:
        return result

    selected_tasks = result["tasks"][:max_tasks]

    plan = []

    for index, task in enumerate(selected_tasks, start=1):
        plan.append({
            "order": index,
            "task_id": task["id"],
            "title": task["title"],
            "priority": task["priority"],
            "due_date": task["due_date"],
            "suggested_action": (
                f"Work on {task['title']} and record your progress."
            ),
        })

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_active_tasks": result["count"],
        "planned_tasks": len(plan),
        "plan": plan,
    }


def start_high_priority_tasks(
    limit: int = 1,
) -> dict[str, Any]:
    """
    Start up to 'limit' pending high-priority tasks
    by updating their status to in_progress.

    Args:
        limit: Maximum number of tasks to start.
    """
    if not 1 <= limit <= 5:
        return {"error": "limit must be between 1 and 5"}

    result = get_priority_tasks()

    if "error" in result:
        return result

    pending_high_priority = [
        task
        for task in result["tasks"]
        if task["priority"] == "high"
        and task["status"] == "pending"
    ]

    selected = pending_high_priority[:limit]
    updated = []

    for task in selected:
        updated.append(
            update_task(
                task_id=task["id"],
                status="in_progress",
            )
        )

    return {
        "started_count": len(updated),
        "tasks": updated,
    }
