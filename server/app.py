from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Action, Observation, StepResult, RewardInfo, TaskInfo
from server.smart_contract_audit_env_environment import SmartContractAuditEnv

app = FastAPI(
    title="Smart Contract Audit Environment",
    description="OpenEnv environment for AI-powered Solidity smart contract security auditing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = SmartContractAuditEnv()


@app.get("/health")
def health():
    return {"status": "ok", "environment": "smart_contract_audit_env"}


@app.post("/reset", response_model=Observation)
def reset(task_id: str = "easy"):
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="task_id must be easy, medium, or hard")
    return env.reset(task_id=task_id)


@app.post("/step", response_model=StepResult)
def step(action: Action, task_id: str = "easy"):
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="task_id must be easy, medium, or hard")
    return env.step(action=action, task_id=task_id)


@app.get("/state", response_model=Observation)
def state(task_id: str = "easy"):
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail="task_id must be easy, medium, or hard")
    return env.state(task_id=task_id)


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            TaskInfo(task_id="easy", description="Audit a simple contract with 1 reentrancy vulnerability", difficulty="easy", max_steps=5),
            TaskInfo(task_id="medium", description="Audit a DeFi contract with 3 vulnerabilities", difficulty="medium", max_steps=5),
            TaskInfo(task_id="hard", description="Audit a complex DeFi protocol with 4 vulnerabilities", difficulty="hard", max_steps=5),
        ]
    }


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()