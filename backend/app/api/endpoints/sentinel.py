from fastapi import APIRouter, BackgroundTasks
from typing import Dict, Any
from backend.app.tasks.sentinel import sentinel_hazard_poll, scheduler, last_run_time

router = APIRouter(prefix="/sentinel", tags=["Sentinel"])

@router.post("/trigger")
async def manual_trigger(background_tasks: BackgroundTasks):
    """
    Manually overrides the APScheduler interval and fires a Sentinel poll immediately.
    """
    background_tasks.add_task(sentinel_hazard_poll)
    return {"status": "success", "message": "Sentinel manual hazard poll triggered in background."}

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Returns the operational status of the APScheduler and the latest poll execution.
    """
    is_running = scheduler.running
    jobs = scheduler.get_jobs()
    
    return {
        "running": is_running,
        "active_jobs": len(jobs),
        "last_run": last_run_time.isoformat() if last_run_time else None
    }
