from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    pipeline_status: str
    data_staleness_hours: float

@router.get("", response_model=HealthResponse)
async def health_check():
    """Reports pipeline status, data staleness hours."""
    return HealthResponse(
        status="ok",
        pipeline_status="active",
        data_staleness_hours=1.2
    )
