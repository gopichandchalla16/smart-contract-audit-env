# I Trained an AI to Audit Smart Contracts Using Reinforcement Learning — Here's What Happened

*By Gopichand Challa | Meta PyTorch OpenEnv Hackathon, April 2026*

🎥 **[Watch the Demo Video →](https://www.loom.com/share/f893d0641f30456d909776b661ab4bc6)**

---

I want to tell you about the 85 minutes that changed how I think about AI.

Yesterday morning, I ran a training loop on Google Colab — a free T4 GPU, no fancy hardware, no big team. Just me, a notebook, and a question: *Can I teach an AI to think like a smart contract auditor using reinforcement learning?*

The answer, it turns out, is yes. And the reward curve tells the story better than I can.

![Reward Curve](training/reward_curve.jpg)

---

## The Problem I Was Trying to Solve

Smart contract bugs are expensive. Not "that's annoying" expensive — I mean *The DAO hack drained $60M* expensive. *Poly Network lost $600M* expensive. *Compound's oracle manipulation lost $80M* expensive.

The scary part? Most of these vulnerabilities follow known patterns. Reentrancy. Missing access control. Unchecked return values. Oracle manipulation. Stuff that, if you know what to look for, you'd catch in a careful code review.

So the question isn't *can* an AI detect these — it's whether we can train one to do it *reliably*, with structured output that's actually useful to a developer. No labelled data. Just reward signals.

That's what this project is about.

---

## What is GRPO and Why Did I Choose It?

Most people fine-tune LLMs with supervised learning: show the model examples, train it to copy them. That works, but it has a ceiling. The model learns to mimic — it doesn't learn to *reason*.

GRPO (Group Relative Policy Optimization) is different. It's reinforcement learning — the same family of algorithms used in DeepSeek-R1 and ChatGPT's reasoning mode, but without needing a separate "value model" (which saves a massive amount of memory).

Here's how it works in plain English:

1. The model looks at a Solidity contract
2. It generates **4 different audit reports** for the same contract
3. Each report gets a **reward score** from our environment
4. The model updates itself to make the *better* reports more likely next time
5. Repeat 200 times

No labeled examples. No human feedback. The reward signal is the teacher.

---

## Building the Environment — The Multi-Step Iterative Loop

Before training, I needed an environment the model could interact with. I built this as a **FastAPI app on HuggingFace Spaces** implementing the OpenEnv base class.

But here's the key design insight that makes this environment genuinely interesting: **it's multi-step**.

Most text RL environments are single-shot — the model gives one answer, gets one reward, episode ends. That's not how real auditing works. A real auditor does multiple passes: a first pass catches obvious bugs, subsequent passes catch subtle ones.

So I built the environment to support **up to 5 steps per episode**:

```
Episode Start
    │
    ▼
Step 1: Agent submits initial audit
    │   → Environment returns reward + targeted feedback:
    │     "You found reentrancy ✓. Missing: oracle manipulation.
    │      Hint: check if borrow() uses a single spot price source."
    ▼
Step 2: Agent refines with the feedback hint → score improves
    │
    ▼
Step 3–5: Agent deepens — severity labels, exact line numbers, attack vectors
    │
    ▼
Done: score ≥ 0.95  OR  5 steps exhausted
```

The agent learns to *use feedback* — to iterate on its own outputs, not just produce one-shot answers. This is the same reasoning loop that makes o1 and R1 powerful, but applied to a real-world security domain.

```python
class SmartContractAuditEnv(OpenEnv.Environment):
    def reset(self) -> dict:
        # Returns a fresh Solidity contract to audit + difficulty level
        ...
    def step(self, action: str) -> dict:
        # Takes audit response → reward + done + targeted hints
        ...
```

### Three Difficulty Tiers — Progressive Complexity

I built three contracts, each progressively harder:

| Difficulty | Contract | Vulnerabilities |
|---|---|---|
| 🟢 Easy | VulnerableBank | 1 — reentrancy |
| 🟡 Medium | DeFiVault | 3 — reentrancy + missing access control + tx.origin |
| 🔴 Hard | RiskyLend | 5 — reentrancy + oracle manipulation + delegatecall + unchecked call + access control |

The **Hard** contract is a real-world-style DeFi lending protocol with over 100 lines of code and vulnerability interactions — flash loan attack surface, delegatecall privilege escalation, the works.

### The Reward Function (Multi-Component)

```
total_reward = env_reward      (0.0–1.0)  Did you find the real vulnerability?
             + format_score    (0.0–0.3)  Structured report: severity / location / fix?
             + coverage_score  (0.0–0.2)  Impact + attack vector + mitigation explained?
             + delta_bonus     (+0.1)     Did you improve over your previous step?
             - penalty         (-0.2)     False "NO_VULNERABILITY" when one exists
             ─────────────────────────────
             Clipped to [0.0, 1.5]
```

The **anti-hallucination penalty** was a late addition — and essential. Early in training the model had a bad habit of confidently saying "NO_VULNERABILITIES_FOUND" when it didn't know the answer. The penalty pushed it to actually try.

The **delta bonus** rewards improvement across steps — if your step 2 audit scores higher than step 1, you get an extra signal. Regression is penalized. This shapes the agent to use feedback productively.

---

## The Model: Qwen2.5-1.5B on a Free GPU

I used **Qwen2.5-1.5B-Instruct** — small enough to fit on Colab's free T4 GPU in 4-bit precision (~1.57 GB VRAM).

For efficient training, I used **QLoRA** — which adds small trainable "adapter" layers instead of updating the whole model. Out of 1.03 billion total parameters, only **18.4 million (1.78%)** were actually trained.

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

## The Results: 10.9× Improvement

| Step | Reward | What Was Happening |
|------|--------|--------------------|
| 10 | 0.030 | Baseline — mostly confused, often hallucinating |
| 40 | 0.105 | Starting to use structured format |
| 80 | 0.148 | Identifying reentrancy patterns reliably |
| 130 | 0.217 | Consistent vulnerability detection + correct severity |
| 150 | **0.284** | Peak — format + accuracy + coverage all improving |
| **200** | **0.329** | **Final — 10.9× above baseline** |

KL divergence stayed mostly below 0.05 throughout — meaning the model was learning without drifting dangerously far from its original behaviour. Healthy RL signal.

The dip at step 70 (0.095) is normal RL exploration — the model was trying new output formats. The trend is what matters, not individual steps.

---

## Before vs. After: The Same Contract

```solidity
pragma solidity ^0.8.0;
contract VulnerableBank {
    mapping(address => uint256) public balances;
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount; // ← STATE UPDATED AFTER EXTERNAL CALL!
    }
}
```

**❌ Untrained base model:**
> *"1. Reentrancy: The withdraw function can be reentered through an external call..."*
> — Vague. No severity. No line number. No attack vector. No fix.

**✅ GRPO-trained model (after 200 steps):**
```
VULNERABILITY: Reentrancy Attack
SEVERITY: High
LOCATION: withdraw() — line 7, external call before state update
ATTACK VECTOR: Attacker deploys malicious contract with fallback() that
               re-calls withdraw(). Balance not decremented until after
               ETH sent → recursive drain loop empties contract.
IMPACT: 100% of contract funds drainable in a single transaction.
FIX: Apply Checks-Effects-Interactions — move balances[msg.sender] -= amount
     BEFORE the external call. Alternatively, use OpenZeppelin ReentrancyGuard.
```

That's a real audit report. Structured, specific, actionable. Produced by a 1.5B model trained in 85 minutes on a free GPU.

---

## What I Learned About Building RL Environments

1. **Multi-step > single-step for real-world tasks.** The feedback loop between environment and agent is where real learning happens. A one-shot reward doesn't capture the iterative nature of real auditing.
2. **Reward function design matters more than anything else.** I spent more time on reward components than any other part. The anti-hallucination penalty and delta bonus were both late additions — both essential.
3. **Difficulty curriculum matters.** Starting on easy contracts and progressing to hard ones gives the agent a learning path. Random hard examples early on produces mostly noise.
4. **Small models can learn surprisingly well with the right reward signal.** 1.5B parameters, trained in under 2 hours, writes better security reports than the base model.
5. **GRPO is memory-efficient.** No separate critic model = whole thing fits in ~2 GB VRAM. Works on any free Colab.

---

## What's Next

- Train longer (500+ steps) with curriculum scheduling (easy → hard contracts only)
- Bigger base model (Qwen2.5-7B or Llama-3.2-3B)
- Richer reward signal for the Hard contract (partial credit per vulnerability found)
- Full multi-step training where the agent learns to *use feedback* across steps, not just within them
- Open-source local auditor that replaces first-pass manual review

---

## Try It Yourself

| Resource | Link |
|----------|------|
| 🎥 **Demo Video** | [Watch on Loom](https://www.loom.com/share/f893d0641f30456d909776b661ab4bc6) |
| 🏠 **Environment Space** | [smart-contract-audit-env](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env) |
| 🎮 **Live Demo** | [smart-contract-auditor](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor) |
| 🤗 **Model Weights** | [smart-contract-audit-qwen-grpo](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo) |
| 📓 **Training Notebook** | [Open in Colab](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link) |
| 💻 **GitHub** | [smart-contract-audit-env](https://github.com/gopichandchalla16/smart-contract-audit-env) |

---

*Built at the Meta PyTorch OpenEnv Community Hackathon, April 2026.*  
*Gopichand Challa — CSE Graduate | Web3 + AI Builder | Bengaluru, India*
