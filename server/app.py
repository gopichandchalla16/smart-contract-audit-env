from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import sys
import os
import uvicorn
import traceback
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Action, Observation, StepResult, RewardInfo
from smart_contract_audit_env_environment import SmartContractAuditEnv

START_TIME = time.time()
VALID_TASKS = ["easy", "medium", "hard"]

app = FastAPI(
    title="Smart Contract Audit Environment",
    description="OpenEnv-compliant RL environment for AI-powered Solidity smart contract security auditing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global env instance — always alive
env = SmartContractAuditEnv()


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
            "hint": "Environment auto-recovered. Retry your request."
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "valid_task_ids": VALID_TASKS,
            "hint": "Use task_id=easy, medium, or hard"
        }
    )


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    uptime_seconds = round(time.time() - START_TIME, 1)
    return {
        "status": "ok",
        "environment": "smart-contract-audit-env",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "tasks_available": VALID_TASKS
    }


# ── Root ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "Smart Contract Audit Environment",
        "version": "1.0.0",
        "tasks": VALID_TASKS,
        "endpoints": ["/reset", "/step", "/state", "/health", "/docs"],
        "usage": "POST /reset?task_id=easy to start, POST /step?task_id=easy with Action body to audit"
    }


# ── Reset ─────────────────────────────────────────────────────────────────────
@app.post("/reset")
def reset(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}"
        )
    try:
        obs = env.reset(task_id=task_id)
        return obs.dict()
    except Exception as e:
        # Auto-recover: reinit env and retry once
        global env
        env = SmartContractAuditEnv()
        obs = env.reset(task_id=task_id)
        return obs.dict()


# ── Step ──────────────────────────────────────────────────────────────────────
@app.post("/step")
def step(action: Action, task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}"
        )
    # Input sanitization
    if action.findings is None:
        action.findings = []
    if action.severity is None:
        action.severity = []
    if action.vulnerable_lines is None:
        action.vulnerable_lines = []
    if action.explanation is None:
        action.explanation = ""

    # Cap findings to prevent abuse (max 20)
    action.findings = action.findings[:20]
    action.vulnerable_lines = action.vulnerable_lines[:20]

    try:
        # Auto-reset if episode already done
        state = env.states.get(task_id, {})
        if state.get("step_count", 0) >= 5:
            env.reset(task_id=task_id)

        result = env.step(action=action, task_id=task_id)
        return result.dict()
    except Exception as e:
        # Auto-recover: reset this task and retry
        try:
            env.reset(task_id=task_id)
            result = env.step(action=action, task_id=task_id)
            return result.dict()
        except Exception as e2:
            raise HTTPException(
                status_code=500,
                detail=f"Step failed after recovery attempt: {str(e2)}"
            )


# ── State ─────────────────────────────────────────────────────────────────────
@app.get("/state")
def state(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}"
        )
    try:
        obs = env.state(task_id=task_id)
        return obs.dict()
    except Exception as e:
        env.reset(task_id=task_id)
        obs = env.state(task_id=task_id)
        return obs.dict()


# ── Legacy audit endpoint ─────────────────────────────────────────────────────
@app.post("/audit")
def audit(action: Action, task_id: str = "easy"):
    """Legacy endpoint — wraps /step for backward compatibility"""
    return step(action=action, task_id=task_id)


# ── Tasks list ────────────────────────────────────────────────────────────────
@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy", "difficulty": "easy", "vulnerabilities": 1, "description": "Find reentrancy in VulnerableBank"},
            {"id": "medium", "difficulty": "medium", "vulnerabilities": 3, "description": "Find 3 vulns in DeFiVault"},
            {"id": "hard", "difficulty": "hard", "vulnerabilities": 4, "description": "Find 4 vulns in ComplexDeFi"}
        ]
    }


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 7860)),
        reload=False,
        workers=1,
        timeout_keep_alive=30
    )


if __name__ == "__main__":
    main()
