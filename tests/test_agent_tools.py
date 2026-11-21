
import pytest

from app.tools import task_tools
from app.services import workflow


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    """Use a separate temporary database for every test."""
    database = tmp_path / "test_agentdesk.db"

    monkeypatch.setattr(task_tools, "DB_PATH", database)

    task_tools.initialize_database()

    return database


def test_create_task(test_database):
    result = task_tools.create_task(
        title="Prepare AI interview",
        priority="high",
    )

    assert result["title"] == "Prepare AI interview"
    assert result["priority"] == "high"
    assert result["status"] == "pending"


def test_list_tasks(test_database):
    task_tools.create_task(
        title="Learn AI agents",
        priority="medium",
    )

    result = task_tools.list_tasks()

    assert result["count"] == 1
    assert result["tasks"][0]["title"] == "Learn AI agents"


def test_update_task(test_database):
    created = task_tools.create_task(
        title="Update GitHub",
    )

    result = task_tools.update_task(
        task_id=created["id"],
        status="completed",
    )

    assert result["status"] == "completed"


def test_invalid_priority(test_database):
    result = task_tools.create_task(
        title="Invalid task",
        priority="urgent",
    )

    assert "error" in result


def test_daily_plan_excludes_completed(test_database):
    completed = task_tools.create_task(
        title="Finished task",
        priority="high",
    )

    task_tools.update_task(
        task_id=completed["id"],
        status="completed",
    )

    task_tools.create_task(
        title="Pending task",
        priority="medium",
    )

    result = workflow.generate_daily_plan()

    assert result["planned_tasks"] == 1
    assert result["plan"][0]["title"] == "Pending task"


def test_priority_order(test_database):
    task_tools.create_task(
        title="Low priority",
        priority="low",
    )

    task_tools.create_task(
        title="High priority",
        priority="high",
    )

    result = workflow.get_priority_tasks()

    assert result["tasks"][0]["title"] == "High priority"
