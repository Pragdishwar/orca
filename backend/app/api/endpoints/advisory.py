from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.advisory_engine import compare_hulls
from backend.app.core.auth import require_token, validate_officer
from backend.app.core.broadcast import render_all
from backend.app.core.official import advisory_for_date
from backend.app.db.session import get_db
from backend.app.models.advisory import Advisory
from backend.app.schemas.advisory import AdvisoryReleaseRequest

router = APIRouter()


def _view(a: Advisory) -> Dict[str, Any]:
    return {
        "advisory_id": str(a.advisory_id),
        "inlet_id": a.inlet_id,
        "hull_class": a.hull_class,
        "date": a.advisory_date,
        "verdict": a.verdict,
        "index_value": a.index_value,
        "return_window": a.return_window,
        "turn_back_time": a.turn_back_time,
        "state": a.state,
        "guard_result": a.guard_result,
        "released_by": a.released_by,
        "released_at": a.released_at.isoformat() if a.released_at else None,
    }


async def _get(db: AsyncSession, advisory_id: UUID) -> Advisory:
    result = await db.execute(select(Advisory).filter(Advisory.advisory_id == advisory_id))
    advisory = result.scalars().first()
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    return advisory


@router.get("/latest")
async def latest_advisory(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """The active advisory, which the Offline Compile and Trust tabs work from."""
    result = await db.execute(select(Advisory).order_by(Advisory.created_at.desc()).limit(1))
    advisory = result.scalars().first()
    if not advisory:
        return {"advisory": None, "message": "No advisory yet. Ask a question first."}
    return await _detail(advisory)


@router.get("/{advisory_id}")
async def get_advisory(advisory_id: UUID, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    return await _detail(await _get(db, advisory_id))


async def _detail(advisory: Advisory) -> Dict[str, Any]:
    payload = advisory.payload or {}
    official = await advisory_for_date(advisory.advisory_date or "")
    return {
        "advisory": _view(advisory),
        "payload": payload,
        "official_advisory": official,
        "disagreement": (official.get("severity") in ("warning", "severe"))
                        != (advisory.verdict == "DO_NOT_CROSS"),
    }


@router.post("/{advisory_id}/release", dependencies=[Depends(require_token)])
async def release_advisory(advisory_id: UUID, request: AdvisoryReleaseRequest,
                           db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """R-4: nothing reaches RELEASED without an officer on the roster."""
    officer_row = validate_officer(request.officer_name)
    officer = f"{officer_row['name']} [{officer_row['officer_id']}]"
    advisory = await _get(db, advisory_id)
    if advisory.guard_result == "REJECT":
        raise HTTPException(
            status_code=409,
            detail="Advisory was rejected by the guard and cannot be released. "
                   "The official advisory stands.")
    advisory.state = "RELEASED"
    advisory.released_by = officer
    advisory.released_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(advisory)
    return _view(advisory)


@router.get("/{advisory_id}/broadcast")
async def broadcast_advisory(
    advisory_id: UUID,
    format: Optional[str] = Query(None, pattern="^(sms|vhf|slip|board)$"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Render the advisory into the four offline formats (FR-39)."""
    advisory = await _get(db, advisory_id)
    payload = advisory.payload or {}
    if not payload:
        raise HTTPException(status_code=409, detail="Advisory has no stored payload to render")

    try:
        target = datetime.fromisoformat(advisory.advisory_date).replace(tzinfo=timezone.utc)
        comparison = await compare_hulls(target)
    except (TypeError, ValueError):
        comparison = []

    rendered = render_all(payload, comparison)
    if format:
        return {"format": format, **rendered[format],
                "state": advisory.state, "notice": rendered["notice"]}
    return {**rendered, "state": advisory.state, "advisory": _view(advisory)}
