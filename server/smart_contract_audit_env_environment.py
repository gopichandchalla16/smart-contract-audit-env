from models import Action, Observation, StepResult, RewardInfo
from typing import Dict

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
                "state updated after external call", "withdraw reentrancy"
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
                "checks-effects-interactions", "withdraw reentrancy"
            ],
            "missing access control": [
                "missing access control", "no access control", "unauthorized",
                "unprotected function", "anyone can call", "no modifier",
                "missing onlyOwner", "no authentication", "public drain",
                "emergencyDrain", "unguarded", "no restriction"
            ],
            "tx.origin": [
                "tx.origin", "tx origin", "origin authentication",
                "phishing attack", "tx.origin bypass", "origin bypass",
                "use msg.sender instead", "authentication bypass",
                "tx.origin vulnerability", "origin vs sender"
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
                "unsafe type cast", "arithmetic issue"
            ],
            "oracle manipulation": [
                "oracle manipulation", "price manipulation", "flash loan attack",
                "single price source", "price oracle", "manipulable oracle",
                "oracle attack", "single oracle", "price feed manipulation",
                "untrusted oracle", "oracle exploit"
            ],
            "reentrancy": [
                "reentrancy", "re-entrancy", "reentrant", "recursive call",
                "external call before state", "CEI violation",
                "borrow reentrancy", "reentrancy on borrow"
            ],
            "missing access control": [
                "missing access control", "no access control", "unauthorized liquidation",
                "unprotected liquidate", "anyone can liquidate", "no modifier",
                "missing onlyOwner", "unguarded liquidation", "liquidation access",
                "no restriction on liquidate"
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
                "current_score": 0.0,
                "last_feedback": "",
                "last_findings_count": 0
            }

    def _match_vulnerability(self, finding: str, vuln_key: str, contract: dict) -> bool:
        """Semantic matching: checks synonyms, partial phrases, and line-number hints."""
        finding_lower = finding.lower()
        synonyms = contract.get("vuln_synonyms", {}).get(vuln_key, [vuln_key])
        for synonym in synonyms:
            if synonym.lower() in finding_lower:
                return True
        return False

    def _grade(self, action: Action, task_id: str) -> dict:
        """Grade an action against the expected vulnerabilities using semantic matching."""
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

        # Line number bonus: +0.05 per correctly referenced vulnerable line
        line_bonus = 0.0
        if action.vulnerable_lines and contract.get("vulnerable_lines"):
            correct_lines = set(contract["vulnerable_lines"])
            submitted_lines = set(action.vulnerable_lines)
            matching_lines = correct_lines & submitted_lines
            line_bonus = min(0.1, len(matching_lines) * 0.05)

        # Explanation quality bonus: +0.05 if explanation is substantive (>30 chars)
        explanation_bonus = 0.05 if action.explanation and len(action.explanation) > 30 else 0.0

        false_positives = max(0, len(action.findings) - true_positives)
        missed = len(expected_vulns) - true_positives

        base_score = true_positives / len(expected_vulns) if expected_vulns else 0.0
        fp_penalty = min(0.3, false_positives * 0.1)
        score = max(0.0, min(1.0, base_score + line_bonus + explanation_bonus - fp_penalty))

        return {
            "score": round(score, 4),
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
            "current_score": 0.0,
            "last_feedback": "",
            "last_findings_count": 0
        }
        contract = CONTRACTS[task_id]
        return Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=0.0,
            last_feedback="",
            step_count=0,
            max_steps=5
        )

    def step(self, action: Action, task_id: str = "easy") -> StepResult:
        contract = CONTRACTS[task_id]
        state = self.states[task_id]
        state["step_count"] += 1

        graded = self._grade(action, task_id)
        score = graded["score"]
        true_positives = graded["true_positives"]
        false_positives = graded["false_positives"]
        missed = graded["missed"]

        # Delta reward — reward improvement, penalize stagnation
        prev_score = state["current_score"]
        delta = score - prev_score
        if delta <= 0 and state["step_count"] > 1:
            reward_value = max(0.0, score - 0.05)
        else:
            reward_value = score

        state["current_score"] = score
        state["last_findings_count"] = len(action.findings)

        # Rich feedback with hints
        expected_vulns = contract["vulnerabilities"]
        if score >= 1.0:
            feedback = "Perfect audit! All vulnerabilities found with precise line references."
        elif true_positives == len(expected_vulns):
            feedback = f"All {true_positives} vulnerabilities found! Reduce false positives to improve score. FP count: {false_positives}."
        elif true_positives > 0:
            unmatched = [v for v in expected_vulns if v not in graded["matched_vulns"]]
            hints = ", ".join(unmatched[:2])
            feedback = (
                f"Found {true_positives}/{len(expected_vulns)} vulnerabilities. "
                f"Still missing: [{hints}]. "
                f"Tip: check state-change ordering, access modifiers, and oracle trust."
            )
        else:
            feedback = (
                "No correct vulnerabilities found. "
                "Hint: look for external calls before state updates, unguarded public functions, "
                "and untrusted external price sources."
            )

        state["last_feedback"] = feedback
        done = (score >= 1.0) or (state["step_count"] >= 5)

        obs = Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=score,
            last_feedback=feedback,
            step_count=state["step_count"],
            max_steps=5
        )

        reward = RewardInfo(
            value=round(reward_value, 4),
            cumulative=round(score, 4),
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
                "explanation_bonus": graded["explanation_bonus"]
            }
        )

    def state(self, task_id: str = "easy") -> Observation:
        contract = CONTRACTS[task_id]
        state = self.states[task_id]
        return Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=state["current_score"],
            last_feedback=state["last_feedback"],
            step_count=state["step_count"],
            max_steps=5
        )
