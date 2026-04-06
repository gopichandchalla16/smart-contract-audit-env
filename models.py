from pydantic import BaseModel
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
    findings: List[str] = []
    severity: List[str] = []
    vulnerable_lines: List[int] = []
    explanation: str = ""


class RewardInfo(BaseModel):
    value: float
    cumulative: float
    message: str = ""
    true_positives: int = 0
    false_positives: int = 0
    missed_vulnerabilities: int = 0


class StepResult(BaseModel):
    observation: Observation
    reward: RewardInfo
    done: bool
    info: dict = {}
