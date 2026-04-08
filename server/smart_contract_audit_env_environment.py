from models import Action, Observation, StepResult, RewardInfo
from typing import Dict

SCORE_MIN = 0.01
SCORE_MAX = 0.99


def clamp(score) -> float:
    """Clamp to strictly open (0, 1). CRITICAL: uses truncation not rounding."""
    try:
        v = float(score)
    except Exception:
        return SCORE_MIN
    if v <= 0.0:
        return SCORE_MIN
    if v >= 1.0:
        return SCORE_MAX
    v = int(v * 10000) / 10000.0
    if v <= 0.0:
        return SCORE_MIN
    if v >= 1.0:
        return SCORE_MAX
    return v


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
        "description": "Audit this simple bank contract and find the critical vulnerability. Examine the withdraw() function for ordering issues between external calls and state updates."
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

    // VULNERABILITY 2: Missing access control - no onlyOwner modifier
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
        "description": "Audit this DeFi vault contract and find all 3 critical vulnerabilities: a reentrancy bug in withdraw(), a missing access control on emergencyDrain(), and a tx.origin authentication bypass in adminWithdraw()."
    },
    "hard": {
        "code": """
// SPDX-License-Identifier: MIT
pragma solidity ^0.7.6;

/// @title RiskyLend - A DeFi lending protocol with multiple vulnerabilities
/// @notice This contract is intentionally vulnerable for security research
interface IOracle {
    function getPrice(address token) external view returns (uint256);
}
interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract RiskyLend {
    struct Position {
        uint256 collateral;
        uint256 debt;
        uint256 lastInterestBlock;
    }

    mapping(address => Position) public positions;
    mapping(address => uint256) public liquidityProviders;
    IOracle  public priceOracle;
    address  public governance;
    address  public implementation;
    uint256  public totalLiquidity;
    uint256  public constant COLLATERAL_RATIO = 150; // 150%

    modifier onlyGovernance() {
        require(msg.sender == governance, "Not governance");
        _;
    }

    constructor(address _oracle, address _governance) {
        priceOracle  = IOracle(_oracle);
        governance   = _governance;
    }

    // VULNERABILITY 1: Reentrancy
    // External ETH transfer fires BEFORE pos.collateral is decremented
    // Attacker's fallback() can recursively call withdrawCollateral() to drain all collateral
    function withdrawCollateral(uint256 amount) external {
        Position storage pos = positions[msg.sender];
        require(pos.collateral >= amount, "Insufficient collateral");
        require(pos.debt == 0, "Outstanding debt");
        // CEI VIOLATION: Interaction happens before Effect
        (bool ok, ) = msg.sender.call{value: amount}("");  // line 50: sends ETH first
        require(ok, "ETH transfer failed");
        pos.collateral -= amount;  // line 52: state updated AFTER external call
    }

    // VULNERABILITY 2: Oracle Manipulation / Flash Loan Attack Surface
    // Uses single spot price from priceOracle - susceptible to flash loan manipulation
    // Attacker borrows huge flash loan, inflates collateral token price in AMM,
    // borrows against inflated price, then repays flash loan. Protocol left with bad debt.
    function borrow(address token, uint256 amount) external {
        // Single spot price oracle - no TWAP, no aggregation
        uint256 spotPrice = priceOracle.getPrice(token);  // line 60: manipulable single source
        uint256 collateralValue = positions[msg.sender].collateral * spotPrice;
        require(
            collateralValue >= (amount * COLLATERAL_RATIO) / 100,
            "Insufficient collateral ratio"
        );
        positions[msg.sender].debt += amount;
        totalLiquidity -= amount;
        IERC20(token).transfer(msg.sender, amount);
    }

    // VULNERABILITY 3: Delegatecall Privilege Escalation
    // executeUpgrade() is callable by ANYONE - no access control modifier
    // Attacker can set a malicious implementation and call executeUpgrade with
    // a payload that overwrites governance slot to attacker address
    function upgradeImplementation(address newImpl) external onlyGovernance {
        implementation = newImpl;
    }
    function executeUpgrade(bytes calldata data) external {
        // Missing onlyGovernance - anyone can trigger arbitrary delegatecall
        (bool ok, ) = implementation.delegatecall(data);  // line 79: unrestricted delegatecall
        require(ok, "Delegatecall failed");
    }

    // VULNERABILITY 4: Unchecked Low-Level Call Return Value
    // debt is decremented unconditionally even if the token transfer fails
    // Attacker can repay debt on a malicious ERC20 that always returns false,
    // effectively clearing their debt without paying
    function repayDebt(address token, uint256 amount) external {
        positions[msg.sender].debt -= amount;  // debt cleared first
        // Low-level call return value is NOT checked - silent failure
        token.call(  // line 89: unchecked return value
            abi.encodeWithSignature(
                "transferFrom(address,address,uint256)",
                msg.sender, address(this), amount
            )
        );
    }

    // VULNERABILITY 5: Missing Access Control on Oracle Setter
    // setOracle() is public with NO modifier - anyone can replace the oracle
    // Attacker deploys malicious oracle returning arbitrary prices and calls setOracle()
    // This enables full protocol manipulation: borrow unlimited amounts
    function setOracle(address newOracle) public {  // line 99: no onlyGovernance modifier
        priceOracle = IOracle(newOracle);
    }

    function depositCollateral() external payable {
        positions[msg.sender].collateral += msg.value;
    }

    function provideLiquidity() external payable {
        liquidityProviders[msg.sender] += msg.value;
        totalLiquidity += msg.value;
    }
}
""",
        "vulnerabilities": [
            "reentrancy",
            "oracle manipulation",
            "delegatecall privilege escalation",
            "unchecked return value",
            "missing access control"
        ],
        "vuln_synonyms": {
            "reentrancy": [
                "reentrancy", "re-entrancy", "reentrant", "CEI violation",
                "external call before state update", "call before collateral update",
                "withdrawCollateral reentrancy", "recursive call",
                "checks-effects-interactions", "state updated after",
                "fallback attack", "unsafe external call", "reentrance",
                "collateral drain", "ETH before state", "interaction before effect"
            ],
            "oracle manipulation": [
                "oracle manipulation", "price manipulation", "flash loan",
                "single oracle", "single price source", "spot price",
                "no TWAP", "TWAP missing", "price feed manipulation",
                "centralized oracle", "oracle exploit", "price spoofing",
                "oracle dependency", "on-chain price", "single spot",
                "flash loan attack", "AMM price manipulation", "price oracle attack",
                "manipulable oracle", "untrusted price feed"
            ],
            "delegatecall privilege escalation": [
                "delegatecall", "privilege escalation", "unsafe delegatecall",
                "arbitrary delegatecall", "unrestricted delegatecall",
                "executeUpgrade", "delegatecall exploit", "upgrade attack",
                "proxy attack", "storage collision",
                "delegatecall without access control", "unprotected delegatecall",
                "delegatecall escalation", "delegatecall no auth"
            ],
            "unchecked return value": [
                "unchecked return value", "unchecked call", "return value not checked",
                "low-level call", "ignored return", "unchecked low-level call",
                "call return ignored", "failed call not detected", "token.call unchecked",
                "unsafe call", "return value ignored", "low level call return",
                "unchecked low level", "silent failure", "repayDebt unchecked"
            ],
            "missing access control": [
                "missing access control", "no access control", "setOracle",
                "unprotected setOracle", "anyone can set oracle", "no modifier",
                "missing onlyGovernance", "unauthorized", "unrestricted access",
                "lack of access control", "open function", "no permission check",
                "public oracle setter", "oracle setter unprotected", "no governance check",
                "unguarded setOracle", "oracle access control"
            ]
        },
        "vulnerable_lines": [50, 60, 79, 89, 99],
        "description": (
            "Audit RiskyLend — a real-world DeFi lending protocol. "
            "Find all 5 critical vulnerabilities: "
            "(1) reentrancy in withdrawCollateral(), "
            "(2) flash-loan oracle manipulation in borrow(), "
            "(3) delegatecall privilege escalation in executeUpgrade(), "
            "(4) unchecked low-level call return in repayDebt(), "
            "(5) missing access control on setOracle(). "
            "For each: name the vulnerability, assign severity, identify the line number, and explain the attack vector."
        )
    }
}


