from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class AdvisoryResponse(BaseModel):
    advisory_id: UUID
    boat_id: str
    inlet_id: str
    verdict: str
    index_value: float
    return_window: Dict[str, Any]
    turn_back_time: str
    state: str
    guard_result: str
    released_by: Optional[str] = None
    released_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdvisoryReleaseRequest(BaseModel):
    officer_name: str
