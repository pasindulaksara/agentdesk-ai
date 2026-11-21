
import json
import time
from datetime import datetime

from ollama import chat

from app.tools.task_tools import (
    create_task,
    list_tasks,
    update_task,
)


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
}


def run_agent(task: str) -> dict:
    started_at = time.perf_counter()
    tool_history = []

    messages = [
        {
            "role": "system",
            "content": (
                "You are AgentDesk AI, a task management assistant. "
                "Use tools to create, list, and update tasks. "
                "Use get_current_time when you need today's date. "
                "Due dates must be YYYY-MM-DD. "
                "Never claim a task was saved unless the tool confirms it. "
                "Do not invent tool results. "
                "Keep answers short."
            ),
        },
        {"role": "user", "content": task},
    ]

    for step in range(MAX_STEPS):
        print(f"[AGENT] Step {step + 1}", flush=True)

        response = chat(
            model=MODEL,
            messages=messages,
            tools=[
                get_current_time,
                calculate,
                create_task,
                list_tasks,
                update_task,
            ],
            think=False,
            options={
                "temperature": 0,
                "num_predict": 256,
            },
        )

        messages.append(response.message)
        tool_calls = response.message.tool_calls or []

        if not tool_calls:
            return {
                "task": task,
                "answer": response.message.content or "",
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

    return {
        "task": task,
        "answer": "Agent reached maximum steps.",
        "tools_used": tool_history,
        "steps": MAX_STEPS,
        "execution_time_seconds": round(
            time.perf_counter() - started_at, 2
        ),
    }
