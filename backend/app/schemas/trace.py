from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

class TraceResponse(BaseModel):
    trace_id: UUID
    nodes: Dict[str, Any]
    hinge_events: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
