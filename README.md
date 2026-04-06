---
title: Smart Contract Audit Env
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
tags:
  - openenv
  - smart-contracts
  - solidity
  - security
  - reinforcement-learning
  - code-review
  - web3
pinned: false
---

# 🔍 Smart Contract Audit Environment

> An OpenEnv-compliant reinforcement learning environment where AI agents learn to audit Solidity smart contracts for security vulnerabilities — a task that protects **billions of dollars** in live DeFi protocols.

[![HF Space](https://img.shields.io/badge/🤗%20HuggingFace-Space-blue)](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-green)](https://github.com/meta-pytorch/OpenEnv)

---

## 🌍 Why This Environment Matters

Smart contract auditing is one of the most high-stakes tasks in software engineering. In 2023 alone, **$1.8B was lost** to DeFi exploits — reentrancy attacks, oracle manipulation, and broken access control. Human auditors are expensive and scarce. This environment trains AI agents to detect these critical vulnerabilities autonomously, filling a genuine gap in the RL/agent evaluation ecosystem.

---

## 🎯 Tasks

| Task | Difficulty | Contract | Vulnerabilities to Find | Max Steps |
|------|-----------|----------|------------------------|-----------|
| `easy` | 🟢 Easy | VulnerableBank | 1 — Reentrancy | 5 |
| `medium` | 🟡 Medium | DeFiVault | 3 — Reentrancy, Missing Access Control, tx.origin | 5 |
| `hard` | 🔴 Hard | ComplexDeFi | 4 — Integer Overflow, Oracle Manipulation, Reentrancy, Missing Access Control | 5 |

### Task Descriptions

**Easy — VulnerableBank**  
A simple bank contract with a single critical reentrancy flaw in `withdraw()`. The external `.call{value}` happens before the balance state update — a classic exploit pattern. Good baseline for evaluating whether an agent understands the Checks-Effects-Interactions pattern.

**Medium — DeFiVault**  
A DeFi vault with 3 independent vulnerabilities: reentrancy in `withdraw()`, an unguarded `emergencyDrain()` callable by anyone, and `tx.origin` authentication bypass in `adminWithdraw()`. Requires the agent to read the full contract rather than stopping after the first finding.

**Hard — ComplexDeFi**  
A sophisticated lending protocol with 4 vulnerabilities: unsafe int256→uint256 cast causing integer overflow, a single-source price oracle vulnerable to flash loan manipulation, reentrancy during borrow execution, and unprotected `liquidate()`. This task is designed to challenge frontier models — all 4 must be found for a perfect score.

---

## 📐 OpenEnv Spec Compliance

### Observation Space

```json
{
  "task_id": "easy",
  "task_description": "Audit this simple bank contract and find the critical vulnerability.",
  "contract_code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n...",
  "current_score": 0.0,
  "last_feedback": "",
  "step_count": 0,
  "max_steps": 5
}
```

### Action Space

```json
{
  "findings": ["reentrancy vulnerability in withdraw() - external call before state update"],
  "severity": ["high"],
  "vulnerable_lines": [14],
  "explanation": "The withdraw() function calls msg.sender.call before updating balances[msg.sender], violating the Checks-Effects-Interactions pattern and enabling reentrancy."
}
```

### Reward Space

```json
{
  "value": 0.9,
  "cumulative": 0.9,
  "message": "Found 1/1 vulnerabilities. Line bonus: +0.05. Explanation bonus: +0.05.",
  "true_positives": 1,
  "false_positives": 0,
  "missed_vulnerabilities": 0
}
```

---

## 🏆 Reward Function Design

The reward function provides **dense, shaped signal** throughout the episode — not just at the end.

| Component | Value | Notes |
|-----------|-------|-------|
| True positive vulnerability | `+1/N` per vuln | N = total expected vulns |
| False positive penalty | `-0.1` per FP | Capped at -0.3 |
| Correct line reference bonus | `+0.05` per line | Capped at +0.1 |
| Substantive explanation bonus | `+0.05` | Requires >30 chars |
| No-progress penalty | `-0.05` | Applied from step 2+ if delta ≤ 0 |

**Key design choices:**
- Rewards partial progress (agent gets credit for finding 2/4 vulns)
- Penalizes hallucination (false positives hurt the score)
- Incentivizes precision (correct line numbers give bonus)
- Incentivizes reasoning (explanation quality rewarded)
- Penalizes stagnation (same answer repeated across steps costs score)

### Grader — Semantic Matching

Vulnerability matching is **semantic, not keyword-only**. Each vulnerability has a curated synonym set:

- `reentrancy` matches: `"re-entrancy"`, `"CEI violation"`, `"external call before state update"`, `"checks-effects-interactions"`, `"recursive call"`, etc.
- `missing access control` matches: `"unprotected function"`, `"anyone can call"`, `"missing onlyOwner"`, `"no modifier"`, etc.
- `oracle manipulation` matches: `"flash loan attack"`, `"single price source"`, `"price feed manipulation"`, etc.
- `tx.origin` matches: `"origin authentication bypass"`, `"phishing attack"`, `"use msg.sender instead"`, etc.
- `integer overflow` matches: `"unsafe cast"`, `"arithmetic overflow"`, `"unsafe type conversion"`, etc.

This ensures frontier models are not penalized for describing vulnerabilities in natural language.

---

## 📊 Baseline Scores

Baseline agent: `mistralai/mistral-7b-instruct` via HuggingFace Inference Router

| Task | Score | True Positives | False Positives | Notes |
|------|-------|---------------|-----------------|-------|
| easy | 0.90 | 1/1 | 0 | Line bonus applied |
| medium | 0.67 | 2/3 | 0 | tx.origin missed |
| hard | 0.50 | 2/4 | 1 | Oracle + overflow missed |

**Hard task is intentionally frontier-challenging** — Mistral-7B scores 0.50. A stronger model (e.g., GPT-4, Claude 3.5) should score 0.80+.

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Environment info |
| `GET /health` | GET | Health check |
| `POST /reset?task_id=easy` | POST | Reset and get initial observation |
| `POST /step?task_id=easy` | POST | Submit action, receive reward + feedback |
| `GET /state?task_id=easy` | GET | Current environment state |
| `GET /docs` | GET | Swagger UI — interactive API explorer |

---

## 🚀 Setup & Usage

### Run Locally

```bash
git clone https://github.com/gopichandchalla16/smart-contract-audit-env
cd smart-contract-audit-env
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Run with Docker

```bash
docker build -t smart-contract-audit-env .
docker run -p 7860:7860 smart-contract-audit-env
```

### Run Inference Script

```bash
export HF_TOKEN=your_hf_token_here
export API_BASE_URL=https://router.huggingface.co/novita/v3/openai
export MODEL_NAME=mistralai/mistral-7b-instruct
export ENV_URL=http://localhost:8000
python inference.py
```

### Expected Output Format

```
[START] task=easy env=smart-contract-audit-env model=mistralai/mistral-7b-instruct
[STEP] step=1 action=... reward=0.90 done=true error=null
[END] success=true steps=1 score=0.90 rewards=0.90
```

---

## 🔧 Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `API_BASE_URL` | `https://router.huggingface.co/novita/v3/openai` | No | LLM API endpoint |
| `MODEL_NAME` | `mistralai/mistral-7b-instruct` | No | Model identifier |
| `HF_TOKEN` | — | **Yes** | HuggingFace / API key |
| `ENV_URL` | `http://localhost:8000` | No | Environment server URL |

---

## 🗂 Project Structure

```
smart-contract-audit-env/
├── server/
│   ├── app.py                              # FastAPI server (OpenEnv endpoints)
│   └── smart_contract_audit_env_environment.py  # Core env logic + graders
├── models.py                               # Pydantic typed models
├── inference.py                            # Baseline inference script
├── openenv.yaml                            # OpenEnv metadata + spec
├── Dockerfile                              # Containerized deployment
├── requirements.txt                        # Dependencies
└── README.md
```

---

## 🛡 Real-World Impact

This environment directly addresses a real gap:
- **Manual audits cost $50,000–$200,000** per protocol
- **Automated tools miss logic-level bugs** (Slither, MythX focus on patterns, not semantics)
- **An LLM agent trained here** could serve as a first-pass auditor, dramatically reducing cost and time-to-audit for Web3 protocols

---

*Built for the Meta × Scaler OpenEnv Hackathon — April 2026*
