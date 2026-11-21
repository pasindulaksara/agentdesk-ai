
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.agents.agent import run_agent


app = FastAPI(
    title="AgentDesk AI",
    description="AI Agent and Automation Platform",
    version="1.0.0",
)


class TaskRequest(BaseModel):
    task: str = Field(min_length=1)


@app.get("/")
def home():
    return {
        "project": "AgentDesk AI",
        "status": "running",
        "message": "AI Agent is ready!"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/agent/run")
async def execute_agent(request: TaskRequest):
    try:
        result = await run_in_threadpool(run_agent, request.task)
        return result

    except Exception as error:
        print(f"Agent error: {error}")
        raise HTTPException(
            status_code=500,
            detail="Agent execution failed"
        )
