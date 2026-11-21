
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
    session_id: str = Field(
        default="default",
        min_length=1,
        max_length=100,
    )


@app.get("/")
def home():
    return {
        "project": "AgentDesk AI",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/agent/run")
async def execute_agent(request: TaskRequest):
    try:
        return await run_in_threadpool(
            run_agent,
            request.task,
            request.session_id,
        )

    except Exception as error:
        print(f"Agent error: {error}", flush=True)
        raise HTTPException(
            status_code=500,
            detail="Agent execution failed",
        )
