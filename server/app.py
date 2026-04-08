from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import uvicorn
import time
import threading
import requests as http_requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Action, Observation, StepResult, RewardInfo
from smart_contract_audit_env_environment import SmartContractAuditEnv

START_TIME = time.time()
VALID_TASKS = ["easy", "medium", "hard"]

# NUCLEAR CLAMP: applied to every outgoing JSON response
SCORE_FLOOR = 0.01
SCORE_CEIL  = 0.99

def nuclear_clamp(v) -> float:
    """Last-resort clamp on every score before it leaves the server."""
    try:
        v = float(v)
    except Exception:
        return SCORE_FLOOR
    if v <= 0.0:
        return SCORE_FLOOR
    if v >= 1.0:
        return SCORE_CEIL
    return round(v, 4)

def sanitize_response(d: dict) -> dict:
    """Walk the response dict and clamp all score fields. NUCLEAR SAFETY."""
    score_fields = {"current_score", "value", "cumulative"}
    for k, v in d.items():
        if k in score_fields:
            d[k] = nuclear_clamp(v)
        elif isinstance(v, dict):
            d[k] = sanitize_response(v)
    return d


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
    global env
    if env is None:
        env = SmartContractAuditEnv()
    return env


def reinit_env() -> SmartContractAuditEnv:
    global env
    env = SmartContractAuditEnv()
    return env


# ───────────────────────────────────────────────────────────────
# 24/7 FREE KEEP-ALIVE: self-ping background thread
# ───────────────────────────────────────────────────────────────
KEEP_ALIVE_INTERVAL = 240

def _keep_alive_worker():
    time.sleep(20)
    port = int(os.getenv("PORT", 7860))
    url  = f"http://localhost:{port}/health"
    ping_count = 0
    while True:
        try:
            resp = http_requests.get(url, timeout=10)
            ping_count += 1
            if ping_count % 10 == 0:
                uptime = round((time.time() - START_TIME) / 3600, 2)
                print(f"[KEEP-ALIVE] ping #{ping_count} OK | uptime={uptime}h | status={resp.status_code}", flush=True)
        except Exception as e:
            print(f"[KEEP-ALIVE] ping failed: {e}", flush=True)
        time.sleep(KEEP_ALIVE_INTERVAL)


def _warmup_worker():
    time.sleep(5)
    try:
        e = get_env()
        for task_id in ["easy", "medium", "hard"]:
            e.reset(task_id=task_id)
        print("[WARMUP] All 3 tasks pre-initialized and ready.", flush=True)
    except Exception as ex:
        print(f"[WARMUP] failed: {ex}", flush=True)


@app.on_event("startup")
def startup_event():
    ka_thread = threading.Thread(target=_keep_alive_worker, daemon=True, name="keep-alive")
    ka_thread.start()
    wu_thread = threading.Thread(target=_warmup_worker, daemon=True, name="warmup")
    wu_thread.start()
    print("[STARTUP] Keep-alive (4min interval) + warmup threads started.", flush=True)


# ── Exception handlers ──────────────────────────────────────────────────────────
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


# ── Health ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": "smart-contract-audit-env",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "tasks_available": VALID_TASKS,
        "keep_alive": "active"
    }


# ── Root ───────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "Smart Contract Audit Environment",
        "version": "1.0.0",
        "tasks": VALID_TASKS,
        "endpoints": ["/reset", "/step", "/state", "/health", "/tasks", "/docs"],
        "usage": "POST /reset?task_id=easy to start, POST /step?task_id=easy with Action body to audit",
        "keep_alive": "self-ping every 4 minutes - runs 24/7"
    }


# ── Tasks list ────────────────────────────────────────────────────────────
@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "easy",   "difficulty": "easy",   "vulnerabilities": 1, "description": "Find reentrancy in VulnerableBank"},
            {"id": "medium", "difficulty": "medium", "vulnerabilities": 3, "description": "Find 3 vulns in DeFiVault"},
            {"id": "hard",   "difficulty": "hard",   "vulnerabilities": 4, "description": "Find 4 vulns in ComplexDeFi"}
        ]
    }


# ── Reset ───────────────────────────────────────────────────────────────
@app.post("/reset")
def reset(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}")
    try:
        obs = get_env().reset(task_id=task_id)
        return sanitize_response(obs.dict())
    except Exception:
        obs = reinit_env().reset(task_id=task_id)
        return sanitize_response(obs.dict())


# ── Step ───────────────────────────────────────────────────────────────
@app.post("/step")
def step(action: Action, task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}")

    action.findings = (action.findings or [])[:20]
    action.severity = (action.severity or [])[:20]
    action.vulnerable_lines = (action.vulnerable_lines or [])[:20]
    action.explanation = action.explanation or ""

    try:
        e = get_env()
        if e.states.get(task_id, {}).get("step_count", 0) >= 5:
            e.reset(task_id=task_id)
        result = e.step(action=action, task_id=task_id)
        return sanitize_response(result.dict())
    except Exception as ex:
        try:
            e = reinit_env()
            e.reset(task_id=task_id)
            result = e.step(action=action, task_id=task_id)
            return sanitize_response(result.dict())
        except Exception as ex2:
            raise HTTPException(status_code=500, detail=f"Step failed: {str(ex2)}")


# ── State ───────────────────────────────────────────────────────────────
@app.get("/state")
def state(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id '{task_id}'. Choose from: {VALID_TASKS}")
    try:
        obs = get_env().state(task_id=task_id)
        return sanitize_response(obs.dict())
    except Exception:
        e = reinit_env()
        e.reset(task_id=task_id)
        return sanitize_response(e.state(task_id=task_id).dict())


# ── Legacy ───────────────────────────────────────────────────────────────
@app.post("/audit")
def audit(action: Action, task_id: str = "easy"):
    return step(action=action, task_id=task_id)


# ── Entry point ────────────────────────────────────────────────────────────
def main():
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 7860)),
        reload=False,
        workers=1,
        timeout_keep_alive=75
    )


if __name__ == "__main__":
    main()
