from fastapi import APIRouter
from backend.app.schemas.validation import ValidationResponse

router = APIRouter()

@router.get("", response_model=ValidationResponse)
async def get_validation(threshold: float = 2.0):
    """Computes hits, misses, false alarms, POD, FAR, skill score vs Hs > threshold baseline."""
    # Mock data for validation response
    return ValidationResponse(
        hits=120,
        misses=5,
        false_alarms=15,
        pod=0.96,
        far=0.11,
        skill_score=0.85,
        failure_cases=[
            {"query_id": "test-1", "reason": "Edge case missed by guard"}
        ]
    )
