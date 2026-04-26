# I Trained an AI to Audit Smart Contracts Using Reinforcement Learning — Here's What Happened

*By Gopichand Challa | Meta PyTorch OpenEnv Hackathon, April 2026*

---

I want to tell you about the 85 minutes that changed how I think about AI.

Yesterday morning, I ran a training loop on Google Colab — a free T4 GPU, no fancy hardware, no big team. Just me, a notebook, and a question: *Can I teach an AI to think like a smart contract auditor using reinforcement learning?*

The answer, it turns out, is yes. And the reward curve tells the story better than I can.

![Reward Curve](training/reward_curve.jpg)

---

## The Problem I Was Trying to Solve

Smart contract bugs are expensive. Not "that's annoying" expensive — I mean *The DAO hack drained $60M* expensive. *Poly Network lost $600M* expensive.

The scary part? Most of these vulnerabilities follow known patterns. Reentrancy. Missing access control. Unchecked return values. Stuff that, if you know what to look for, you'd catch in a code review.

So the question isn't *can* an AI detect these — it's whether we can train one to do it *reliably*, with structured output that's actually useful to a developer.

That's what this project is about.

---

## What is GRPO and Why Did I Choose It?

Most people fine-tune LLMs with supervised learning: show the model examples, train it to copy them. That works, but it has a ceiling. The model just learns to mimic — it doesn't learn to *reason*.

GRPO (Group Relative Policy Optimization) is different. It's reinforcement learning — specifically, the same family of algorithms used to train ChatGPT, but without needing a separate "value model" (which saves a ton of memory).

Here's how it works in plain English:

1. The model looks at a Solidity contract
2. It generates **4 different audit reports** for the same contract
3. Each report gets a **reward score** from our environment
4. The model updates itself to make the *better* reports more likely next time
5. Repeat 200 times

The model learns by trying, failing, and trying again. That's real learning — not memorization.

---

## Building the Environment (OpenEnv API)

Before training, I needed an environment the model could interact with. I built this as a **FastAPI app on HuggingFace Spaces** implementing the OpenEnv base class:

```python
class SmartContractAuditEnv(OpenEnv.Environment):
    def reset(self) -> dict:
        # Returns a fresh Solidity contract to audit
        ...
    def step(self, action: str) -> dict:
        # Takes audit response, returns reward + done
        ...
```

Two endpoints:
- `POST /reset` — gives the model a fresh Solidity contract to audit
- `POST /step` — takes the model's audit response and returns a reward score

The reward function has four components:

```python
total_reward = (
    env_reward      # Did you find the real vulnerability? (0.0–1.0)
  + format_score   # Is the report structured properly? (0.0–0.3)
  + coverage_score # Did you explain impact AND fix? (0.0–0.2)
  + penalty        # -0.2 if you said "no vulnerability" when there was one
)
# Clipped to [0.0, 1.5]
```

The anti-hallucination penalty was critical. Early in training, the model had a bad habit of saying "NO_VULNERABILITIES_FOUND" when confused. The penalty pushed it to actually try.

---

## The Model: Qwen2.5-1.5B on a Free GPU

I used **Qwen2.5-1.5B-Instruct** — small enough to fit on Colab's free T4 GPU in 4-bit precision (~1.57 GB VRAM).

For efficient training, I used **QLoRA** — which adds small trainable "adapter" layers instead of updating the whole model. Out of 1.03 billion total parameters, only **18.4 million (1.78%)** were actually trained.

Training config:
```python
GRPOConfig(
    max_steps=200,
    learning_rate=5e-6,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_generations=4,           # 4 responses per prompt → better gradient signal
    max_completion_length=350,
    temperature=0.9,
    optim="adamw_8bit",
)
```

---

## The Results: 10.9× Improvement

| Step | Reward | What Was Happening |
|------|--------|--------------------||
| 10 | 0.030 | Baseline — mostly confused |
| 40 | 0.105 | Starting to use structured format |
| 80 | 0.148 | Identifying reentrancy patterns |
| 130 | 0.217 | Consistent vulnerability detection |
| 150 | 0.284 | Peak performance on format + accuracy |
| **200** | **0.329** | **Final — 10.9× above baseline** |

The KL divergence stayed mostly below 0.05 throughout, meaning the model was learning *without* drifting dangerously far from its original behavior.

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

**Untrained model:**
> *"1. Reentrancy: The withdraw function can be reentered through an external call..."* ← vague, wrong fix

**RL-trained model:**
> *"VULNERABILITY: Reentrancy Attack*
> *SEVERITY: High*
> *LOCATION: withdraw() — external call before state update*
> *IMPACT: Attacker can repeatedly call withdraw() before balance is zeroed, draining all funds*
> *FIX: Apply checks-effects-interactions — update balances[msg.sender] BEFORE the external call. Or use OpenZeppelin ReentrancyGuard."*

That's a real audit report. Structured, specific, actionable.

---

## What I Learned About GRPO

1. **Reward function design matters more than anything.** I spent more time on reward components than any other part. The anti-hallucination penalty was a late addition — essential.
2. **Small models can learn surprisingly well.** 1.5B parameters, trained in under 2 hours, writes better security reports than the base model.
3. **GRPO is memory-efficient.** No separate critic model = whole thing fits in ~2 GB VRAM. Works on any free Colab.
4. **Dips in reward curves are normal.** At step 70, reward dropped to 0.095. That's RL exploration — the trend matters, not individual steps.

---

## What's Next

- Train longer (500+ steps) with curriculum (easy → hard contracts)
- Bigger base model (Qwen2.5-7B)
- Richer reward signal (multi-vulnerability contracts)
- Open-source local auditor that produces reports useful enough to replace first-pass manual review

---

## Try It Yourself

| Resource | Link |
|----------|------|
| 🤗 Live Demo | [smart-contract-auditor](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor) |
| 🤗 Model Weights | [smart-contract-audit-qwen-grpo](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo) |
| 📓 Colab Notebook | [Open in Colab](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link) |
| 🔧 Environment Code | [HF Space Files](https://huggingface.co/spaces/Gopichand0516/smart-contract-audit-env/tree/main) |
| 💻 GitHub | [smart-contract-audit-env](https://github.com/gopichandchalla16/smart-contract-audit-env) |

---

*Built at the Meta PyTorch OpenEnv Community Hackathon, April 2026.*
*Gopichand Challa — CSE Graduate | Web3 + AI Builder | Bengaluru, India*
