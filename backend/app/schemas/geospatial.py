from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class GeofenceResponse(BaseModel):
    ground_id: str
    in_imbl: bool
    in_mpa: bool
    distance_to_boundary_km: Optional[float] = None

class PFZPoint(BaseModel):
    lat: float
    lon: float
    score: float
    distance_km: float

class PFZResponse(BaseModel):
    ground_id: str
    points: List[PFZPoint]

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float

class RouteResponse(BaseModel):
    corridor_h3: List[str]
    distance_nm: float
    eta_hours: float
    risk_score: float

class ProductivityResponse(BaseModel):
    region: str
    series: List[Dict[str, Any]]
