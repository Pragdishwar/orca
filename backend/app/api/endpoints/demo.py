from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ForceFailureRequest(BaseModel):
    mode: str = "verdict_contradiction"


@router.post("/force-failure")
async def force_failure(body: ForceFailureRequest = ForceFailureRequest()) -> Dict[str, Any]:
    """Describes the forced-failure control (F-07, FR-18).

    The injection itself happens inside the graph's Synthesis node, driven by
    `force_failure` on the query request, so the guard rejects a real
    contradiction rather than a canned response. Send the next query with
    force_failure=true to see it.
    """
    return {
        "mode": body.mode,
        "armed": True,
        "how": ("Send POST /api/query with force_failure=true. The Synthesis node will "
                "emit a verdict_token that contradicts the computed verdict, and the "
                "deterministic guard will reject the advisory and publish the official "
                "bulletin instead."),
        "expected_guard": "REJECT",
    }


@router.get("/degradation-modes")
async def degradation_modes() -> Dict[str, Any]:
    """The faults the Trust tab can simulate (FR-42)."""
    return {"modes": [
        {"id": "verdict_contradiction",
         "label": "LLM contradicts the computed verdict",
         "rule": "R-1",
         "effect": "Guard rejects; official advisory published verbatim with a notice."},
        {"id": "unmatched_numeral",
         "label": "Generated text contains a number not in the payload",
         "rule": "R-7",
         "effect": "Guard rejects on number injection; official advisory published."},
        {"id": "stale_data",
         "label": "Data staleness exceeds 24 hours",
         "rule": "R-2",
         "effect": "NO_ADVISORY emitted; official advisory published."},
    ]}
