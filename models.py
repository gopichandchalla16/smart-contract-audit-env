from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Action(BaseModel):
    """Agent's audit submission for a smart contract."""
    findings: List[str] = Field(
        default=[],
        description="List of vulnerability findings. Each entry is a concise description."
    )
    severity: List[str] = Field(
        default=[],
        description="Severity label per finding: 'high', 'medium', or 'low'. Must match findings length."
    )
    vulnerable_lines: List[int] = Field(
        default=[],
        description="List of line numbers where vulnerabilities were found."
    )
    explanation: str = Field(
        default="",
        description="Detailed technical explanation of all vulnerabilities, attack vectors, and recommended fixes."
    )


class Observation(BaseModel):
    """Environment observation returned to the agent."""
    task_id: str
    task_description: str
    contract_code: str
    current_score: float
    last_feedback: str
    step_count: int
    max_steps: int


class RewardInfo(BaseModel):
    """Detailed reward breakdown."""
    value: float         = Field(..., description="Per-step reward, strictly in (0, 1)")
    cumulative: float    = Field(..., description="Cumulative task score, strictly in (0, 1)")
    message: str         = Field(default="", description="Human-readable feedback")
    true_positives: int  = Field(default=0)
    false_positives: int = Field(default=0)
    missed_vulnerabilities: int = Field(default=0)


class StepResult(BaseModel):
    """Full result returned by env.step()."""
    observation: Observation
    reward: RewardInfo
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)
