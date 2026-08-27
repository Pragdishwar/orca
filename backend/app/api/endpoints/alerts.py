from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.advisory_engine import compare_hulls
from backend.app.core.auth import require_token, validate_officer
from backend.app.core.broadcast import render_all
from backend.app.db.session import get_db
from backend.app.models.alert import Alert
from backend.app.models.boat import Boat
from backend.app.schemas.alert import AlertReleaseRequest

router = APIRouter()


def _view(a: Alert, boat: Optional[Boat] = None) -> Dict[str, Any]:
    return {
        "alert_id": str(a.alert_id),
        "boat_id": a.boat_id,
        "boat": {"hull_class": boat.hull_class, "length_m": boat.length_m,
                 "home_harbour": boat.home_harbour} if boat else None,
        "trigger_type": a.trigger_type,
        "severity": a.severity,
        "source_id": a.source_id,
        "verdict": a.verdict,
        "index_value": a.index_value,
        "hull_class": a.hull_class,
        "state": a.state,
        "released_by": a.released_by,
        "released_at": a.released_at.isoformat() if a.released_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "trigger_detail": (a.payload or {}).get("trigger_detail"),
    }


@router.get("")
async def list_alerts(
    state: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if state:
        stmt = stmt.filter(Alert.state == state)
    if severity:
        stmt = stmt.filter(Alert.severity == severity)
    alerts = (await db.execute(stmt)).scalars().all()

    boats = {b.boat_id: b for b in (await db.execute(select(Boat))).scalars().all()}
    rows = [_view(a, boats.get(a.boat_id)) for a in alerts]
    return {
        "alerts": rows,
        "summary": {
            "total": len(rows),
            "pending_release": sum(1 for r in rows if r["state"] == "PENDING_RELEASE"),
            "released": sum(1 for r in rows if r["state"] == "RELEASED"),
            "severe": sum(1 for r in rows if r["severity"] == "severe"),
            "warning": sum(1 for r in rows if r["severity"] == "warning"),
            "advisory": sum(1 for r in rows if r["severity"] == "advisory"),
        },
        "note": ("Alerts are produced by the scheduled Sentinel poll, independent of any "
                 "question being asked, and enter the same release gate and broadcast "
                 "renderer as a query-triggered advisory."),
    }


@router.post("/{alert_id}/release", dependencies=[Depends(require_token)])
async def release_alert(alert_id: UUID, request: AlertReleaseRequest,
                        db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """R-4: same human release gate an advisory goes through (FR-30)."""
    officer_row = validate_officer(request.officer_name)
    officer = f"{officer_row['name']} [{officer_row['officer_id']}]"
    result = await db.execute(select(Alert).filter(Alert.alert_id == alert_id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.state = "RELEASED"
    alert.released_by = officer
    alert.released_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return _view(alert)


@router.get("/{alert_id}/broadcast")
async def broadcast_alert(alert_id: UUID, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """FR-30: an alert compiles into the same four formats as an advisory."""
    result = await db.execute(select(Alert).filter(Alert.alert_id == alert_id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    payload = (alert.payload or {}).get("advisory")
    if not payload:
        raise HTTPException(status_code=409, detail="Alert has no stored advisory payload")

    try:
        target = datetime.fromisoformat(payload["date"]).replace(tzinfo=timezone.utc)
        comparison = compare_hulls(target)
    except (KeyError, TypeError, ValueError):
        comparison = []
    return {**render_all(payload, comparison), "state": alert.state,
            "alert": _view(alert)}
