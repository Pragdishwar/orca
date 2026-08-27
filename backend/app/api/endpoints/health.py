from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dataset import RECORD_START, RECORD_YEARS
from backend.app.db.session import get_db
from backend.app.models.source_registry import SourceRegistry

router = APIRouter()

# R-2 staleness bands.
STALE_WARN_HOURS = 6
STALE_HALT_HOURS = 24


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Pipeline status, last successful pull and staleness (FR-45)."""
    result = await db.execute(
        select(SourceRegistry).filter(SourceRegistry.access_status == "CONNECTED"))
    connected = result.scalars().all()

    now = datetime.now(timezone.utc)
    last_pull = None
    for src in connected:
        if src.last_pull_ts:
            ts = datetime.fromisoformat(src.last_pull_ts)
            if last_pull is None or ts > last_pull:
                last_pull = ts

    staleness = 0.0 if last_pull is None else (now - last_pull).total_seconds() / 3600.0

    if not connected:
        status = "failed"
    elif staleness > STALE_HALT_HOURS:
        status = "halted"
    elif staleness > STALE_WARN_HOURS:
        status = "stale"
    else:
        status = "active"

    return {
        "status": "ok",
        "pipeline_status": status,
        "connected_sources": [s.provider for s in connected],
        "primary_source": connected[0].provider if connected else None,
        "last_pull": last_pull.isoformat() if last_pull else None,
        "staleness_hours": round(staleness, 2),
        "stale_warn_hours": STALE_WARN_HOURS,
        "stale_halt_hours": STALE_HALT_HOURS,
        "record": {
            "start": RECORD_START.date().isoformat(),
            "years": RECORD_YEARS,
            "provenance": "SYNTHETIC_STRUCTURED",
        },
    }
