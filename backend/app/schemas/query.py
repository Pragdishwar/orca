from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class QueryRequest(BaseModel):
    session_id: Optional[UUID] = None
    query_text: str
    persona: Optional[str] = "fisherman"
    force_failure: bool = False
    stream: bool = False
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    gps_error: Optional[str] = None
    boat_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    verdict: str
    index_value: float
    hull_class: str
    hull_label: str
    date: str
    return_window: Optional[Dict[str, Any]] = None
    turn_back_time: Optional[str] = None
    trace_id: Optional[UUID] = None
    advisory_id: Optional[UUID] = None
    guard: Dict[str, Any]
    sources: List[Dict[str, Any]]
    discovery_log: Dict[str, Any]
    layers: List[str]
    language: str
    intent: Optional[str] = None
    context: Dict[str, Any]
    updated_fields: List[str] = []
    hourly: List[Dict[str, Any]] = []
    hull_comparison: List[Dict[str, Any]] = []
    official_advisory: Dict[str, Any]
    disagreement: bool = False
    hinge_events: List[Dict[str, Any]] = []
    provenance: str
    date_mapped_from_request: bool = False
    broadcast: Optional[Dict[str, Any]] = None
    intent_result: Optional[Dict[str, Any]] = None
