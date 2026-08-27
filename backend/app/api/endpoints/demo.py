from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ForceFailureResponse(BaseModel):
    status: str
    message: str

@router.post("/force-failure", response_model=ForceFailureResponse)
async def force_failure():
    """Simulates guard rejection."""
    # This might interact with the guard module or a DB flag in a real scenario
    return ForceFailureResponse(
        status="success",
        message="Guard rejection simulated for next query."
    )
