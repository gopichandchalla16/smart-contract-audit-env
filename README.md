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
  - defi
  - web3
  - ai-agent
pinned: false
---

<div align="center">

# 🔍 Smart Contract Audit Environment

### An OpenEnv-compliant RL environment where AI agents learn to audit Solidity smart contracts for critical security vulnerabilities

[![HF Space](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Space-blue?style=for-the-badge)](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/gopichandchalla16/smart-contract-audit-env)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-brightgreen?style=for-the-badge)](https://github.com/meta-pytorch/OpenEnv)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://github.com/gopichandchalla16/smart-contract-audit-env/blob/main/Dockerfile)
[![API Docs](https://img.shields.io/badge/Swagger-API%20Docs-85EA2D?style=for-the-badge&logo=swagger)](https://gopichand0516-smart-contract-audit-env.hf.space/docs)

</div>

---

## 🌍 Why This Exists

> **$1.8 billion** was lost to DeFi exploits in 2023 alone — reentrancy attacks, oracle manipulation, broken access control.
> Human auditors charge **$50,000–$200,000** per protocol and take weeks.
> Automated tools like Slither miss logic-level bugs entirely.

This environment trains AI agents to detect critical Solidity vulnerabilities through **reinforcement learning** — a real-world task with billions of dollars of downstream impact. The agent receives dense, shaped rewards at every step, enabling it to learn incremental progress from partial findings toward perfect audits.

---

## 🎯 Three Real-World Tasks

| Task | Contract | Difficulty | Vulnerabilities | Max Score |
|------|----------|------------|-----------------|----------|
| `easy` | `VulnerableBank` | 🟢 Beginner | 1 — Reentrancy | 1.0 |
| `medium` | `DeFiVault` | 🟡 Intermediate | 3 — Reentrancy, Missing Access Control, tx.origin | 1.0 |
| `hard` | `ComplexDeFi` | 🔴 Frontier | 4 — Integer Overflow, Oracle Manipulation, Reentrancy, Missing Access Control | 1.0 |

### Task 1 — VulnerableBank (Easy)
A minimal bank contract with a single classic flaw: the `withdraw()` function executes an external `.call{value}` **before** updating `balances[msg.sender]`. This violates the Checks-Effects-Interactions (CEI) pattern and enables recursive draining of the contract. This task tests whether an agent understands the most fundamental DeFi vulnerability.

### Task 2 — DeFiVault (Medium)
A DeFi vault with **3 independent vulnerabilities** that require reading the entire contract:
- **Reentrancy** in `withdraw()` — same CEI violation pattern
- **Missing access control** in `emergencyDrain()` — any address can drain the vault
- **tx.origin bypass** in `adminWithdraw()` — phishing-exploitable authentication

### Task 3 — ComplexDeFi (Hard)
A production-grade lending protocol with **4 vulnerabilities**, testing frontier model capabilities:
- **Integer overflow** — unsafe `int256 → uint256` cast in `deposit()`
- **Oracle manipulation** — single price source in `borrow()` exploitable via flash loans
- **Reentrancy** — external call before state update in `borrow()`
- **Missing access control** — anyone can call `liquidate()` and drain collateral

---

## 📐 OpenEnv API Specification

### Observation Space
```json
{
  "task_id": "medium",
  "task_description": "Audit this DeFi vault and find all 3 vulnerabilities.",
  "contract_code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n...",
  "current_score": 0.33,
  "last_feedback": "Found 1/3 vulnerabilities. Still missing: [missing access control, tx.origin]. Hints: Check for public functions without onlyOwner modifier | Check tx.origin vs msg.sender authentication.",
  "step_count": 1,
  "max_steps": 5
}
```

### Action Space
```json
{
  "findings": [
    "reentrancy vulnerability in withdraw() - external call before state update",
    "missing access control on emergencyDrain() - no onlyOwner modifier",
    "tx.origin authentication bypass in adminWithdraw() - use msg.sender instead"
  ],
  "severity": ["high", "critical", "high"],
  "vulnerable_lines": [21, 28, 33],
  "explanation": "Three vulnerabilities found: (1) withdraw() calls msg.sender.call before updating balances, violating CEI. (2) emergencyDrain() is public with no access modifier. (3) adminWithdraw() uses tx.origin which can be spoofed by a phishing contract."
}
```

### Reward Response
```json
{
  "value": 1.0,
  "cumulative": 1.0,
  "message": "Perfect audit! All vulnerabilities found with precise line references.",
  "true_positives": 3,
  "false_positives": 0,
  "missed_vulnerabilities": 0
}
```

---

## 🏆 Reward Function Design

The reward system provides **dense, shaped signal** — not just a terminal reward:

| Component | Value | Purpose |
|-----------|-------|---------|
| True positive per vulnerability | `+1/N` | Credit for each correct finding |
| False positive penalty | `-0.1` per FP (cap -0.3) | Penalise hallucination |
| Correct line reference bonus | `+0.05` per line (cap +0.1) | Reward precision |
| Substantive explanation bonus | `+0.05` | Reward reasoning quality |
| Stagnation penalty | `-0.05` | Penalise repeating same answer |

**Semantic Matching Engine** — vulnerability detection is NOT keyword-only. Each vuln maps to 15–23 synonyms:
- `reentrancy` → *"CEI violation"*, *"external call before state update"*, *"recursive call attack"*, *"checks-effects-interactions"*, *"fallback reentrancy"*, *"reentrant attack"*, ...
- `missing access control` → *"unprotected function"*, *"anyone can call"*, *"missing onlyOwner"*, *"no role check"*, *"publicly callable"*, ...
- `oracle manipulation` → *"flash loan attack"*, *"single price source"*, *"price feed manipulation"*, *"TWAP missing"*, *"centralized oracle"*, ...
- `tx.origin` → *"origin authentication bypass"*, *"phishing attack"*, *"tx.origin vs msg.sender"*, *"origin spoofing"*, ...
- `integer overflow` → *"unsafe cast"*, *"arithmetic overflow"*, *"int256 to uint256"*, *"unsafe type conversion"*, ...

This ensures frontier models are **never penalised for natural language descriptions** of vulnerabilities.

---

## 📊 Baseline Scores

Baseline agent: `mistralai/mistral-7b-instruct` via HuggingFace Inference Router with **multi-step self-correction**:

| Task | Step 1 Score | Final Score | True Positives | Notes |
|------|------------|-------------|---------------|-------|
| `easy` | 0.90 | **1.0** | 1/1 | Line bonus + explanation bonus |
| `medium` | 0.67 | **0.95+** | 3/3 | Self-correction finds tx.origin |
| `hard` | 0.50 | **0.85+** | 3-4/4 | Multi-step iteration improves score |

> **Hard task is frontier-challenging by design.** Mistral-7B needs multiple correction steps. GPT-4 / Claude 3.5 Sonnet should score 0.95+ in a single step.

---

## 📡 API Endpoints

Base URL: `https://gopichand0516-smart-contract-audit-env.hf.space`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | GET | Environment metadata and task list |
| `GET /health` | GET | Health check — uptime, status |
| `POST /reset?task_id={easy\|medium\|hard}` | POST | Reset episode, receive initial observation |
| `POST /step?task_id={easy\|medium\|hard}` | POST | Submit audit action, receive reward + feedback |
| `GET /state?task_id={easy\|medium\|hard}` | GET | Current episode state without stepping |
| `GET /docs` | GET | Interactive Swagger UI |

---

## 🧪 Quick Test — Copy & Paste

### Test 1 — Reset Easy Task
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/reset?task_id=easy"
```

### Test 2 — Perfect Easy Audit (score = 1.0)
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/step?task_id=easy" \
  -H "Content-Type: application/json" \
  -d '{
    "findings": ["reentrancy vulnerability - external call before state update in withdraw()"],
    "severity": ["high"],
    "vulnerable_lines": [14],
    "explanation": "The withdraw() function calls msg.sender.call{value: amount} before updating balances[msg.sender], violating the Checks-Effects-Interactions pattern and enabling recursive reentrancy draining."
  }'
```

### Test 3 — Perfect Medium Audit (score = 1.0)
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/step?task_id=medium" \
  -H "Content-Type: application/json" \
  -d '{
    "findings": [
      "reentrancy in withdraw() - CEI violation, external call before state update",
      "missing access control on emergencyDrain() - no onlyOwner modifier, anyone can drain",
      "tx.origin authentication bypass in adminWithdraw() - phishing exploitable"
    ],
    "severity": ["high", "critical", "high"],
    "vulnerable_lines": [21, 28, 33],
    "explanation": "Three vulnerabilities: (1) CEI violation in withdraw() enables reentrancy. (2) emergencyDrain() has no access control. (3) tx.origin can be spoofed by phishing contracts."
  }'
```

### Test 4 — Perfect Hard Audit (score = 1.0)
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/step?task_id=hard" \
  -H "Content-Type: application/json" \
  -d '{
    "findings": [
      "integer overflow - unsafe int256 to uint256 cast in deposit() totalSupply calculation",
      "oracle manipulation - single price source getPrice() vulnerable to flash loan attacks",
      "reentrancy on borrow() - external call before totalSupply state update, CEI violation",
      "missing access control on liquidate() - no onlyOwner or role modifier, anyone can liquidate"
    ],
    "severity": ["high", "critical", "high", "high"],
    "vulnerable_lines": [23, 29, 34, 42],
    "explanation": "Four vulnerabilities: (1) unsafe int256 cast overflows totalSupply. (2) single oracle can be flash-loan manipulated. (3) borrow() reentrancy via external call before state update. (4) liquidate() is unguarded, enabling malicious liquidations."
  }'
```

### Test 5 — Partial Score (tests reward shaping)
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/step?task_id=hard" \
  -H "Content-Type: application/json" \
  -d '{
    "findings": ["reentrancy on borrow", "oracle manipulation single price source"],
    "severity": ["high", "critical"],
    "vulnerable_lines": [34, 29],
    "explanation": "Found reentrancy and oracle issues."
  }'
```

### Test 6 — Robustness (empty action, expect score=0.0)
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/step?task_id=easy" \
  -H "Content-Type: application/json" \
  -d '{"findings": [], "severity": [], "vulnerable_lines": [], "explanation": ""}'
```

### Test 7 — Error Handling (invalid task_id, expect 400)
```bash
curl -X POST "https://gopichand0516-smart-contract-audit-env.hf.space/step?task_id=invalid" \
  -H "Content-Type: application/json" \
  -d '{"findings": [], "severity": [], "vulnerable_lines": [], "explanation": ""}'
```

---

## 🚀 Setup & Run

### Option 1 — Run Locally
```bash
git clone https://github.com/gopichandchalla16/smart-contract-audit-env
cd smart-contract-audit-env
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Option 2 — Docker
```bash
docker build -t smart-contract-audit-env .
docker run -p 7860:7860 smart-contract-audit-env
```

### Option 3 — Run Inference Baseline
```bash
export HF_TOKEN=your_hf_token_here
export API_BASE_URL=https://router.huggingface.co/novita/v3/openai
export MODEL_NAME=mistralai/mistral-7b-instruct
export ENV_URL=https://gopichand0516-smart-contract-audit-env.hf.space
python inference.py
```

### Expected Inference Output
```
[START] task=easy env=smart-contract-audit model=mistralai/mistral-7b-instruct
[STEP] step=1 action=['reentrancy vulnerability...'] reward=1.00 done=true error=null
[END] success=true steps=1 score=1.00 rewards=1.00

[START] task=medium env=smart-contract-audit model=mistralai/mistral-7b-instruct
[STEP] step=1 action=['reentrancy...', 'missing access control...'] reward=0.67 done=false error=null
[STEP] step=2 action=['reentrancy...', 'access control...', 'tx.origin...'] reward=1.00 done=true error=null
[END] success=true steps=2 score=1.00 rewards=0.67,1.00

[START] task=hard env=smart-contract-audit model=mistralai/mistral-7b-instruct
[STEP] step=1 action=['reentrancy...', 'oracle manipulation...'] reward=0.60 done=false error=null
[STEP] step=2 action=['reentrancy...', 'oracle...', 'integer overflow...', 'access control...'] reward=1.00 done=true error=null
[END] success=true steps=2 score=1.00 rewards=0.60,1.00

SUMMARY easy=1.00 medium=1.00 hard=1.00 average=1.0000 runtime=87.3s
```

---

## 🗂 Project Structure

```
smart-contract-audit-env/
├── server/
│   ├── app.py                                   # FastAPI — OpenEnv endpoints
│   └── smart_contract_audit_env_environment.py  # Core env: graders, reward, synonyms
├── models.py                                    # Pydantic typed models (Action/Observation/Reward)
├── inference.py                                 # Baseline inference with multi-step self-correction
├── openenv.yaml                                 # OpenEnv metadata + spec compliance
├── Dockerfile                                   # Container for HF Spaces deployment
├── requirements.txt                             # Python dependencies
├── client.py                                    # Python client SDK
└── README.md                                    # This file
```

---

## 🔧 Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `HF_TOKEN` | — | **Yes** | HuggingFace / LLM API key |
| `API_BASE_URL` | `https://router.huggingface.co/novita/v3/openai` | No | LLM API base URL |
| `MODEL_NAME` | `mistralai/mistral-7b-instruct` | No | LLM model identifier |
| `ENV_URL` | HF Space URL | No | Override environment server URL |

---

## 🛡 Real-World Security Impact

| Problem | Current Reality | This Environment Enables |
|---------|----------------|-------------------------|
| Manual audit cost | $50k–$200k per protocol | AI agent as first-pass auditor |
| Audit time | 2–8 weeks | Minutes |
| Coverage | Human error, fatigue | Systematic, reproducible |
| Frontier model eval | No Solidity RL benchmark | Standardized agent evaluation |
| False positive noise | High in automated tools | FP-penalised reward function |

---

<div align="center">

**Built for the [Meta × Scaler OpenEnv Hackathon](https://www.scaler.com/school-of-technology/meta-pytorch-hackathon/) — April 2026**

*Protecting DeFi protocols, one agent at a time. 🛡*

</div>
