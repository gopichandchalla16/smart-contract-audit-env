---
title: Smart Contract Audit Env
emoji: ??
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
short_description: RL environment for smart contract auditing
---
# 🔐 Smart Contract Audit Agent — GRPO + RL Training

[![Model on HF](https://img.shields.io/badge/🤗%20Model-Gopichand0516%2Fsmart--contract--audit--qwen--grpo-blue)](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo)
[![Demo Space](https://img.shields.io/badge/🤗%20Demo-smart--contract--auditor-green)](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor)
[![Hackathon](https://img.shields.io/badge/Meta%20PyTorch-OpenEnv%20Hackathon-orange)](https://github.com/gopichandchalla16/smart-contract-audit-env)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

> Fine-tuned **Qwen2.5-1.5B-Instruct** using **GRPO (Group Relative Policy Optimization) + QLoRA** reinforcement learning to detect Solidity smart contract vulnerabilities. Trained for 200 steps (~85 minutes) on a free T4 GPU — achieving a **10.9× reward improvement** from baseline 0.030 → final 0.329.

---

## 📊 Training Results — 10.9× Reward Improvement


| Metric | Value |
|--------|-------|
| **Baseline Reward** (Step 10) | 0.030 |
| **Final Reward** (Step 200) | **0.329** |
| **Improvement** | **🔥 10.9×** |
| **Peak Reward** (Step 150) | 0.284 |
| **Training Steps** | 200 |
| **Training Time** | ~85.7 min (T4 GPU) |
| **Base Model** | Qwen2.5-1.5B-Instruct |
| **Trainable Params** | 18.4M / 1.03B (1.78%) |

### Step-by-Step Reward Progression (Real Logged Data)

| Step | Reward | KL Divergence | Training Loss |
|------|--------|---------------|---------------|
| 10 | 0.041 | 0.000017 | 0.000000 |
| 20 | 0.051 | 0.000019 | 0.000000 |
| 30 | 0.075 | 0.000234 | 0.000000 |
| 40 | 0.031 | 0.000908 | 0.000001 |
| 50 | 0.031 | 0.001202 | 0.000001 |
| 60 | 0.050 | 0.002177 | 0.000002 |
| 70 | 0.072 | 0.004207 | 0.000004 |
| 80 | 0.119 | 0.009147 | 0.000009 |
| 90 | 0.112 | 0.022168 | 0.000022 |
| 100 | 0.125 | 0.030487 | 0.000030 |
| 110 | 0.157 | 0.053824 | 0.000054 |
| 120 | 0.194 | 0.054709 | 0.000055 |
| 130 | 0.227 | 0.020788 | 0.000021 |
| 140 | 0.272 | 0.028111 | 0.000028 |
| 150 | **0.267** | 0.015059 | 0.000015 |
| 160 | 0.246 | 0.021848 | 0.000022 |
| 170 | 0.237 | 0.014134 | 0.000014 |
| 180 | 0.245 | 0.025343 | 0.000025 |
| 190 | 0.309 | 0.021611 | 0.000022 |
| **200** | **0.298** | **0.008714** | **0.000009** |

---

## 🎯 What It Detects

The RL-trained agent detects real Solidity vulnerabilities:

- **Reentrancy attacks** — state updated after external call (e.g. the classic drain-the-contract bug)
- **Missing access control** — functions callable by anyone with no `onlyOwner` check
- **Integer overflow/underflow** — unchecked arithmetic pre-Solidity 0.8.0
- **Oracle manipulation** — price feeds that can be flash-loan attacked
- **tx.origin misuse** — phishing-vulnerable authentication
- **Unchecked external call return values** — silent failure on `.call()`

---

## 🏗️ Architecture

```
Base Model:     Qwen2.5-1.5B-Instruct (4-bit QLoRA via Unsloth)
RL Algorithm:   GRPO (Group Relative Policy Optimization)
Adapter:        LoRA r=16, α=16 — 1.78% params trainable
Environment:    FastAPI HF Space (reset/step OpenEnv API)
Reward Fn:      Environment accuracy + format + coverage − hallucination penalty
```

### Reward Function (Multi-Component)

```python
total_reward = (
    env_reward      # 0.0–1.0  — Did you catch the real vulnerability?
  + format_score   # 0.0–0.3  — Is the report properly structured?
  + coverage_score # 0.0–0.2  — Did you explain IMPACT + FIX?
  + penalty        # -0.2     — Penalty for claiming NO_VULNERABILITY when one exists
)
# Clipped to [0.0, 1.5]
```

### GRPO Training Config

```python
GRPOConfig(
    max_steps=200,
    learning_rate=5e-6,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,   # effective batch = 4
    num_generations=4,               # sample 4 responses per prompt
    max_completion_length=350,
    temperature=0.9,
    optim="adamw_8bit",
)
```

---

## 🚀 Quick Start

### Run the Demo

👉 **[Try the live Gradio demo on HuggingFace Spaces](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor)**

### Use the Model

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "Gopichand0516/smart-contract-audit-qwen-grpo"
)
tokenizer = AutoTokenizer.from_pretrained(
    "Gopichand0516/smart-contract-audit-qwen-grpo"
)

contract = """
pragma solidity ^0.8.0;
contract Vulnerable {
    mapping(address => uint) public balances;
    function withdraw() public {
        uint amount = balances[msg.sender];
        (bool ok,) = msg.sender.call{value: amount}("");
        balances[msg.sender] = 0;  // state updated AFTER external call!
    }
}
"""

prompt = f"Audit this Solidity contract:\n{contract}"
inputs = tokenizer(prompt, return_tensors="pt")
output = model.generate(**inputs, max_new_tokens=300)
print(tokenizer.decode(output[0], skip_special_tokens=True))
```

---

## 📁 Repository Structure

```
smart-contract-audit-env/
├── server/              # FastAPI OpenEnv environment
├── training/
│   ├── Smart_Contract_Audit_GRPO_Training.ipynb  ← Full Colab notebook (200 steps)
│   └── reward_curve.jpg                          ← Training reward chart
├── BLOG.md              # Full technical blog post
├── inference.py         # Inference helper
├── client.py            # Environment client
├── openenv.yaml         # OpenEnv spec
└── README.md
```

---

## 🔗 Links

| Resource | Link |
|----------|------|
| 🤗 Trained Model | [Gopichand0516/smart-contract-audit-qwen-grpo](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo) |
| 🤗 Live Demo | [Gopichand0516/smart-contract-auditor](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor) |
| 📓 Colab Notebook | [Open in Colab](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link) |
| 📝 Blog Post | [BLOG.md](./BLOG.md) |

---

## 👤 Author

**Gopichand Challa** — CSE Graduate, Web3 + AI Builder

[![GitHub](https://img.shields.io/badge/GitHub-gopichandchalla16-black?logo=github)](https://github.com/gopichandchalla16)
[![HuggingFace](https://img.shields.io/badge/🤗-Gopichand0516-yellow)](https://huggingface.co/Gopichand0516)

Built for the **Meta PyTorch OpenEnv Community Hackathon** — April 2026 🎉


