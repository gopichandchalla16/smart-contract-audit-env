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

An OpenEnv-compliant reinforcement learning environment where AI agents learn to audit Solidity smart contracts for security vulnerabilities.

## 🌍 Environment Overview

Smart contract auditing is a critical real-world task — billions of dollars in DeFi protocols depend on identifying vulnerabilities like reentrancy, missing access control, and oracle manipulation. This environment trains AI agents to perform security audits autonomously.

## 🎯 Tasks

| Task | Difficulty | Vulnerabilities | Max Steps |
|------|-----------|----------------|----------|
| `easy` | Easy | 1 (Reentrancy) | 5 |
| `medium` | Medium | 3 (Reentrancy, Access Control, tx.origin) | 5 |
| `hard` | Hard | 4 (Reentrancy, Access Control, Oracle Manipulation, Integer Overflow) | 5 |

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Reset environment, get initial observation |
| `/step` | POST | Submit audit action, get reward |
| `/state` | GET | Get current environment state |
| `/docs` | GET | Swagger UI |

## 📥 Observation Space

```json
{
  "task_id": "easy",
  "task_description": "Audit this contract...",
  "contract_code": "pragma solidity...",
  "current_score": 0.0,
  "last_feedback": "",
  "step_count": 0,
  "max_steps": 5
}
```

## 📤 Action Space

```json
{
  "findings": ["reentrancy vulnerability in withdraw()"],
  "severity": ["high"],
  "vulnerable_lines": [14],
  "explanation": "External call before state update allows reentrancy attack"
}
```

## 🏆 Reward Function

- **+1.0** per correctly identified vulnerability (normalized)
- **-0.1** per false positive finding
- **Partial credit** for finding some but not all vulnerabilities
- **No-progress penalty** if score doesn't improve across steps

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

### Run Inference

```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/novita/v3/openai
export MODEL_NAME=mistralai/mistral-7b-instruct
export ENV_URL=http://localhost:8000
python inference.py
```

## 📊 Baseline Scores

| Task | Score | Model |
|------|-------|-------|
| easy | 0.90 | Mistral-7B-Instruct |
| medium | 0.67 | Mistral-7B-Instruct |
| hard | 0.50 | Mistral-7B-Instruct |

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://router.huggingface.co/novita/v3/openai` | LLM API endpoint |
| `MODEL_NAME` | `mistralai/mistral-7b-instruct` | Model to use |
| `HF_TOKEN` | required | HuggingFace API token |
| `ENV_URL` | `http://localhost:8000` | Environment server URL |
