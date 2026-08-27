from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class SessionCreate(BaseModel):
    language: str = "en"
    persona: str = "fisherman"
    context: Dict[str, Any] = {}


class SessionResponse(BaseModel):
    session_id: UUID
    language: str
    persona: str
    context: Dict[str, Any]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
