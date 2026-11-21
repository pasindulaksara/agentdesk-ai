
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="AgentDesk AI",
    description="AI Agent and Automation Platform",
    version="1.0.0",
)


class TaskRequest(BaseModel):
    task: str


@app.get("/")
def home():
    return {
        "project": "AgentDesk AI",
        "status": "running",
        "message": "Your AI Agent platform is ready!"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/agent/run")
def run_agent(request: TaskRequest):
    return {
        "task": request.task,
        "status": "received",
        "message": "Agent execution will be connected next."
    }
