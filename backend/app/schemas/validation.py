from pydantic import BaseModel
from typing import List, Dict, Any

class ValidationResponse(BaseModel):
    hits: int
    misses: int
    false_alarms: int
    pod: float
    far: float
    skill_score: float
    failure_cases: List[Dict[str, Any]]
