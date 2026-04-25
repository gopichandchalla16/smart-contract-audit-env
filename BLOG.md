# I Trained an AI to Audit Smart Contracts Using Reinforcement Learning — Here's What Happened

*By Gopichand Challa | Meta PyTorch OpenEnv Hackathon, April 2026*

---

I want to tell you about the 85 minutes that changed how I think about AI.

Yesterday morning, I ran a training loop on Google Colab — a free T4 GPU, no fancy hardware, no big team. Just me, a notebook, and a question: *Can I teach an AI to think like a smart contract auditor using reinforcement learning?*

The answer, it turns out, is yes. And the reward curve tells the story better than I can.

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

## Building the Environment

Before training, I needed an environment the model could interact with. Think of it like a gym for the AI — it submits an audit, gets a score, and learns.

I built this as a **FastAPI app on HuggingFace Spaces** with two endpoints:

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
```

The anti-hallucination penalty was important. Early in training, the model had a bad habit of saying "NO_VULNERABILITIES_FOUND" when it was confused. That penalty pushed it to actually try.

---

## The Model: Qwen2.5-1.5B on a Free GPU

I used **Qwen2.5-1.5B-Instruct** — a 1.5 billion parameter model, small enough to fit on Colab's free T4 GPU in 4-bit precision (about 1.57 GB of GPU memory).

For efficient training, I used **QLoRA** — which adds small trainable "adapter" layers instead of updating the whole model. Out of 1.03 billion total parameters, only **18.4 million (1.78%)** were actually trained. That's the magic of LoRA: massive parameter efficiency.

Training setup:
- **200 GRPO update steps**
- **4 responses sampled per prompt** (that's how GRPO works — more samples = better gradient signal)
- **Learning rate**: 5e-6 with AdamW 8-bit optimizer
- **Total time**: 85.7 minutes

---

## The Results: 10.9× Improvement

Here's the moment I got excited. Watching the reward column during training:

| Step | Reward | What Was Happening |
|------|--------|--------------------|
| 10 | 0.030 | Baseline — mostly confused |
| 40 | 0.105 | Starting to use structured format |
| 80 | 0.148 | Identifying reentrancy patterns |
| 130 | 0.217 | Consistent vulnerability detection |
| 150 | 0.284 | Peak performance on format + accuracy |
| **200** | **0.329** | **Final — 10.9× above baseline** |

The KL divergence stayed mostly below 0.05 (our instability threshold), which means the model was learning *without* drifting too far from its original behavior. A few spikes at steps 120 and 190, but it always recovered.

The reward didn't go up in a perfectly smooth line — there were dips (step 70: 0.095, step 120: 0.185). That's normal in RL. The model sometimes "forgets" a strategy temporarily before consolidating it. The trend line was always upward.

---

## Before vs. After: The Same Contract

To really show the learning, I tested both the untrained base model and the RL-trained model on the same vulnerable contract:

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

**Untrained model output:**
> *"1. Reentrancy: The withdraw function can be reentered through an external call before it has fully executed..."*

Okay, it *mentioned* reentrancy but the fix it suggested was actually wrong — it told me to check the balance *after* the call, which is exactly the bug.

**RL-trained model output:**
> *"VULNERABILITY: Reentrancy Attack*
> *SEVERITY: High*
> *LOCATION: withdraw() function — external call before state update*
> *IMPACT: Attacker can repeatedly call withdraw() before balances[msg.sender] is zeroed, draining all funds*
> *FIX: Apply checks-effects-interactions pattern — update balances[msg.sender] BEFORE the external call, or use OpenZeppelin's ReentrancyGuard"*

That's a real audit report. Structured, specific, actionable. The model learned not just *what* to detect but *how* to explain it.

---

## What I Learned About GRPO

A few things surprised me during this process:

**1. The reward function design matters more than anything else.** I spent more time tuning the reward components than on any other part of the project. Get the reward wrong and the model learns the wrong thing. The anti-hallucination penalty was a late addition — before it, the model kept saying "no bugs found" to avoid getting penalized for wrong answers.

**2. Small models can learn surprisingly well.** 1.5B parameters is tiny by modern standards. But with the right task structure and reward signal, it learned to write better security reports in under 2 hours. I didn't need GPT-4.

**3. GRPO is genuinely efficient.** Because it doesn't need a separate value/critic model, the whole thing fit in ~2 GB of GPU memory. You can replicate this experiment on any free Colab session.

**4. Dips in the reward curve are normal.** At step 70, reward dropped to 0.095. I almost stopped the training. Don't. RL is noisy by nature — the model is exploring. The trend matters, not individual steps.

---

## What's Next

This is version 1 of the model, trained for the hackathon. The reward is still relatively low (0.329 out of a possible 1.5) — there's a lot of room to improve:

- **Train longer** — 500+ steps with a curriculum (easy contracts → hard contracts)
- **Better base model** — Qwen2.5-3B or 7B could learn faster and plateau higher
- **Richer reward signal** — add rewards for detecting multiple vulnerabilities in one contract
- **Dataset diversity** — right now the environment generates contracts with one vulnerability type; real contracts are messier

The bigger vision: an open-source AI auditor that developers can run locally, that catches the obvious bugs before they go to a paid audit, and that produces reports that are actually useful — not just "vulnerability detected" but here's what an attacker would do and here's exactly how to fix it.

---

## Try It Yourself

Everything is open source and free to run:

- 🤗 **Live Demo**: [huggingface.co/spaces/Gopichand0516/smart-contract-auditor](https://huggingface.co/spaces/Gopichand0516/smart-contract-auditor)
- 🤗 **Model Weights**: [huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo](https://huggingface.co/Gopichand0516/smart-contract-audit-qwen-grpo)
- 📓 **Colab Notebook**: [Open and run it yourself](https://colab.research.google.com/drive/1TPfiFJC9rGpS8ZBETGL5XSUXf-Xltsd6?usp=drive_link)
- 💻 **GitHub**: [smart-contract-audit-env](https://github.com/gopichandchalla16/smart-contract-audit-env)

If you run it and improve on 0.329, I want to know. Tweet me at [@GopichandAI](https://twitter.com/GopichandAI).

---

*Built at the Meta PyTorch OpenEnv Community Hackathon, April 2026.*
*Gopichand Challa — CSE Graduate | Web3 + AI Builder | Bengaluru, India*
