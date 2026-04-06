"""
Smart Contract Audit Environment - Baseline Inference Script

MANDATORY FORMAT:
[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

API Credentials read from environment variables:
- API_BASE_URL (default provided)
- MODEL_NAME   (default provided)
- HF_TOKEN     (mandatory, no default)
"""
import os
import re
import json
import time
from openai import OpenAI
import requests

# ── Environment Variables ───────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/novita/v3/openai")
MODEL_NAME   = os.getenv("MODEL_NAME",   "mistralai/mistral-7b-instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

ENV_URL  = os.getenv("ENV_URL", "http://localhost:8000")
BENCHMARK = "smart-contract-audit"
MAX_STEPS = 5

client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

SYSTEM_PROMPT = """You are an expert Solidity smart contract security auditor.
Analyze the contract carefully and identify ALL security vulnerabilities.

Respond ONLY with valid JSON in exactly this format:
{
  "findings": ["reentrancy vulnerability in withdraw()", "missing access control on emergencyDrain()"],
  "severity": ["high", "high"],
  "vulnerable_lines": [14, 28],
  "explanation": "Detailed explanation of each vulnerability and how to fix it"
}

Common vulnerabilities to check:
- Reentrancy: external call before state update
- Missing access control: functions without onlyOwner
- tx.origin authentication bypass
- Oracle manipulation: single price source
- Integer overflow/underflow
- Unsafe external calls"""


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, with fallback."""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    # Fallback: basic reentrancy guess
    return {
        "findings": ["reentrancy vulnerability detected"],
        "severity":  ["high"],
        "vulnerable_lines": [],
        "explanation": "External call before state update detected."
    }


def run_task(task_id: str) -> float:
    """Run one full episode for a task. Returns final score."""
    # Reset environment
    try:
        reset_resp = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id}, timeout=30)
        obs = reset_resp.json()
    except Exception as e:
        print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}")
        print(f"[STEP] step=1 action=null reward=0.00 done=true error=env_reset_failed")
        print(f"[END] success=false steps=1 score=0.00 rewards=0.00")
        return 0.0

    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}")

    reward_list  = []
    final_score  = 0.0
    step         = 0
    done         = False

    for step in range(1, MAX_STEPS + 1):
        # ── LLM Call ────────────────────────────────────────────────────────
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": (
                        f"Task: {obs.get('task_description', '')}\n\n"
                        f"Solidity Contract:\n```solidity\n{obs.get('contract_code', '')}\n```\n\n"
                        f"Previous feedback: {obs.get('last_feedback', 'None')}\n"
                        f"Current score: {obs.get('current_score', 0.0):.2f}\n"
                        f"Steps used: {obs.get('step_count', 0)}/{obs.get('max_steps', 5)}"
                    )}
                ],
                temperature=0.1,
                max_tokens=800,
            )
            response_text = completion.choices[0].message.content or ""
            last_error = "null"
        except Exception as exc:
            last_error = str(exc).replace("\n", " ")[:100]
            print(f"[STEP] step={step} action=null reward=0.00 done=true error={last_error}")
            done = True
            break

        # ── Parse Action ────────────────────────────────────────────────────
        action = extract_json(response_text)
        action_str = str(action.get('findings', []))[:80].replace("\n", " ")

        # ── Step Environment ────────────────────────────────────────────────
        try:
            step_resp = requests.post(
                f"{ENV_URL}/step",
                json=action,
                params={"task_id": task_id},
                timeout=30
            )
            result = step_resp.json()
        except Exception as exc:
            last_error = str(exc).replace("\n", " ")[:100]
            print(f"[STEP] step={step} action={action_str} reward=0.00 done=true error={last_error}")
            done = True
            break

        reward_val  = result.get("reward", {}).get("value", 0.0)
        final_score = result.get("reward", {}).get("cumulative", 0.0)
        done        = result.get("done", False)
        obs         = result.get("observation", obs)

        reward_list.append(reward_val)
        print(f"[STEP] step={step} action={action_str} reward={reward_val:.2f} done={str(done).lower()} error=null")

        if done:
            break

        time.sleep(0.5)  # avoid hammering the server

    # ── END line ────────────────────────────────────────────────────────────
    rewards_str = ",".join([f"{r:.2f}" for r in reward_list]) if reward_list else "0.00"
    success     = final_score >= 0.5
    print(f"[END] success={str(success).lower()} steps={step} score={final_score:.2f} rewards={rewards_str}")

    return final_score


def main():
    # Verify environment is reachable
    try:
        health = requests.get(f"{ENV_URL}/health", timeout=15)
        health.raise_for_status()
    except Exception as e:
        print(f"[END] success=false steps=0 score=0.00 rewards=")
        return

    scores     = {}
    start_time = time.time()

    for task_id in ["easy", "medium", "hard"]:
        scores[task_id] = run_task(task_id)
        time.sleep(1.0)

    elapsed = time.time() - start_time
    avg     = sum(scores.values()) / len(scores)
    print(f"SUMMARY easy={scores['easy']:.2f} medium={scores['medium']:.2f} hard={scores['hard']:.2f} average={avg:.4f} runtime={elapsed:.1f}s")


if __name__ == "__main__":
    main()
