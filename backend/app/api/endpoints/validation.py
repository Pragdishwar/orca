from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from backend.app.core import validation as validation_core

router = APIRouter()


@router.get("")
async def get_validation(
    threshold: Optional[float] = Query(
        None, ge=0.0, le=1.0,
        description="Index operating point. Defaults to the reference hull's unsafe band."),
) -> Dict[str, Any]:
    """Contingency table, POD, FAR, days-per-year and baseline skill.

    Recomputed from the analysis record on every call, so moving the threshold
    moves the numbers (FR-37). Nothing here is a stored constant.
    """
    return await validation_core.compute(threshold)
