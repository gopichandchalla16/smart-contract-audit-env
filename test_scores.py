import requests
import json

BASE = "https://gopichand0516-smart-contract-audit-env.hf.space"

actions = {
    "easy": {
        "findings": ["reentrancy vulnerability - external call before state update in withdraw()"],
        "severity": ["high"],
        "vulnerable_lines": [14],
        "explanation": "REENTRANCY: withdraw() calls msg.sender.call before updating balances. CEI violation. FIX: Use ReentrancyGuard."
    },
    "medium": {
        "findings": [
            "reentrancy in withdraw() CEI violation",
            "missing access control emergencyDrain no onlyOwner",
            "tx.origin authentication bypass phishing"
        ],
        "severity": ["high", "high", "high"],
        "vulnerable_lines": [21, 28, 33],
        "explanation": "Three vulnerabilities found with CEI analysis."
    },
    "hard": {
        "findings": [
            "integer overflow unsafe int256 to uint256 cast deposit",
            "oracle manipulation single price source flash loan risk",
            "reentrancy external call before totalSupply update borrow CEI",
            "missing access control liquidate no modifier anyone can call"
        ],
        "severity": ["high", "high", "high", "medium"],
        "vulnerable_lines": [23, 29, 34, 42],
        "explanation": "All 4 vulnerabilities found with full CEI and fix recommendations."
    }
}

all_pass = True
for t in ["easy", "medium", "hard"]:
    requests.post(BASE + "/reset", params={"task_id": t}, timeout=25)
    r = requests.post(BASE + "/step", json=actions[t], params={"task_id": t}, timeout=25)
    d = r.json()
    score = d["reward"]["cumulative"]
    ok = score > 0.0 and score < 1.0
    if not ok:
        all_pass = False
    status = "PASS" if ok else "FAIL"
    print("task=" + t + " score=" + str(round(score, 2)) + " | " + status)

print()
if all_pass:
    print("PHASE 2 PASS - ALL SCORES IN RANGE")
else:
    print("PHASE 2 FAIL")