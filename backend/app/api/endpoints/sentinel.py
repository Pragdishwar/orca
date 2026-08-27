from typing import Any, Dict

from fastapi import APIRouter

from backend.app.tasks.sentinel import (
    POLL_INTERVAL_MINUTES,
    last_run_summary,
    last_run_time,
    scheduler,
    sentinel_hazard_poll,
)

router = APIRouter()


@router.post("/trigger")
async def manual_trigger() -> Dict[str, Any]:
    """Fire a poll immediately instead of waiting for the interval.

    Runs inline rather than in the background so the caller gets the cycle's
    result and the Alerts tab can be refreshed straight away.
    """
    summary = await sentinel_hazard_poll()
    return {"status": "success", **summary}


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    import backend.app.tasks.sentinel as s
    return {
        "running": scheduler.running,
        "active_jobs": len(scheduler.get_jobs()),
        "interval_minutes": POLL_INTERVAL_MINUTES,
        "last_run": s.last_run_time.isoformat() if s.last_run_time else None,
        "last_run_summary": s.last_run_summary,
    }
