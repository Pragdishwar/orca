from pydantic import BaseModel
from typing import Dict, Any

class RegistryBase(BaseModel):
    provider: str
    country: str
    variables: Dict[str, Any]
    spatial_coverage: str
    resolution_km: float
    access_method: str
    access_status: str
    priority_tier: int

class RegistryCreate(RegistryBase):
    source_id: str

class RegistryResponse(RegistryBase):
    source_id: str

    class Config:
        from_attributes = True
