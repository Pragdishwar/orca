from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AlertResponse(BaseModel):
    alert_id: UUID
    boat_id: str
    trigger_type: str
    severity: str
    source_id: str
    state: str
    released_by: Optional[str] = None
    released_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertReleaseRequest(BaseModel):
    officer_name: str
