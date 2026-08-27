from pydantic import BaseModel
from typing import Dict, Optional, Any
from uuid import UUID
from datetime import datetime

class SessionCreate(BaseModel):
    language: str = "en"
    persona: str = "default"
    context: Dict[str, Any] = {}

class SessionResponse(BaseModel):
    session_id: UUID
    language: str
    persona: str
    context: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