# ─── Sophisticated grading constants ──────────────────────────────────────────

SEVERITY_WEIGHTS = {
    "reentrancy":                      "high",
    "oracle manipulation":             "high",
    "delegatecall privilege escalation": "high",
    "integer overflow":                "high",
    "tx.origin":                       "high",
    "missing access control":          "medium",
    "unchecked return value":          "medium",
}

SEVERITY_SYNONYMS = {
    "high":   ["high", "critical", "severe", "critical severity", "high severity"],
    "medium": ["medium", "moderate", "medium severity"],
    "low":    ["low", "minor", "informational", "low severity"],
}

TECH_KEYWORDS = [
    "CEI", "checks-effects-interactions", "reentrancy guard", "nonReentrant",
    "TWAP", "oracle aggregator", "price manipulation", "flash loan",
    "delegatecall", "storage slot", "onlyGovernance", "onlyOwner",
    "tx.origin", "msg.sender", "integer overflow", "SafeMath",
    "access control", "modifier", "return value", "low-level call",
    "ReentrancyGuard", "SafeERC20", "Chainlink", "attack vector",
    "exploit", "mitigation", "recommendation", "severity",
]


class SmartContractAuditEnv:
    def __init__(self):
        self.states: Dict[str, dict] = {}
        self._init_states()

    def _init_states(self):
        for task_id in ["easy", "medium", "hard"]:
            self.states[task_id] = {
                "step_count":          0,
                "current_score":       SCORE_MIN,
                "last_feedback":       "",
                "last_findings_count": 0,
                "best_score":          SCORE_MIN,
            }

    def _match_vulnerability(self, finding: str, vuln_key: str, contract: dict) -> bool:
        finding_lower = finding.lower()
        synonyms = contract.get("vuln_synonyms", {}).get(vuln_key, [vuln_key])
        for synonym in synonyms:
            if synonym.lower() in finding_lower:
                return True
        key_words = [w for w in vuln_key.lower().split() if len(w) > 3]
        if len(key_words) >= 2:
            if sum(1 for w in key_words if w in finding_lower) >= 2:
                return True
        return False

    def _grade(self, action: Action, task_id: str) -> dict:
        contract       = CONTRACTS[task_id]
        expected_vulns = contract["vulnerabilities"]
        findings       = action.findings or []
        severities     = action.severity  if hasattr(action, "severity") and action.severity else []
        sub_lines      = action.vulnerable_lines or []
        explanation    = action.explanation or ""

        # ── True / False positives ─────────────────────────────────────────────
        true_positives = 0
        matched_vulns  = []
        for vuln in expected_vulns:
            for finding in findings:
                if self._match_vulnerability(finding, vuln, contract):
                    true_positives += 1
                    matched_vulns.append(vuln)
                    break

        false_positives = max(0, len(findings) - true_positives)
        missed          = len(expected_vulns) - true_positives

        # ── Base score ────────────────────────────────────────────────────────
        base = (true_positives / len(expected_vulns)) if expected_vulns else SCORE_MIN

        # ── Severity bonus / penalty (+0.03 correct, -0.02 wrong) ─────────────
        severity_bonus = 0.0
        wrong_sev_pen  = 0.0
        for i, vuln in enumerate(matched_vulns):
            expected_sev = SEVERITY_WEIGHTS.get(vuln, "medium")
            submitted_sev = severities[i].lower().strip() if i < len(severities) else ""
            if submitted_sev and submitted_sev in SEVERITY_SYNONYMS.get(expected_sev, []):
                severity_bonus += 0.03
            elif submitted_sev:
                wrong_sev_pen  += 0.02
        severity_bonus = min(severity_bonus, 0.12)

        # ── Line-number bonus (+0.015 per correct line, cap 0.06) ─────────────
        correct_lines = set(contract.get("vulnerable_lines", []))
        hit_lines     = correct_lines & set(sub_lines)
        line_bonus    = min(0.06, len(hit_lines) * 0.015)

        # ── Explanation quality bonus ──────────────────────────────────────────
        explanation_bonus = 0.0
        if len(explanation) > 300:
            explanation_bonus = 0.05
        elif len(explanation) > 100:
            explanation_bonus = 0.03
        elif len(explanation) > 30:
            explanation_bonus = 0.01

        kw_hits       = sum(1 for kw in TECH_KEYWORDS if kw.lower() in explanation.lower())
        keyword_bonus = min(0.04, kw_hits * 0.01)

        # ── False-positive penalty (−0.12 each, cap 0.35) ─────────────────────
        fp_penalty = min(0.35, false_positives * 0.12)

        # ── Combine and hard-cap at 0.97 ──────────────────────────────────────
        raw = (
            base
            + severity_bonus
            + line_bonus
            + explanation_bonus
            + keyword_bonus
            - fp_penalty
            - wrong_sev_pen
        )
        raw   = max(SCORE_MIN, min(raw, 0.97))
        score = clamp(raw)

        return {
            "score":             score,
            "true_positives":    true_positives,
            "false_positives":   false_positives,
            "missed":            missed,
            "matched_vulns":     matched_vulns,
            "severity_bonus":    round(severity_bonus, 4),
            "line_bonus":        round(line_bonus, 4),
            "explanation_bonus": round(explanation_bonus, 4),
            "keyword_bonus":     round(keyword_bonus, 4),
            "fp_penalty":        round(fp_penalty, 4),
        }

    def grade(self, task_id: str = "easy") -> float:
        return clamp(self.states.get(task_id, {}).get("current_score", SCORE_MIN))

    def reset(self, task_id: str = "easy") -> Observation:
        self.states[task_id] = {
            "step_count":          0,
            "current_score":       SCORE_MIN,
            "last_feedback":       "",
            "last_findings_count": 0,
            "best_score":          SCORE_MIN,
        }
        contract = CONTRACTS[task_id]
        return Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=SCORE_MIN,
            last_feedback="",
            step_count=0,
            max_steps=5,
        )

    def _build_feedback(self, graded: dict, task_id: str, step: int) -> str:
        contract       = CONTRACTS[task_id]
        expected_vulns = contract["vulnerabilities"]
        tp             = graded["true_positives"]
        total          = len(expected_vulns)
        matched        = graded["matched_vulns"]
        score          = graded["score"]

        HINTS = {
            "reentrancy":                        "Look for external calls (call/send/transfer) BEFORE state updates — CEI violation.",
            "missing access control":            "Check for public/external functions with NO onlyOwner or onlyGovernance modifier.",
            "tx.origin":                         "Search for tx.origin used in require() for authentication instead of msg.sender.",
            "integer overflow":                  "Look for unsafe int256 <-> uint256 type casts or arithmetic without SafeMath.",
            "oracle manipulation":               "Check if borrow/pricing logic uses a SINGLE spot price source (flash-loan vulnerable).",
            "delegatecall privilege escalation": "Find delegatecall to an external address — check whether it has access control.",
            "unchecked return value":             "Search for low-level .call() whose bool return value is never checked.",
        }

        if score >= 0.95:
            return (
                f"PERFECT AUDIT! Score={score:.4f}. All {total} vulnerabilities identified with correct severity, "
                f"line numbers, and technical explanation. Well done!"
            )

        if tp == total:
            return (
                f"All {total}/{total} vulnerabilities found! Score={score:.4f}. "
                f"Improve score by: (1) adding correct severity labels (high/medium/low), "
                f"(2) including exact line numbers, (3) removing any false positives, "
                f"(4) expanding technical explanation with attack vectors."
            )

        unmatched = [v for v in expected_vulns if v not in matched]
        hint_msgs = " | ".join(HINTS.get(v, f"Investigate {v}") for v in unmatched[:3])

        if tp > 0:
            return (
                f"Step {step}: Found {tp}/{total} vulnerabilities. Score={score:.4f}. "
                f"Still missing: {unmatched}. "
                f"Hints: {hint_msgs}. "
                f"Also: provide severity labels and line numbers for each finding to boost score."
            )

        return (
            f"Step {step}: No correct vulnerabilities found yet. Score={score:.4f}. "
            f"This contract has {total} vulnerabilities: {expected_vulns}. "
            f"Hints: {hint_msgs}. "
            f"Re-read the contract carefully and report: vulnerability name, severity, line number, and explanation."
        )

    def step(self, action: Action, task_id: str = "easy") -> StepResult:
        contract = CONTRACTS[task_id]
        state    = self.states[task_id]
        state["step_count"] += 1

        graded          = self._grade(action, task_id)
        score           = graded["score"]
        true_positives  = graded["true_positives"]
        false_positives = graded["false_positives"]
        missed          = graded["missed"]

        prev_best        = state.get("best_score", SCORE_MIN)
        state["best_score"] = max(prev_best, score)
        prev_score          = state["current_score"]
        delta               = score - prev_score

        if delta > 0 or state["step_count"] == 1:
            reward_value = clamp(score)
        else:
            reward_value = clamp(max(SCORE_MIN, score - 0.05))

        state["current_score"]       = score
        state["last_findings_count"] = len(action.findings)

        feedback = self._build_feedback(graded, task_id, state["step_count"])
        state["last_feedback"] = feedback

        done = (score >= 0.95) or (state["step_count"] >= 5)

        obs = Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=clamp(score),
            last_feedback=feedback,
            step_count=state["step_count"],
            max_steps=5,
        )
        reward = RewardInfo(
            value=clamp(reward_value),
            cumulative=clamp(score),
            message=feedback,
            true_positives=true_positives,
            false_positives=false_positives,
            missed_vulnerabilities=missed,
        )
        return StepResult(
            observation=obs,
            reward=reward,
            done=done,
            info={
                "step":             state["step_count"],
                "true_positives":   true_positives,
                "false_positives":  false_positives,
                "missed":           missed,
                "matched_vulns":    graded["matched_vulns"],
                "best_score":       clamp(state["best_score"]),
                "severity_bonus":   graded["severity_bonus"],
                "line_bonus":       graded["line_bonus"],
                "explanation_bonus": graded["explanation_bonus"],
                "keyword_bonus":    graded["keyword_bonus"],
                "fp_penalty":       graded["fp_penalty"],
            },
        )

    def state(self, task_id: str = "easy") -> Observation:
        contract = CONTRACTS[task_id]
        s        = self.states[task_id]
        return Observation(
            task_id=task_id,
            task_description=contract["description"],
            contract_code=contract["code"],
            current_score=clamp(s["current_score"]),
            last_feedback=s["last_feedback"],
            step_count=s["step_count"],
            max_steps=5,
        )
