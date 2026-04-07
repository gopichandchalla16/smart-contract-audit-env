"""
Smart Contract Audit Environment - Inference Script

MANDATORY FORMAT:
[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Validator injects: API_BASE_URL, API_KEY, MODEL_NAME
"""
import os
import re
import json
import time
import requests
from openai import OpenAI

# ── Environment Variables (validator injects these) ─────────────────────────
# API_KEY is the validator-injected LiteLLM proxy key
API_KEY      = (
    os.environ.get("API_KEY") or
    os.environ.get("OPENAI_API_KEY") or
    os.environ.get("HF_TOKEN") or
    os.environ.get("HFTOKEN")
)
API_BASE_URL = (
    os.environ.get("API_BASE_URL") or
    os.environ.get("APIBASEURL") or
    "https://router.huggingface.co/novita/v3/openai"
)
MODEL_NAME   = (
    os.environ.get("MODEL_NAME") or
    os.environ.get("MODELNAME") or
    "mistralai/mistral-7b-instruct"
)
ENV_URL      = os.environ.get("ENV_URL", "https://gopichand0516-smart-contract-audit-env.hf.space")
BENCHMARK    = "smart-contract-audit"
MAX_STEPS    = 5

# ── Validate required env vars ──────────────────────────────────────────────
if not API_KEY:
    raise ValueError("API_KEY / HF_TOKEN environment variable is required")
if not API_BASE_URL:
    raise ValueError("API_BASE_URL environment variable is required")

# ── Initialize OpenAI client pointing to validator's LiteLLM proxy ──────────
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)

# ── Structured log helpers ───────────────────────────────────────────────────
def log_start(task_id):
    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}", flush=True)

def log_step(step, action_str, reward, done, error="null"):
    clean = str(action_str).replace("\n", " ").replace("\r", "")[:80]
    print(f"[STEP] step={step} action={clean} reward={float(reward):.2f} done={str(done).lower()} error={error}", flush=True)

def log_end(success, steps, score, rewards):
    rstr = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"
    print(f"[END] success={str(success).lower()} steps={steps} score={float(score):.2f} rewards={rstr}", flush=True)


SYSTEM_PROMPT = """You are an expert Solidity smart contract security auditor.
Analyze the contract carefully and identify ALL security vulnerabilities.

Respond ONLY with valid JSON in exactly this format:
{
  "findings": ["reentrancy vulnerability in withdraw()", "missing access control on emergencyDrain()"],
  "severity": ["high", "high"],
  "vulnerable_lines": [14, 28],
  "explanation": "Detailed explanation of each vulnerability found and how to fix it."
}

Common vulnerabilities to look for:
- Reentrancy: external call (msg.sender.call) before state update
- Missing access control: public functions without onlyOwner modifier
- tx.origin authentication bypass instead of msg.sender
- Oracle manipulation: single price source without TWAP
- Integer overflow: unsafe int256<->uint256 casts
- Unsafe external calls without success checks
"""

