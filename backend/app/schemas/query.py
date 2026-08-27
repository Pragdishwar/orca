from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID

class QueryRequest(BaseModel):
    session_id: UUID
    query_text: str

class QueryResponse(BaseModel):
    answer: str
    verdict: str
    return_window: Optional[Dict[str, Any]] = None
    trace_id: Optional[UUID] = None
    guard: Dict[str, Any]
    sources: List[Dict[str, Any]]
    layers: List[str]

    class Config:
        from_attributes = True
