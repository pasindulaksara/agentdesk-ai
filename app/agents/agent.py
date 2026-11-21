import json
import time
from datetime import datetime

from ollama import chat

MODEL = "qwen3:1.7b"
MAX_STEPS = 3


# Tool 1: Get current date and time
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Tool 2: Perform calculations
def calculate(a: float, b: float, operation: str) -> float:
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

    raise ValueError(f"Unsupported operation: {operation}")


AVAILABLE_TOOLS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
}


def run_agent(task: str) -> dict:
    print(f"\n[AGENT] Task: {task}", flush=True)

    started_at = time.perf_counter()

    messages = [
        {
            "role": "system",
            "content": (
                "You are AgentDesk AI, an AI assistant. "
                "Use the available tools when a task requires them. "
                "For mathematical calculations, use the calculate tool. "
                "For current date or time, use get_current_time. "
                "Do not invent tool results. "
                "Keep answers short and clear."
            ),
        },
        {
            "role": "user",
            "content": task,
        },
    ]

    tool_history = []

    for step in range(MAX_STEPS):
        step_number = step + 1

        print(f"[AGENT] Step {step_number} started...", flush=True)

        step_started = time.perf_counter()

        try:
            response = chat(
                model=MODEL,
                messages=messages,
                tools=[get_current_time, calculate],
                think=False,
                options={
                    "temperature": 0,
                    "num_predict": 128,
                },
            )

        except Exception as error:
            print(f"[ERROR] Ollama: {error}", flush=True)
            raise

        step_seconds = round(time.perf_counter() - step_started, 2)

        print(
            f"[AGENT] Step {step_number} completed " f"in {step_seconds}s", flush=True
        )

        print(f"[AGENT] Tool calls: {response.message.tool_calls}", flush=True)

        messages.append(response.message)

        tool_calls = response.message.tool_calls or []

        if not tool_calls:
            total_seconds = round(time.perf_counter() - started_at, 2)

            print(f"[AGENT] Finished in {total_seconds}s", flush=True)

            return {
                "task": task,
                "answer": response.message.content or "",
                "tools_used": tool_history,
                "steps": step_number,
                "execution_time_seconds": total_seconds,
            }

        for tool_call in tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments or {}

            print(f"[TOOL] Executing: {name}({arguments})", flush=True)

            if name not in AVAILABLE_TOOLS:
                result = {"error": f"Unknown tool: {name}"}

            else:
                try:
                    result = AVAILABLE_TOOLS[name](**arguments)

                except Exception as error:
                    result = {"error": str(error)}

            print(f"[TOOL] Result: {result}", flush=True)

            tool_history.append(
                {
                    "tool": name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(result),
                }
            )

    total_seconds = round(time.perf_counter() - started_at, 2)

    print(f"[AGENT] Maximum steps reached after {total_seconds}s", flush=True)

    return {
        "task": task,
        "answer": "Agent reached maximum execution steps.",
        "tools_used": tool_history,
        "steps": MAX_STEPS,
        "execution_time_seconds": total_seconds,
    }
