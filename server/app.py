from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Action, Observation, StepResult, RewardInfo
from smart_contract_audit_env_environment import SmartContractAuditEnv

app = FastAPI(
    title="Smart Contract Audit Environment",
    description="OpenEnv-compliant environment for AI-powered Solidity smart contract security auditing.",
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
    return {"status": "ok", "environment": "smart-contract-audit-env", "version": "1.0.0"}


@app.get("/")
def root():
    return {
        "name": "Smart Contract Audit Environment",
        "version": "1.0.0",
        "tasks": ["easy", "medium", "hard"],
        "endpoints": ["/reset", "/step", "/state", "/health", "/docs"]
    }


@app.post("/reset")
def reset(task_id: str = "easy"):
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail=f"Invalid task_id. Choose from: easy, medium, hard")
    obs = env.reset(task_id=task_id)
    return obs.dict()


@app.post("/step")
def step(action: Action, task_id: str = "easy"):
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail=f"Invalid task_id.")
    result = env.step(action=action, task_id=task_id)
    return result.dict()


@app.get("/state")
def state(task_id: str = "easy"):
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail=f"Invalid task_id.")
    obs = env.state(task_id=task_id)
    return obs.dict()


@app.post("/audit")
def audit(action: Action, task_id: str = "easy"):
    """Legacy audit endpoint — wraps /step for backward compatibility"""
    result = env.step(action=action, task_id=task_id)
    return result.dict()
