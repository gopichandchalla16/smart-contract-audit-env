from models import Action, Observation, StepResult, RewardInfo
from typing import Dict

# ---------------------------------------------------------------------------
# VALIDATOR REQUIREMENT: scores MUST be STRICTLY between 0 and 1
# Never exactly 0.0 or exactly 1.0
# Clamped to [0.01, 0.99] at every return point
# ---------------------------------------------------------------------------
SCORE_MIN = 0.01
SCORE_MAX = 0.99

def clamp(score: float) -> float:
    """Clamp score to strictly open interval (0.01, 0.99). Never 0.0 or 1.0."""
    try:
        v = float(score)
    except Exception:
        return SCORE_MIN
    if v <= 0.0:
        return SCORE_MIN
    if v >= 1.0:
        return SCORE_MAX
    return round(v, 4)


CONTRACTS = {
    "easy": {
        "code": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        // VULNERABILITY: External call before state update (Reentrancy)
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] -= amount;  // State updated AFTER external call
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
""",
        "vulnerabilities": ["reentrancy"],
        "vuln_synonyms": {
            "reentrancy": [
                "reentrancy", "re-entrancy", "reentrant", "reentrancy attack",
                "external call before state update", "call before balance update",
                "checks-effects-interactions", "CEI violation", "recursive call",
                "state updated after external call", "withdraw reentrancy",
                "reentrance", "reentrant attack", "cross-function reentrancy",
                "msg.sender.call before", "call before update", "unsafe external call",
                "fallback reentrancy", "callback attack", "send before update",
                "transfer before update", "balance not updated", "state not updated before call",
                "violates CEI", "interactions before effects"
            ]
        },
        "vulnerable_lines": [14],
        "description": "Audit this simple bank contract and find the critical vulnerability."
    },

    "medium": {
        "code": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DeFiVault {
    mapping(address => uint256) public balances;
    address public owner;
    uint256 public totalDeposits;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
    }

    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        // VULNERABILITY 1: Reentrancy - external call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
    }

    // VULNERABILITY 2: Missing access control - anyone can call this
    function emergencyDrain() public {
        payable(msg.sender).transfer(address(this).balance);
    }

    // VULNERABILITY 3: tx.origin authentication bypass
    function adminWithdraw(uint256 amount) public {
        require(tx.origin == owner, "Not owner");
        payable(msg.sender).transfer(amount);
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
""",
        "vulnerabilities": ["reentrancy", "missing access control", "tx.origin"],
        "vuln_synonyms": {
            "reentrancy": [
                "reentrancy", "re-entrancy", "reentrant", "recursive call",
                "external call before state update", "CEI violation",
                "checks-effects-interactions", "withdraw reentrancy",
                "reentrance", "callback attack", "fallback attack",
                "call before balance", "state updated after", "unsafe call",
                "msg.sender.call before balance"
            ],
            "missing access control": [
                "missing access control", "no access control", "unauthorized",
                "unprotected function", "anyone can call", "no modifier",
                "missing onlyOwner", "no authentication", "public drain",
                "emergencyDrain", "unguarded", "no restriction",
                "no access modifier", "lack of access control", "open function",
                "no role check", "missing modifier", "publicly callable",
                "no owner check", "unrestricted access", "drain without auth",
                "unprotected drain", "no permission check"
            ],
            "tx.origin": [
                "tx.origin", "tx origin", "origin authentication",
                "phishing attack", "tx.origin bypass", "origin bypass",
                "use msg.sender instead", "authentication bypass",
                "tx.origin vulnerability", "origin vs sender",
                "tx.origin phishing", "transaction origin", "origin check",
                "origin instead of sender", "insecure authentication",
                "use msg.sender", "tx origin attack", "origin spoofing"
            ]
        },
        "vulnerable_lines": [21, 28, 33],
        "description": "Audit this DeFi vault and find all 3 vulnerabilities."
    },

    "hard": {
        "code": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IPriceOracle {
    function getPrice() external view returns (uint256);
}

contract ComplexDeFi {
    mapping(address => uint256) public balances;
    mapping(address => uint256) public borrowings;
    IPriceOracle public oracle;
    address public admin;
    uint256 public totalSupply;

    constructor(address _oracle) {
        oracle = IPriceOracle(_oracle);
        admin = msg.sender;
    }

    function deposit(uint256 amount) public {
        balances[msg.sender] += amount;
        // VULNERABILITY 1: Integer overflow (pre-0.8 pattern, unsafe cast)
        totalSupply += uint256(int256(amount) - 1);
    }

    function borrow(uint256 amount) public {
        uint256 price = oracle.getPrice();
        // VULNERABILITY 2: Oracle manipulation - single source price
        uint256 collateral = balances[msg.sender] * price;
        require(collateral >= amount * 2, "Insufficient collateral");
        borrowings[msg.sender] += amount;
        // VULNERABILITY 3: Reentrancy on borrow
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        totalSupply -= amount;
    }

    function liquidate(address user) public {
        // VULNERABILITY 4: Missing access control on liquidation
        uint256 price = oracle.getPrice();
        uint256 collateralValue = balances[user] * price;
        require(collateralValue < borrowings[user], "Not liquidatable");
        balances[user] = 0;
        borrowings[user] = 0;
        payable(msg.sender).transfer(collateralValue);
    }

    function adminFunction() public {
        require(msg.sender == admin);
        totalSupply = 0;
    }
}
""",
        "vulnerabilities": ["integer overflow", "oracle manipulation", "reentrancy", "missing access control"],
        "vuln_synonyms": {
            "integer overflow": [
                "integer overflow", "overflow", "unsafe cast", "int256 cast",
                "unsafe integer conversion", "arithmetic overflow",
                "uint256 int256", "unsafe arithmetic", "integer underflow",
                "unsafe type cast", "arithmetic issue", "int256 to uint256",
                "unsafe downcast", "signedness issue", "type confusion",
                "negative cast", "arithmetic bug", "numeric overflow",
                "unsafe conversion", "integer bug"
            ],
            "oracle manipulation": [
                "oracle manipulation", "price manipulation", "flash loan attack",
                "single price source", "price oracle", "manipulable oracle",
                "oracle attack", "single oracle", "price feed manipulation",
                "untrusted oracle", "oracle exploit", "single source of truth",
                "centralized oracle", "price feed attack", "twap missing",
                "no price aggregation", "oracle dependency", "price manipulation risk",
                "on-chain price oracle", "single price feed", "price spoofing"
            ],
            "reentrancy": [
                "reentrancy", "re-entrancy", "reentrant", "recursive call",
                "external call before state", "CEI violation",
                "borrow reentrancy", "reentrancy on borrow",
                "call before update", "state updated after call",
                "reentrance", "callback exploit", "fallback exploit",
                "cross-function reentrancy", "borrow callback"
            ],
            "missing access control": [
                "missing access control", "no access control", "unauthorized liquidation",
                "unprotected liquidate", "anyone can liquidate", "no modifier",
                "missing onlyOwner", "unguarded liquidation", "liquidation access",
                "no restriction on liquidate", "open liquidation", "unrestricted liquidate",
                "no role", "no auth on liquidate", "public liquidation",
                "lack of access control", "no permission"
            ]
        },
        "vulnerable_lines": [23, 29, 34, 42],
        "description": "Audit this complex DeFi protocol and find all 4 critical vulnerabilities."
    }
}


class SmartContractAuditEnv:
    def __init__(self):
        self.states: Dict[str, dict] = {}
        self._init_states()

    def _init_states(self):
        for task_id in ["easy", "medium", "hard"]:
            self.states[task_id] = {
                "step_count": 0,
                "current_score": SCORE_MIN,
                "last_feedback": "",
                "last_findings_count": 0,
                "best_score": SCORE_MIN
            }

    def _match_vulnerability(self, finding: str, vuln_key: str, contract: dict) -> bool:
        finding_lower = finding.lower()
        synonyms = contract.get("vuln_synonyms", {}).get(vuln_key, [vuln_key])
        for synonym in synonyms:
            if synonym.lower() in finding_lower:
                return True
        key_words = [w for w in vuln_key.lower().split() if len(w) > 3]
        if len(key_words) >= 2:
            matches = sum(1 for w in key_words if w in finding_lower)
            if matches >= 2:
                return True
        return False

    def _grade(self, action: Action, task_id: str) -> dict:
        contract = CONTRACTS[task_id]
        expected_vulns = contract["vulnerabilities"]

        true_positives = 0
        matched_vulns = set()

        for vuln in expected_vulns:
            for finding in action.findings:
                if self._match_vulnerability(finding, vuln, contract):
                    if vuln not in matched_vulns:
                        true_positives += 1
                        matched_vulns.add(vuln)
                    break

        # Line number bonus
        line_bonus = 0.0
        if action.vulnerable_lines and contract.get("vulnerable_lines"):
            correct_lines = set(contract["vulnerable_lines"])
            submitted_lines = set(action.vulnerable_lines)
            matching_lines = correct_lines & submitted_lines
            line_bonus = min(0.06, len(matching_lines) * 0.03)

        # Explanation quality bonus
        explanation_bonus = 0.03 if action.explanation and len(action.explanation) > 50 else 0.0

        false_positives = max(0, len(action.findings) - true_positives)
        missed = len(expected_vulns) - true_positives

        base_score = true_positives / len(expected_vulns) if expected_vulns else SCORE_MIN
        fp_penalty = min(0.3, false_positives * 0.1)
        raw_score = base_score + line_bonus + explanation_bonus - fp_penalty

        # TRIPLE SAFETY: clamp strictly between 0.01 and 0.99 — NEVER 0.0 or 1.0
        score = clamp(raw_score)

        return {
            "score": score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "missed": missed,
            "matched_vulns": list(matched_vulns),
            "line_bonus": line_bonus,
            "explanation_bonus": explanation_bonus
        }

    def reset(self, task_id: str = "easy") -> Observation:
        self.states[task_id] = {
            "step_count": 0,
            "current_score": SCORE_MIN,
            "last_feedback": "",
            "last_findings_count": 0,
            "best_score": SCORE_MIN
        }
        contract = CONTRACTS[task_id]
        return Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=SCORE_MIN,
            last_feedback="",
            step_count=0,
            max_steps=5
        )

    def step(self, action: Action, task_id: str = "easy") -> StepResult:
        contract = CONTRACTS[task_id]
        state = self.states[task_id]
        state["step_count"] += 1

        graded = self._grade(action, task_id)
        score        = graded["score"]  # already clamped by _grade()
        true_positives  = graded["true_positives"]
        false_positives = graded["false_positives"]
        missed          = graded["missed"]

        prev_best = state.get("best_score", SCORE_MIN)
        state["best_score"] = max(prev_best, score)

        prev_score = state["current_score"]
        delta = score - prev_score

        # Reward value: always clamped
        if delta > 0 or state["step_count"] == 1:
            reward_value = clamp(score)
        else:
            reward_value = clamp(max(SCORE_MIN, score - 0.05))

        state["current_score"] = score
        state["last_findings_count"] = len(action.findings)

        # Feedback
        expected_vulns = contract["vulnerabilities"]
        vuln_hints = {
            "reentrancy":             "Look for external calls (msg.sender.call) before state updates",
            "missing access control": "Check for public functions without onlyOwner or role modifiers",
            "tx.origin":              "Check authentication using tx.origin instead of msg.sender",
            "integer overflow":       "Look for unsafe int256<->uint256 casts or arithmetic without SafeMath",
            "oracle manipulation":    "Check for single external price sources without TWAP or aggregation",
        }

        if score >= SCORE_MAX:
            feedback = "Excellent audit! All vulnerabilities found with precise analysis."
        elif true_positives == len(expected_vulns):
            feedback = f"All {true_positives} vulnerabilities found! Reduce false positives to maximise score."
        elif true_positives > 0:
            unmatched = [v for v in expected_vulns if v not in graded["matched_vulns"]]
            hint_msgs = [vuln_hints.get(v, f"Check for {v}") for v in unmatched[:2]]
            hints_str = " | ".join(hint_msgs)
            feedback = (
                f"Found {true_positives}/{len(expected_vulns)} vulnerabilities. "
                f"Still missing: {unmatched}. "
                f"Hints: {hints_str}."
            )
        else:
            all_hints = " | ".join([vuln_hints.get(v, v) for v in expected_vulns])
            feedback = (
                f"No correct vulnerabilities found. "
                f"Hints for all {len(expected_vulns)} vulns: {all_hints}."
            )

        state["last_feedback"] = feedback
        done = (score >= SCORE_MAX) or (state["step_count"] >= 5)

        obs = Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=clamp(score),
            last_feedback=feedback,
            step_count=state["step_count"],
            max_steps=5
        )

        reward = RewardInfo(
            value=clamp(reward_value),
            cumulative=clamp(score),
            message=feedback,
            true_positives=true_positives,
            false_positives=false_positives,
            missed_vulnerabilities=missed
        )

        return StepResult(
            observation=obs,
            reward=reward,
            done=done,
            info={
                "step": state["step_count"],
                "true_positives": true_positives,
                "false_positives": false_positives,
                "missed": missed,
                "matched_vulns": graded["matched_vulns"],
                "line_bonus": graded["line_bonus"],
                "explanation_bonus": graded["explanation_bonus"],
                "best_score": state["best_score"]
            }
        )

    def state(self, task_id: str = "easy") -> Observation:
        contract = CONTRACTS[task_id]
        s = self.states[task_id]
        return Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=clamp(s["current_score"]),
            last_feedback=s["last_feedback"],
            step_count=s["step_count"],
            max_steps=5
        )
