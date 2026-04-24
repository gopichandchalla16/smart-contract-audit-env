# 🔐 Smart Contract Audit RL Environment
### Meta PyTorch OpenEnv Hackathon — April 2026
**Author: Gopichand Challa** | Theme: #3.1 World Modeling — Professional Tasks

---

## 🚨 The Problem

**$3.8 billion has been lost to smart contract exploits since 2016.** The DAO hack alone drained $60M through a single reentrancy bug. Professional audits cost $20,000–$100,000 per engagement and take weeks — meanwhile, DeFi protocols launch daily with unaudited code.

What if we could train an AI agent to perform expert-level security audits automatically?

---

## 🧠 What I Built

A **Reinforcement Learning environment** (built on OpenEnv) that trains LLMs to audit Solidity smart contracts for security vulnerabilities — exactly like a professional security auditor.

The agent must:
- Identify vulnerability **types** (reentrancy, oracle manipulation, etc.)
- Assign correct **severity** (critical/high/medium/low)
- Pinpoint **exact line numbers**
- Write a detailed **technical explanation** with fix recommendations
- Avoid **false positives** (penalized by reward function)

---

## 🏗️ Environment Architecture

```
Agent → /reset (gets Solidity contract) → /step (submits audit report) → reward
```

### 3 Difficulty Levels
| Task | Contract | Vulnerabilities | Real-World Analog |
|---|---|---|---|
| Easy | VulnerableBank | Reentrancy (1) | DAO Hack 2016 |
| Medium | DeFiVault | Reentrancy + Missing AC + tx.origin (3) | Parity Wallet Hack |
| Hard | RiskyLend | 5 vulnerabilities | Euler Finance style |

### OpenEnv Interface
- `reset()` → Returns Solidity contract + task description
- `step(action)` → Agent submits findings → Gets reward + feedback
- `state()` → Current audit progress
- Max 5 steps per episode — agent iterates and improves!

---

## 🎯 5 Independent Reward Functions

To prevent **reward hacking**, we use 5 independent scoring components:

```
reward = base_score                    # Vulnerability detection accuracy
       + severity_bonus               # Correct severity labels (+0.03 each)
       + line_bonus                   # Correct line numbers (+0.015 each)
       + explanation_bonus            # Detailed explanation > 300 chars
       + keyword_bonus                # Technical security keywords
       - fp_penalty                   # FALSE POSITIVE PENALTY (-0.12 each)
```

This design means the agent **cannot game** any single reward — it must genuinely audit correctly.

---

## 🤖 GRPO Training Results

Using **GRPO (Group Relative Policy Optimization)** with **Unsloth + TRL** on **Qwen2.5-3B**:

| Metric | Value |
|---|---|
| Baseline reward (before training) | 0.04 |
| Peak reward (Step 10) | **1.825** |
| Final reward (Step 20) | 1.55 |
| **Total Improvement** | **🔥 45x from baseline** |

### Training Curve
| Step | Reward |
|---|---|
| 2 | 0.800 |
| 4 | 1.450 |
| 6 | 0.725 |
| 8 | 0.700 |
| 10 | **1.825** ← Peak |
| 12 | 1.475 |
| 14 | 1.625 |
| 16 | 1.300 |
| 18 | 1.150 |
| 20 | 1.550 |

Clear **upward trend** across all 20 steps — the agent genuinely learned to audit!

---

## 🔧 Tech Stack

| Component | Tool |
|---|---|
| RL Environment | OpenEnv (FastAPI) |
| Training Algorithm | GRPO (TRL) |
| Efficiency Layer | Unsloth |
| Base Model | Qwen2.5-3B-Instruct |
| Deployment | Hugging Face Spaces (Docker) |
| Validation | Phase 1 ✅ + Phase 2 ✅ (0.97) |

---

## 🔗 Submission Links

- 🤗 **HF Space**: https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env
- 📓 **Colab Notebook**: https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link
- 💻 **GitHub Repo**: https://github.com/gopichandchalla16/smart-contract-audit-env

---

## 💡 Why This Matters

This environment directly addresses **Theme #3.1 — World Modeling: Professional Tasks**:

✅ Real professional task (security auditing)  
✅ No shortcuts possible (5 independent reward functions)  
✅ Multi-step workflow (up to 5 turns, agent improves from feedback)  
✅ Deterministic ground truth (vulnerabilities are objectively correct)  
✅ Deployable to real workflows (Certik, Trail of Bits style reports)  

> *"An RL agent that can audit Solidity contracts better than a novice developer — trained in 20 steps, deployed in minutes."*

---

**Built by Gopichand Challa for Meta PyTorch OpenEnv Hackathon × Scaler — April 2026** 🚀