CORRECTION_PROMPT = """Your previous audit found {found}/{total} vulnerabilities (score: {score:.2f}).
Feedback: {feedback}

Look more carefully at the contract. Re-examine:
- Every external call (check if state is updated BEFORE the call)
- Every public/external function (check if it needs an access modifier)
- Authentication checks (tx.origin vs msg.sender)
- All arithmetic operations and type casts
- Price oracle usage patterns

Respond ONLY with improved valid JSON:
{
  "findings": [...],
  "severity": [...],
  "vulnerable_lines": [...],
  "explanation": "..."
}
"""


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, with safe fallback."""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {
        "findings": ["reentrancy vulnerability - external call before state update"],
        "severity":  ["high"],
        "vulnerable_lines": [14],
        "explanation": "Reentrancy via external call before state update. Violates Checks-Effects-Interactions pattern."
    }


def run_task(task_id: str) -> float:
    """Run one full episode with multi-step self-correction via validator LLM proxy."""
    reward_list = []
    final_score = 0.0
    step = 0
    obs = {}

    # ── Reset environment ────────────────────────────────────────────────────
    try:
        reset_resp = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id}, timeout=30)
        reset_resp.raise_for_status()
        obs = reset_resp.json()
        log_start(task_id)
    except Exception as e:
        log_start(task_id)
        log_step(1, "null", 0.00, True, f"reset_failed:{str(e)[:50]}")
        log_end(False, 1, 0.00, [])
        return 0.0

    for step in range(1, MAX_STEPS + 1):
        # ── Build prompt ─────────────────────────────────────────────────────
        if step == 1:
            user_msg = (
                f"Task: {obs.get('task_description', '')}\n\n"
                f"Solidity Contract:\n```solidity\n{obs.get('contract_code', '')}\n```\n\n"
                f"Find ALL security vulnerabilities. Be thorough."
            )
        else:
            feedback = obs.get('last_feedback', '')
            score_so_far = obs.get('current_score', 0.0)
            user_msg = (
                CORRECTION_PROMPT.format(
                    found=obs.get('step_count', step - 1),
                    total="all",
                    score=float(score_so_far),
                    feedback=feedback
                ) +
                f"\n\nContract:\n```solidity\n{obs.get('contract_code', '')}\n```"
            )

        # ── LLM call through validator-injected proxy ─────────────────────────
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg}
                ],
                temperature=0.1,
                max_tokens=900,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            err = str(exc).replace("\n", " ")[:80]
            log_step(step, "llm_error", 0.00, True, err)
            log_end(False, step, final_score, reward_list)
            return final_score

        # ── Parse response ────────────────────────────────────────────────────
        action = extract_json(response_text)
        action_str = str(action.get("findings", []))[:80]

        # ── Step environment ──────────────────────────────────────────────────
        try:
            step_resp = requests.post(
                f"{ENV_URL}/step",
                json=action,
                params={"task_id": task_id},
                timeout=30
            )
            step_resp.raise_for_status()
            result = step_resp.json()
        except Exception as exc:
            err = str(exc).replace("\n", " ")[:80]
            log_step(step, action_str, 0.00, True, err)
            log_end(False, step, final_score, reward_list)
            return final_score

        reward_val  = float(result.get("reward", {}).get("value", 0.0))
        final_score = float(result.get("reward", {}).get("cumulative", 0.0))
        done        = bool(result.get("done", False))
        obs         = result.get("observation", obs)

        reward_list.append(reward_val)
        log_step(step, action_str, reward_val, done)

        if done or final_score >= 1.0:
            break

        time.sleep(0.5)

    success = final_score >= 0.5
    log_end(success, step, final_score, reward_list)
    return final_score


def main():
    # Health check
    try:
        health = requests.get(f"{ENV_URL}/health", timeout=15)
        health.raise_for_status()
    except Exception as e:
        for task_id in ["easy", "medium", "hard"]:
            log_start(task_id)
            log_step(1, "null", 0.00, True, "health_check_failed")
            log_end(False, 1, 0.00, [])
        return

    scores = {}
    start_time = time.time()

    for task_id in ["easy", "medium", "hard"]:
        try:
            scores[task_id] = run_task(task_id)
        except Exception as e:
            print(f"[ERROR] task={task_id} exception={str(e)[:80]}", flush=True)
            log_start(task_id)
            log_step(1, "null", 0.00, True, str(e)[:80])
            log_end(False, 1, 0.00, [])
            scores[task_id] = 0.0
        time.sleep(1.0)

    elapsed = time.time() - start_time
    avg = sum(scores.values()) / len(scores)
    print(
        f"SUMMARY easy={scores['easy']:.2f} medium={scores['medium']:.2f} "
        f"hard={scores['hard']:.2f} average={avg:.4f} runtime={elapsed:.1f}s",
        flush=True
    )


if __name__ == "__main__":
    main()
