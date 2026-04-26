---
title: Smart Contract Audit Env
emoji: 🔐
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
short_description: RL env for Solidity audit via GRPO + OpenEnv
---

# 🔐 Smart Contract Audit Agent — RL Environment (OpenEnv + GRPO)

[![HF Space](https://img.shields.io/badge/🤗%20Environment%20Space-smart--contract--audit--env-blue)](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env)
[![Model on HF](https://img.shields.io/badge/🤗%20Trained%20Model-smart--contract--audit--qwen--grpo-green)](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo)
[![Demo Space](https://img.shields.io/badge/🤗%20Live%20Demo-smart--contract--auditor-orange)](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor)
[![Colab](https://img.shields.io/badge/📓%20Training%20Notebook-Open%20in%20Colab-yellow)](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link)
[![Demo Video](https://img.shields.io/badge/🎥%20Demo%20Video-Watch%20on%20Loom-purple)](https://www.loom.com/share/f893d0641f30456d909776b661ab4bc6)
[![Hackathon](https://img.shields.io/badge/Meta%20PyTorch-OpenEnv%20Hackathon%202026-red)](https://github.com/gopichandchalla16/smart-contract-audit-env)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

> **Gopichand Challa** | Meta PyTorch OpenEnv Community Hackathon — April 2026

A **multi-step reinforcement learning environment** built on the OpenEnv framework that trains an LLM to audit Solidity smart contracts. Fine-tuned **Qwen2.5-1.5B-Instruct** via **GRPO + QLoRA** on a free T4 GPU — achieving **10.9× reward improvement** (0.030 → 0.329) in 200 steps (~85 min).

---

## ⚡ Quick Judge Test (60 seconds — no setup required)

**Step 1 — Hit /reset to get a live Solidity contract:**
```bash
curl -X POST https://gopichand0516-smart-contract-audit-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}' | python3 -m json.tool
```

**Step 2 — Submit an audit and get a reward back:**
```bash
curl -X POST https://gopichand0516-smart-contract-audit-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": "VULNERABILITY: Reentrancy Attack\nSEVERITY: High\nLOCATION: withdraw() line 14, external call before state update\nATTACK VECTOR: Attacker re-calls withdraw via fallback before balance resets\nIMPACT: 100% fund drain\nFIX: Move balances[msg.sender] = 0 before external call"
  }' | python3 -m json.tool
```

Expected response includes: `"reward": 0.6–1.0`, `"done": false/true`, `"feedback": "..."`, `"score_breakdown": {...}`

📝 **[Read the full writeup →](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env/blob/main/BLOG.md)**
🎥 **[Watch the Demo Video →](https://www.loom.com/share/f893d0641f30456d909776b661ab4bc6)**

---

## 🔗 All Links (Judges: Start Here)

| Resource | URL |
|----------|-----|
| 🏠 **HF Environment Space** | [spaces/Gopichand0516/smart-contract-audit-env](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env) |
| 🤖 **Trained Model** | [Gopichand0516/smart-contract-audit-qwen-grpo](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo) |
| 🎮 **Live Gradio Demo** | [spaces/Gopichand0516/smart-contract-auditor](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor) |
| 📓 **Training Notebook (Colab)** | [Open in Colab](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link) |
| 🎥 **Demo Video** | [Watch on Loom](https://www.loom.com/share/f893d0641f30456d909776b661ab4bc6) |
| 📝 **Blog Post** | [Read BLOG.md →](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env/blob/main/BLOG.md) |
| 💻 **GitHub Repo** | [gopichandchalla16/smart-contract-audit-env](https://github.com/gopichandchalla16/smart-contract-audit-env) |

---

## 🎯 Problem & Motivation

Smart contract vulnerabilities have caused **billions in losses**: The DAO ($60M reentrancy), Poly Network ($600M access control), Compound ($80M oracle manipulation). These bugs follow known patterns — but auditing is slow, expensive, and requires expert knowledge.

**This project asks: can we train a small LLM to think like a security auditor using pure reinforcement learning — no labeled examples, just a reward signal?**

The answer is yes. And the reward curve proves it.

---

## 📊 Training Results — 10.9× Reward Improvement

![Reward Curve](training/reward_curve.jpg)

| Metric | Value |
|--------|-------|
| 🟥 **Baseline Reward** (Step 10) | 0.030 |
| 🟩 **Final Reward** (Step 200) | **0.329** |
| 🚀 **Improvement** | **🔥 10.9×** |
| 🏆 **Peak Reward** (Step 150) | 0.284 |
| ⏱️ **Training Time** | ~85.7 min (free T4 GPU) |
| 🤖 **Base Model** | Qwen2.5-1.5B-Instruct |
| 🔧 **Trainable Params** | 18.4M / 1.03B (1.78%) |

### 📈 Full Reward Progression

| Step | Reward | KL Divergence |
|------|--------|---------------|
| 10 | 0.030 | 0.000040 |
| 40 | 0.105 | 0.006465 |
| 80 | 0.148 | 0.019515 |
| 130 | 0.217 | 0.017535 |
| 150 | **0.284** | 0.038510 |
| **200** | **0.329** | 0.051547 |

---

## 🔄 Environment Design — Multi-Step Iterative Audit Loop

### Key Innovation: 5-Step Refinement Within Each Episode

Unlike static single-shot tasks, this environment runs **up to 5 interactive steps per episode** — the agent iteratively refines its audit using feedback hints, just like a real human auditor:

```
Episode Start
    │
    ▼
Step 1: Agent submits initial audit report
    │   → Environment scores it, returns targeted feedback:
    │     "Missing: oracle manipulation. Check single spot price source (line 60)."
    ▼
Step 2: Agent refines with feedback → score improves
    │
    ▼
Step 3–5: Agent deepens analysis:
           severity labels, exact line numbers, attack vectors, mitigations
    │
    ▼
Done: score ≥ 0.95  OR  5 steps reached
```

This mirrors how real security audits work: a first pass catches obvious bugs, subsequent passes catch subtle protocol-level vulnerabilities.

### 3-Tier Progressive Difficulty

| Difficulty | Contract | Vulnerabilities | What Makes It Hard |
|---|---|---|---|
| 🟢 **Easy** | VulnerableBank | 1 (reentrancy) | Single pattern, isolated function |
| 🟡 **Medium** | DeFiVault | 3 (reentrancy + access control + tx.origin) | Multiple bugs, interactions between them |
| 🔴 **Hard** | RiskyLend | 5 (reentrancy + oracle manipulation + delegatecall + unchecked call + access control) | Real-world DeFi complexity, 100+ LOC |

**Delta reward signal** — the agent is rewarded for *improvement across steps*, not just absolute score. Regression is penalized, forcing consistent upward learning.

---

## 🏗️ Architecture

```
Base Model:     Qwen2.5-1.5B-Instruct
RL Algorithm:   GRPO (Group Relative Policy Optimization)
Adapter:        QLoRA r=16, alpha=16 — 1.78% of params trainable
Environment:    FastAPI HF Space (OpenEnv /reset + /step API)
Base Class:     server/env.py → SmartContractAuditEnv(OpenEnv.Environment)
Max Steps/Ep:   5 (multi-step iterative loop)
Difficulty:     3 levels (easy → medium → hard)
```

### 💰 Multi-Component Reward Function

```
total_reward = env_reward      (0.0–1.0)  Did you find the real vulnerability?
             + format_score    (0.0–0.3)  Structured report: severity / location / fix?
             + coverage_score  (0.0–0.2)  Impact + attack vector + mitigation explained?
             + delta_bonus     (+0.1)     Did you improve over your previous step?
             - penalty         (-0.2)     False "NO_VULNERABILITY" when one exists
             ─────────────────────────────
             Clipped to [0.0, 1.5]
```

### OpenEnv API Endpoints

```
POST /reset  →  Returns fresh Solidity contract + task description + difficulty level
POST /step   →  Accepts audit report → returns {reward, done, feedback, score_breakdown}
```

### ⚙️ GRPO Training Config

```python
GRPOConfig(
    max_steps=200,
    learning_rate=5e-6,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=4,
    max_completion_length=350,
    temperature=0.9,
    optim="adamw_8bit",
)
```

---

## 🎯 What It Detects

| Vulnerability | Severity | Example Contract |
|---|---|---|
| 🔄 Reentrancy | High | VulnerableBank, DeFiVault, RiskyLend |
| 🔓 Missing Access Control | Medium | DeFiVault (emergencyDrain), RiskyLend (setOracle) |
| 🎭 tx.origin Misuse | High | DeFiVault (adminWithdraw) |
| 🔮 Oracle Manipulation | High | RiskyLend (borrow — single spot price) |
| 📞 Unchecked Return Values | Medium | RiskyLend (repayDebt) |
| ⚡ Delegatecall Escalation | High | RiskyLend (executeUpgrade) |

---

## 🆚 Before vs. After Training

**❌ Untrained base model:**
```
"1. Reentrancy: The withdraw function can be reentered..." ← vague, no location, no fix
```

**✅ GRPO-trained model:**
```
VULNERABILITY: Reentrancy Attack
SEVERITY: High
LOCATION: withdraw() — line 14, external call before state update
ATTACK VECTOR: Attacker deploys malicious contract with fallback() that re-calls
               withdraw(). Balance not decremented until after ETH sent → drain loop.
IMPACT: 100% of contract funds drainable in single transaction
FIX: Apply Checks-Effects-Interactions — move balances[msg.sender] -= amount
     BEFORE the external call. Or use OpenZeppelin ReentrancyGuard.
```

---

## 🚀 Quick Start

### ▶️ Try the Live Demo
👉 **[smart-contract-auditor Space](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor)** — paste any Solidity contract, get an audit report

### 🔁 Interact With the Environment API (Python)

```python
import requests

BASE = "https://gopichand0516-smart-contract-audit-env.hf.space"

# Start episode
obs = requests.post(f"{BASE}/reset", json={"task_id": "medium"}).json()
print(obs["observation"]["contract_code"])

# Submit audit
result = requests.post(f"{BASE}/step", json={
    "action": "VULNERABILITY: Reentrancy\nSEVERITY: High\nLOCATION: withdraw()..."
}).json()
print(result["reward"], result["done"])
```

### 🐍 Use the Trained Model

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("Gopichand0516/smart-contract-audit-qwen-grpo")
tokenizer = AutoTokenizer.from_pretrained("Gopichand0516/smart-contract-audit-qwen-grpo")

contract = """
pragma solidity ^0.8.0;
contract Vulnerable {
    mapping(address => uint) public balances;
    function withdraw() public {
        uint amount = balances[msg.sender];
        (bool ok,) = msg.sender.call{value: amount}("");
        balances[msg.sender] = 0;
    }
}
"""
prompt = f"Audit this Solidity contract and identify all vulnerabilities:\n{contract}"
inputs = tokenizer(prompt, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=300)
print(tokenizer.decode(output[0], skip_special_tokens=True))
```

---

## 📁 Repository Structure

```
smart-contract-audit-env/
├── server/
│   ├── env.py
│   ├── smart_contract_audit_env_environment.py
│   └── models.py
├── training/
│   ├── Smart_Contract_Audit_GRPO_Training_Full.ipynb
│   └── reward_curve.jpg
├── BLOG.md
├── inference.py
├── client.py
├── openenv.yaml
└── README.md
```

---

## 🔒 Security Note

Authentication via `os.environ.get('HF_TOKEN')` or Colab Secrets. **Never hardcode tokens.**

---

## 👤 Author

**Gopichand Challa** — CSE Graduate | Web3 + AI Builder | Bengaluru, India

[![GitHub](https://img.shields.io/badge/GitHub-gopichandchalla16-black?logo=github)](https://github.com/gopichandchalla16)
[![HuggingFace](https://img.shields.io/badge/🤗-Gopichand0516-yellow)](https://huggingface.co/Gopichand0516)

Built for the **Meta PyTorch OpenEnv Community Hackathon** — April 2026 🎉
