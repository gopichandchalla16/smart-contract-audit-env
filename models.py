from pydantic import BaseModel, Field
from typing import List, Optional


class Observation(BaseModel):
    task_id: str
    task_description: str
    contract_code: str
    current_score: float = 0.0
    last_feedback: str = ""
    step_count: int = 0
    max_steps: int = 5


class Action(BaseModel):
    findings: List[str] = Field(
        description="List of vulnerability descriptions found"
    )
    severity: List[str] = Field(
        description="Severity for each finding: high, medium, or low"
    )
    vulnerable_lines: List[int] = Field(
        default=[],
        description="Line numbers of vulnerable code"
    )
    explanation: str = Field(
        description="Root cause analysis and recommended fix"
    )


class RewardInfo(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    cumulative: float = Field(ge=0.0, le=1.0)
    message: str = ""
    true_positives: int = 0
    false_positives: int = 0
    missed_vulnerabilities: int = 0


class StepResult(BaseModel):
    observation: Observation
    reward: RewardInfo
    done: bool
    info: dict = {}


class TaskInfo(BaseModel):
    task_id: str
    description: str
    difficulty: str
    max_steps: int