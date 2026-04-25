---
title: Smart Contract Audit Env
emoji: 🔐
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# 🔐 Smart Contract Audit Environment + GRPO RL Training

[![HF Space](https://img.shields.io/badge/🤗%20HuggingFace-Space-yellow)](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)](https://github.com/gopichandchalla16/smart-contract-audit-env/blob/main/Dockerfile)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-green)](https://github.com/gopichandchalla16/smart-contract-audit-env/blob/main/openenv.yaml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)
[![GRPO Training](https://img.shields.io/badge/GRPO-10.9x%20Improvement-orange)](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo)
[![Model](https://img.shields.io/badge/🤗%20Model-Qwen2.5--3B--GRPO-blue)](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo)

> **Meta OpenEnv Hackathon (Scaler × Meta PyTorch)** — Production-grade reinforcement learning environment for automated smart contract security auditing. Trained with GRPO + QLoRA achieving **10.9× reward improvement** over 200 steps.

---

## 🔗 Submission Links

| Resource | Link |
|---|---|
| 🤗 **HF Space (Environment)** | https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env |
| 🤖 **Trained GRPO Model** | https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo |
| 📓 **Colab Training Notebook** | https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link |
| 💻 **GitHub Repository** | https://github.com/gopichandchalla16/smart-contract-audit-env |
| 📝 **Blog Post** | https://github.com/gopichandchalla16/smart-contract-audit-env/blob/main/BLOG.md |

---

## 📊 GRPO Training Results — 10.9× Reward Improvement

The agent was trained using **GRPO + QLoRA** on `Qwen2.5-3B-Instruct` for **200 steps** (~85 minutes on T4 GPU).

![Reward Curve](https://raw.githubusercontent.com/gopichandchalla16/smart-contract-audit-env/main/training/reward_curve.png)

| Metric | Value |
|---|---|
| **Baseline reward** (Step 0) | 0.030 |
| **Final reward** (Step 200) | **0.329** |
| **Total Improvement** | **🔥 10.9× from baseline** |
| Training steps | 200 |
| Training time | ~85 minutes (T4 GPU) |
| Model | Qwen2.5-3B-Instruct + QLoRA |
| Trainable parameters | 18.4M / 1.03B (1.78%) |
| GRPO generations per prompt | 4 |
| KL Divergence (final) | ~0.051 (stable) |

### Reward Progression (Step-by-Step)

| Step | Reward | KL Divergence |
|------|--------|---------------|
| 10 | 0.030 | 0.000040 |
| 50 | 0.101 | 0.019485 |
| 100 | 0.187 | 0.030487 |
| 150 | 0.267 | 0.038510 |
| 200 | **0.329** | 0.051547 |

### Reward Components

```
Total Reward = Environment Accuracy  (0.0 – 1.0)
             + Format Quality        (0.0 – 0.3)   ← VULNERABILITY, SEVERITY, LOCATION, IMPACT, FIX
             + Coverage Score        (0.0 – 0.2)   ← mentions impact + remediation
             - False Negative Penalty (−0.2)        ← claiming "no vulnerability" when one exists
             ─────────────────────────────────────
Max Possible Reward: 1.5
```

---

## 🎯 Motivation

**$3.8 billion was lost to smart contract exploits since 2016.** Reentrancy alone drained **$60M in the DAO hack**. Professional audits cost $20,000–$100,000 per engagement and take weeks. Meanwhile, DeFi protocols launch daily with unaudited code.

This environment trains AI agents to perform **expert-level security audits automatically** — detecting reentrancy, oracle manipulation, privilege escalation, and more — at near-zero cost.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenEnv Agent Loop                           │
│                                                                 │
│  ┌──────────┐   /reset    ┌──────────────────────────────────┐  │
│  │ inference│ ──────────► │     FastAPI Server (HF Space)    │  │
│  │   .py    │             │  ┌────────────────────────────┐  │  │
│  │          │   Observation│  │  SmartContractAuditEnv     │  │  │
│  │ Phase 1  │ ◄──────────  │  │                            │  │  │
│  │ Enumerate│             │  │  ┌──────────────────────┐  │  │  │
│  │          │             │  │  │  CONTRACTS dict       │  │  │  │
│  │ Phase 2  │   /step     │  │  │  easy / medium / hard │  │  │  │
│  │ Patterns │ ──────────► │  │  └──────────────────────┘  │  │  │
│  │          │             │  │                            │  │  │
│  │ Phase 3  │   Reward    │  │  _grade() → sophisticated  │  │  │
│  │ Report   │ ◄──────────  │  │  scorer                   │  │  │
│  │ + Merge  │             │  └────────────────────────────┘  │  │
│  └──────────┘             └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 GRPO Training Setup

```python
# Model: Qwen2.5-3B-Instruct (4-bit quantized)
# LoRA: r=16, alpha=16, target: q/k/v/o/gate/up/down projections
# Trainable: 1.78% of parameters (18.4M / 1.03B)

training_config = GRPOConfig(
    output_dir="./smart-contract-audit-rl",
    learning_rate=5e-6,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    max_steps=200,
    num_generations=4,        # GRPO samples 4 responses per prompt
    max_completion_length=350,
    temperature=0.9,
    optim="adamw_8bit",       # memory-efficient
)
```

**How GRPO Works:**
1. Model generates **4 different audit reports** for the same Solidity contract
2. Each gets a reward score from the live environment
3. Model updates to make **high-reward responses more likely**
4. Repeat 200 times → model gets better at auditing

---

## 📐 Environment Specification

### Observation Space

| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Task identifier: `"easy"`, `"medium"`, `"hard"` |
| `task_description` | `str` | Natural language audit brief |
| `contract_code` | `str` | Full Solidity source code to audit |
| `current_score` | `float ∈ (0,1)` | Running score from last step |
| `last_feedback` | `str` | Grader hints guiding next action |
| `step_count` | `int` | Steps taken so far |
| `max_steps` | `int` | Maximum steps allowed (5) |

### Action Space

| Field | Type | Description |
|---|---|---|
| `findings` | `List[str]` | Vulnerability descriptions (one per finding) |
| `severity` | `List[str]` | Severity per finding: `"high"`, `"medium"`, `"low"` |
| `vulnerable_lines` | `List[int]` | Source code line numbers where vulns appear |
| `explanation` | `str` | Technical explanation with attack vector + fix |

---

## 📋 Task Difficulty Table

| Task | Difficulty | Contract | Vulnerabilities | Max Score | Real-World Analog |
|---|---|---|---|---|---|
| `easy` | ⭐ Easy | `VulnerableBank` | Reentrancy (1) | 0.97 | DAO Hack 2016 |
| `medium` | ⭐⭐ Medium | `DeFiVault` | Reentrancy + Missing AC + tx.origin (3) | 0.97 | Parity Wallet Hack |
| `hard` | ⭐⭐⭐ Hard | `RiskyLend` | Reentrancy + Oracle Manip + Delegatecall + Unchecked Call + Missing AC (5) | 0.97 | Euler Finance style |

---

## 🚀 Running Locally

```bash
git clone https://github.com/gopichandchalla16/smart-contract-audit-env.git
cd smart-contract-audit-env
pip install -r requirements.txt
export HF_TOKEN=hf_your_token_here
export ENV_URL=http://localhost:7860
uvicorn server.app:app --host 0.0.0.0 --port 7860
python inference.py
```

---

## 📁 Repository Structure

```
smart-contract-audit-env/
├── inference.py                          # 3-phase CoT agent
├── models.py                             # Pydantic data models
├── main.py                               # Entry point
├── openenv.yaml                          # Environment metadata
├── requirements.txt                      # Python dependencies
├── Dockerfile                            # Container build
├── BLOG.md                               # Hackathon blog post
├── training/
│   ├── Smart_Contract_Audit_GRPO_Training.ipynb  # Full training notebook
│   └── reward_curve.png                          # GRPO reward progression chart
└── server/
    ├── app.py                            # FastAPI routes
    └── smart_contract_audit_env_environment.py  # Env + grader
```

---

## 🔮 Future Work

- Extended vulnerability coverage (15+ CWE-mapped types)
- LLM-graded explanation quality scoring
- Multi-file contract auditing (Hardhat/Foundry projects)
- Competitive public leaderboard on HF Spaces
- Multi-language support (Rust/Move for Solana/Aptos)

---

## 👤 Author

**Gopichand Challa** — [GitHub](https://github.com/gopichandchalla16) · [HuggingFace](https://huggingface.co/Gopichand0516) · [@GopichandAI](https://twitter.com/GopichandAI)

Built for the **Meta OpenEnv Hackathon (Scaler × Meta PyTorch)** — April 2026
