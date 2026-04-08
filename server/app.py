from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys, os, uvicorn, time, threading
import requests as http_requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Action, Observation, StepResult, RewardInfo
from smart_contract_audit_env_environment import SmartContractAuditEnv

START_TIME = time.time()
VALID_TASKS = ["easy", "medium", "hard"]
SCORE_FLOOR = 0.01
SCORE_CEIL  = 0.99

def nuclear_clamp(v) -> float:
    try:
        v = float(v)
    except Exception:
        return SCORE_FLOOR
    if v <= 0.0: return SCORE_FLOOR
    if v >= 1.0: return SCORE_CEIL
    v = int(v * 10000) / 10000.0
    if v <= 0.0: return SCORE_FLOOR
    if v >= 1.0: return SCORE_CEIL
    return v

def sanitize_response(d: dict) -> dict:
    score_fields = {"current_score", "value", "cumulative"}
    for k, v in d.items():
        if k in score_fields:
            d[k] = nuclear_clamp(v)
        elif isinstance(v, dict):
            d[k] = sanitize_response(v)
    return d

app = FastAPI(title="Smart Contract Audit Environment", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

env = SmartContractAuditEnv()

def get_env():
    global env
    if env is None:
        env = SmartContractAuditEnv()
    return env

def reinit_env():
    global env
    env = SmartContractAuditEnv()
    return env

KEEP_ALIVE_INTERVAL = 240

def _keep_alive_worker():
    time.sleep(20)
    port = int(os.getenv("PORT", 7860))
    url = f"http://localhost:{port}/health"
    while True:
        try:
            http_requests.get(url, timeout=10)
        except Exception:
            pass
        time.sleep(KEEP_ALIVE_INTERVAL)

def _warmup_worker():
    time.sleep(5)
    try:
        e = get_env()
        for t in ["easy", "medium", "hard"]:
            e.reset(task_id=t)
        print("[WARMUP] All 3 tasks ready.", flush=True)
    except Exception as ex:
        print(f"[WARMUP] failed: {ex}", flush=True)

@app.on_event("startup")
def startup_event():
    threading.Thread(target=_keep_alive_worker, daemon=True).start()
    threading.Thread(target=_warmup_worker, daemon=True).start()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.get("/health")
def health():
    return {"status": "ok", "environment": "smart-contract-audit-env",
            "version": "1.0.0", "uptime_seconds": round(time.time() - START_TIME, 1),
            "tasks_available": VALID_TASKS, "keep_alive": "active"}

@app.get("/")
def root():
    return {"name": "Smart Contract Audit Environment", "version": "1.0.0",
            "tasks": VALID_TASKS, "endpoints": ["/reset", "/step", "/state", "/health", "/tasks"]}

@app.get("/tasks")
def list_tasks():
    return {"tasks": [
        {"id": "easy",   "difficulty": "easy",   "vulnerabilities": 1},
        {"id": "medium", "difficulty": "medium", "vulnerabilities": 3},
        {"id": "hard",   "difficulty": "hard",   "vulnerabilities": 4}
    ]}

@app.post("/reset")
def reset(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id. Choose from: {VALID_TASKS}")
    try:
        obs = get_env().reset(task_id=task_id)
        return sanitize_response(obs.dict())
    except Exception:
        obs = reinit_env().reset(task_id=task_id)
        return sanitize_response(obs.dict())

@app.post("/step")
def step(action: Action, task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id. Choose from: {VALID_TASKS}")
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
    except Exception:
        try:
            e = reinit_env()
            e.reset(task_id=task_id)
            result = e.step(action=action, task_id=task_id)
            return sanitize_response(result.dict())
        except Exception as ex2:
            raise HTTPException(status_code=500, detail=str(ex2))

@app.get("/state")
def state(task_id: str = "easy"):
    if task_id not in VALID_TASKS:
        raise HTTPException(status_code=400, detail=f"Invalid task_id. Choose from: {VALID_TASKS}")
    try:
        obs = get_env().state(task_id=task_id)
        return sanitize_response(obs.dict())
    except Exception:
        e = reinit_env()
        e.reset(task_id=task_id)
        return sanitize_response(e.state(task_id=task_id).dict())

@app.post("/audit")
def audit(action: Action, task_id: str = "easy"):
    return step(action=action, task_id=task_id)

def main():
    uvicorn.run("server.app:app", host="0.0.0.0",
                port=int(os.getenv("PORT", 7860)), reload=False, workers=1)

if __name__ == "__main__":
    main()
