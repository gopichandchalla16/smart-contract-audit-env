from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import uvicorn
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

# Global env instance
env = SmartContractAuditEnv()


def get_env() -> SmartContractAuditEnv:
    """Always returns a valid env, reinits if crashed."""
    global env
    if env is None:
        env = SmartContractAuditEnv()
    return env


def reinit_env() -> SmartContractAuditEnv:
    """Force reinitialize the global env."""
    global env
    env = SmartContractAuditEnv()
    return env


# --- Global exception handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
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


# --- Health ---
@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": "smart-contract-audit-env",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "tasks_available": VALID_TASKS
    }


# --- Root ---
@app.get("/")
def root():
    return {
        "name": "Smart Contract Audit Environment",
        "version": "1.0.0",
        "tasks": VALID_TASKS,
        "endpoints": ["/reset", "/step", "/state", "/health", "/tasks", "/docs"],
        "usage": "POST /reset?task_id=easy to start, POST /step?task_id=easy with Action body to audit"
    }


# --- Tasks list ---
@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy",   "difficulty": "easy",   "vulnerabilities": 1, "description": "Find reentrancy in VulnerableBank"},
            {"id": "medium", "difficulty": "medium", "vulnerabilities": 3, "description": "Find 3 vulns in DeFiVault"},
            {"id": "hard",   "difficulty": "hard",   "vulnerabilities": 4, "description": "Find 4 vulns in ComplexDeFi"}
        ]
    }


# --- Reset ---
@app.post("/reset")
def reset(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}")
    try:
        obs = get_env().reset(task_id=task_id)
        return obs.dict()
    except Exception:
        obs = reinit_env().reset(task_id=task_id)
        return obs.dict()


# --- Step ---
@app.post("/step")
def step(action: Action, task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}")

    # Input sanitization
    action.findings = (action.findings or [])[:20]
    action.severity = (action.severity or [])[:20]
    action.vulnerable_lines = (action.vulnerable_lines or [])[:20]
    action.explanation = action.explanation or ""

    try:
        e = get_env()
        # Auto-reset if episode already done
        if e.states.get(task_id, {}).get("step_count", 0) >= 5:
            e.reset(task_id=task_id)
        result = e.step(action=action, task_id=task_id)
        return result.dict()
    except Exception as ex:
        try:
            e = reinit_env()
            e.reset(task_id=task_id)
            result = e.step(action=action, task_id=task_id)
            return result.dict()
        except Exception as ex2:
            raise HTTPException(status_code=500, detail=f"Step failed: {str(ex2)}")


# --- State ---
@app.get("/state")
def state(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}")
    try:
        obs = get_env().state(task_id=task_id)
        return obs.dict()
    except Exception:
        e = reinit_env()
        e.reset(task_id=task_id)
        return e.state(task_id=task_id).dict()


# --- Legacy audit endpoint ---
@app.post("/audit")
def audit(action: Action, task_id: str = "easy"):
    """Legacy endpoint — wraps /step for backward compatibility"""
    return step(action=action, task_id=task_id)


# --- Entry point ---
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
