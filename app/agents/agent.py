
import json
import time
from datetime import datetime

from ollama import chat

from app.tools.task_tools import create_task, list_tasks, update_task
from app.services.workflow import (
    get_priority_tasks,
    generate_daily_plan,
    start_high_priority_tasks,
)
from app.services.memory import get_history, save_message


MODEL = "qwen3:1.7b"
MAX_STEPS = 4


def get_current_time() -> str:
    """Get the current local date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(a: float, b: float, operation: str) -> float:
    """
    Perform a mathematical calculation.

    Args:
        a: First number.
        b: Second number.
        operation: add, subtract, multiply, or divide.
    """
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    raise ValueError("Unsupported operation")


AVAILABLE_TOOLS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "create_task": create_task,
    "list_tasks": list_tasks,
    "update_task": update_task,
    "get_priority_tasks": get_priority_tasks,
    "generate_daily_plan": generate_daily_plan,
    "start_high_priority_tasks": start_high_priority_tasks,
}


def run_agent(task: str, session_id: str = "default") -> dict:
    started_at = time.perf_counter()
    tool_history = []

    history = get_history(session_id)

    messages = [
        {
            "role": "system",
            "content": (
                "You are AgentDesk AI, an AI task management "
                "and workflow automation assistant. "
                "Use conversation history to understand follow-up requests. "
                "Use tools to create, list, and update tasks. "
                "Use get_priority_tasks for important tasks. "
                "Use generate_daily_plan for daily plans. "
                "Use start_high_priority_tasks only when explicitly requested. "
                "Never change task statuses without permission. "
                "Use get_current_time for today's date. "
                "Due dates must use YYYY-MM-DD. "
                "Never invent task details or tool results. "
                "Keep responses concise."
            ),
        },
        *history,
        {"role": "user", "content": task},
    ]

    for step in range(MAX_STEPS):
        print(f"[AGENT] Session: {session_id} | Step {step + 1}", flush=True)

        response = chat(
            model=MODEL,
            messages=messages,
            tools=list(AVAILABLE_TOOLS.values()),
            think=False,
            options={
                "temperature": 0,
                "num_predict": 256,
            },
        )

        messages.append(response.message)
        tool_calls = response.message.tool_calls or []

        if not tool_calls:
            answer = response.message.content or ""

            save_message(session_id, "user", task)
            save_message(session_id, "assistant", answer)

            return {
                "session_id": session_id,
                "task": task,
                "answer": answer,
                "tools_used": tool_history,
                "steps": step + 1,
                "execution_time_seconds": round(
                    time.perf_counter() - started_at, 2
                ),
            }

        for call in tool_calls:
            name = call.function.name
            arguments = call.function.arguments or {}

            print(f"[TOOL] {name}: {arguments}", flush=True)

            try:
                if name not in AVAILABLE_TOOLS:
                    raise ValueError(f"Unknown tool: {name}")

                result = AVAILABLE_TOOLS[name](**arguments)

            except Exception as error:
                result = {"error": str(error)}

            tool_history.append({
                "tool": name,
                "arguments": arguments,
                "result": result,
            })

            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(result),
            })

    answer = "Agent reached maximum execution steps."

    save_message(session_id, "user", task)
    save_message(session_id, "assistant", answer)

    return {
        "session_id": session_id,
        "task": task,
        "answer": answer,
        "tools_used": tool_history,
        "steps": MAX_STEPS,
        "execution_time_seconds": round(
            time.perf_counter() - started_at, 2
        ),
    }
