from pydantic import BaseModel, validator
from typing import List, Optional

# STRICT SCORE BOUNDS: validator requirement — scores MUST be strictly between 0 and 1
SCORE_FLOOR = 0.01
SCORE_CEIL  = 0.99

def _clamp(v: float) -> float:
    """Clamp to strictly open interval (0, 1). Never 0.0 or 1.0."""
    v = float(v)
    if v <= 0.0:
        return SCORE_FLOOR
    if v >= 1.0:
        return SCORE_CEIL
    return round(v, 4)


class Observation(BaseModel):
    task_id: str
    task_description: str
    contract_code: str
    current_score: float = SCORE_FLOOR   # default 0.01 — never 0.0
    last_feedback: str = ""
    step_count: int = 0
    max_steps: int = 5

    @validator("current_score", pre=True, always=True)
    def clamp_current_score(cls, v):
        return _clamp(v if v is not None else SCORE_FLOOR)


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

    @validator("value", "cumulative", pre=True, always=True)
    def clamp_reward_scores(cls, v):
        return _clamp(v if v is not None else SCORE_FLOOR)


class StepResult(BaseModel):
    observation: Observation
    reward: RewardInfo
    done: bool
    info: dict = {}
