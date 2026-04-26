---
title: Smart Contract Audit Env
emoji: 🔐
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

![Reward Curve](training/reward_curve.jpg)

| Metric | Value |
|--------|-------|
| 🟥 **Baseline Reward** (Step 10) | 0.030 |
| 🟩 **Final Reward** (Step 200) | **0.329** |
| 🚀 **Improvement** | **🔥 10.9×** |
| 🏆 **Peak Reward** (Step 150) | 0.284 |
| ⏱️ **Training Steps** | 200 |
| 🖥️ **Training Time** | ~85.7 min (T4 GPU) |
| 🤖 **Base Model** | Qwen2.5-1.5B-Instruct |
| 🔧 **Trainable Params** | 18.4M / 1.03B (1.78%) |

### 📈 Step-by-Step Reward Progression (Real Logged Data)

| Step | Reward | KL Divergence | Training Loss |
|------|--------|---------------|---------------|
| 10 | 0.030 | 0.000040 | 0.000000 |
| 20 | 0.041 | 0.000179 | 0.000000 |
| 30 | 0.037 | 0.001621 | 0.000000 |
| 40 | 0.105 | 0.006465 | 0.000001 |
| 50 | 0.101 | 0.019485 | 0.000001 |
| 60 | 0.135 | 0.035509 | 0.000002 |
| 70 | 0.095 | 0.009482 | 0.000004 |
| 80 | 0.148 | 0.019515 | 0.000009 |
| 90 | 0.179 | 0.017396 | 0.000022 |
| 100 | 0.187 | 0.034385 | 0.000030 |
| 110 | 0.194 | 0.025628 | 0.000054 |
| 120 | 0.185 | 0.052503 | 0.000055 |
| 130 | 0.217 | 0.017535 | 0.000021 |
| 140 | 0.249 | 0.031333 | 0.000028 |
| 150 | **0.284** | 0.038510 | 0.000015 |
| 160 | 0.247 | 0.022530 | 0.000022 |
| 170 | 0.236 | 0.051557 | 0.000014 |
| 180 | 0.215 | 0.023148 | 0.000025 |
| 190 | 0.232 | 0.058089 | 0.000022 |
| **200** | **0.329** | **0.051547** | **0.000009** |

---

## 🎯 What It Detects

The RL-trained agent detects real Solidity vulnerabilities:

- 🔄 **Reentrancy attacks** — state updated after external call (e.g. the classic drain-the-contract bug)
- 🔓 **Missing access control** — functions callable by anyone with no `onlyOwner` check
- ➕ **Integer overflow/underflow** — unchecked arithmetic pre-Solidity 0.8.0
- 🔮 **Oracle manipulation** — price feeds that can be flash-loan attacked
- 🎭 **tx.origin misuse** — phishing-vulnerable authentication
- 📞 **Unchecked external call return values** — silent failure on `.call()`

---

## 🏗️ Architecture

```
Base Model:     Qwen2.5-1.5B-Instruct (4-bit QLoRA via Unsloth)
RL Algorithm:   GRPO (Group Relative Policy Optimization)
Adapter:        LoRA r=16, α=16 — 1.78% params trainable
Environment:    FastAPI HF Space (reset/step OpenEnv API)
Base Class:     server/env.py → class SmartContractAuditEnv(OpenEnv.Environment)
Reward Fn:      Environment accuracy + format + coverage − hallucination penalty
```

### 💰 Reward Function (Multi-Component)

```python
total_reward = (
    env_reward      # 0.0–1.0  — Did you catch the real vulnerability?
  + format_score   # 0.0–0.3  — Is the report properly structured?
  + coverage_score # 0.0–0.2  — Did you explain IMPACT + FIX?
  + penalty        # -0.2     — Penalty for claiming NO_VULNERABILITY when one exists
)
# Clipped to [0.0, 1.5]
```

### ⚙️ GRPO Training Config

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

### ▶️ Run the Demo

👉 **[Try the live Gradio demo on HuggingFace Spaces](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor)**

### 🐍 Use the Model

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
├── 🖥️  server/              # FastAPI OpenEnv environment (SmartContractAuditEnv extends OpenEnv.Environment)
├── 📓  training/
│   ├── 📓_Smart_Contract_Audit_—_GRPO_Training_Notebook.ipynb  ← Full notebook (200 steps, all outputs)
│   └── reward_curve.jpg                                        ← Training reward chart
├── 📝  BLOG.md              # Full technical blog post
├── 🔍  inference.py         # Inference helper
├── 🔗  client.py            # Environment client
├── 📋  openenv.yaml         # OpenEnv spec
└── 📖  README.md
```

---

## 🔗 Links

| Resource | Link |
|----------|------|
| 🤗 Trained Model | [Gopichand0516/smart-contract-audit-qwen-grpo](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo) |
| 🎮 Live Demo | [Gopichand0516/smart-contract-auditor](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor) |
| 📓 Colab Notebook | [Open in Colab](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link) |
| 📝 Blog Post | [BLOG.md](./BLOG.md) |

---

## 🔒 Security Note

This notebook uses `os.environ.get('HF_TOKEN')` or Colab Secrets (`userdata.get('HF_TOKEN')`) for authentication. **Never hardcode tokens in notebooks.** Add your HF token via the Colab Secrets panel (🔑 icon in sidebar).

---

## 👤 Author

**Gopichand Challa** — CSE Graduate, Web3 + AI Builder 🛠️

[![GitHub](https://img.shields.io/badge/GitHub-gopichandchalla16-black?logo=github)](https://github.com/gopichandchalla16)
[![HuggingFace](https://img.shields.io/badge/🤗-Gopichand0516-yellow)](https://huggingface.co/Gopichand0516)

Built for the **Meta PyTorch OpenEnv Community Hackathon** — April 2026 🎉
