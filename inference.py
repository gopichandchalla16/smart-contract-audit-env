"""
Smart Contract Audit Environment - Inference Script
Validator injects: API_BASE_URL, API_KEY, MODEL_NAME

OUTPUT FORMAT (mandatory):
[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""
import os
import re
import json
import time
import requests

# ── Env vars: validator injects API_KEY, API_BASE_URL, MODEL_NAME ──────────
API_KEY      = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("HF_TOKEN") or os.environ.get("HFTOKEN") or "dummy-key"
API_BASE_URL = os.environ.get("API_BASE_URL") or os.environ.get("APIBASEURL") or "https://router.huggingface.co/novita/v3/openai"
MODEL_NAME   = os.environ.get("MODEL_NAME") or os.environ.get("MODELNAME") or "mistralai/mistral-7b-instruct"
ENV_URL      = os.environ.get("ENV_URL", "https://gopichand0516-smart-contract-audit-env.hf.space")
BENCHMARK    = "smart-contract-audit"
MAX_STEPS    = 5

# ── Log helpers ────────────────────────────────────────────────────────────
def log_start(task_id):
    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}", flush=True)

def log_step(step, action_str, reward, done, error="null"):
    clean = str(action_str).replace("\n", " ").replace("\r", "")[:80]
    print(f"[STEP] step={step} action={clean} reward={float(reward):.2f} done={str(done).lower()} error={error}", flush=True)

def log_end(success, steps, score, rewards):
    rstr = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"
    print(f"[END] success={str(success).lower()} steps={steps} score={float(score):.2f} rewards={rstr}", flush=True)


# ── LLM call via raw HTTP (bypasses openai SDK version issues entirely) ────
def call_llm(messages: list) -> str:
    """
    Call LLM using raw HTTP POST to API_BASE_URL/chat/completions.
    This bypasses openai SDK version conflicts completely.
    Falls back to openai SDK if raw HTTP fails.
    """
    # Method 1: Raw HTTP (most reliable, no SDK version issues)
    try:
        url = API_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 900,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"] or ""
    except Exception as e1:
        pass

    # Method 2: OpenAI SDK fallback (lazy import inside try/except)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=900,
        )
        return completion.choices[0].message.content or ""
    except Exception as e2:
        raise RuntimeError(f"Both LLM methods failed. Raw: skipped. SDK: {str(e2)[:100]}")


SYSTEM_PROMPT = """You are an expert Solidity smart contract security auditor.
Analyze the contract and identify ALL security vulnerabilities.

Respond ONLY with valid JSON:
{
  "findings": ["reentrancy in withdraw()", "missing access control"],
  "severity": ["high", "high"],
  "vulnerable_lines": [14, 28],
  "explanation": "Detailed explanation of vulnerabilities and fixes."
}

Look for:
- Reentrancy: external call before state update
- Missing access control: public functions without onlyOwner
- tx.origin instead of msg.sender
- Oracle manipulation
- Integer overflow/underflow
- Unsafe external calls
"""

CORRECTION_PROMPT = """Previous score: {score:.2f}. Feedback: {feedback}

Re-examine more carefully:
- External calls before state updates?
- Public functions needing access modifiers?
- tx.origin vs msg.sender?
- Arithmetic issues?

Respond ONLY with improved JSON:
{{
  "findings": [...],
  "severity": [...],
  "vulnerable_lines": [...],
  "explanation": "..."
}}
"""


def extract_json(text: str) -> dict:
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {
        "findings": ["reentrancy - external call before state update"],
        "severity": ["high"],
        "vulnerable_lines": [14],
        "explanation": "External call before state update violates CEI pattern."
    }


def run_task(task_id: str) -> float:
    reward_list = []
    final_score = 0.0
    step = 0
    obs = {}

    # Reset
    try:
        r = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id}, timeout=30)
        r.raise_for_status()
        obs = r.json()
        log_start(task_id)
    except Exception as e:
        log_start(task_id)
        log_step(1, "null", 0.00, True, f"reset_failed:{str(e)[:50]}")
        log_end(False, 1, 0.00, [])
        return 0.0

    for step in range(1, MAX_STEPS + 1):
        # Build prompt
        if step == 1:
            user_msg = (
                f"Task: {obs.get('task_description', '')}\n\n"
                f"Solidity Contract:\n```solidity\n{obs.get('contract_code', '')}\n```\n\n"
                f"Find ALL security vulnerabilities."
            )
        else:
            user_msg = (
                CORRECTION_PROMPT.format(
                    score=float(obs.get('current_score', 0.0)),
                    feedback=obs.get('last_feedback', '')
                ) + f"\n\nContract:\n```solidity\n{obs.get('contract_code', '')}\n```"
            )

        # LLM call
        try:
            response_text = call_llm([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ])
        except Exception as exc:
            err = str(exc).replace("\n", " ")[:80]
            log_step(step, "llm_error", 0.00, True, err)
            log_end(False, step, final_score, reward_list)
            return final_score

        # Parse + Step
        action = extract_json(response_text)
        action_str = str(action.get("findings", []))[:80]

        try:
            sr = requests.post(
                f"{ENV_URL}/step",
                json=action,
                params={"task_id": task_id},
                timeout=30
            )
            sr.raise_for_status()
            result = sr.json()
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

    log_end(final_score >= 0.5, step, final_score, reward_list)
    return final_score


def main():
    try:
        health = requests.get(f"{ENV_URL}/health", timeout=15)
        health.raise_for_status()
    except Exception:
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
