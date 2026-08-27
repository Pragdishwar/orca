from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.schemas.advisory import AdvisoryResponse, AdvisoryReleaseRequest
from backend.app.db.session import get_db
from backend.app.models.advisory import Advisory

router = APIRouter()

@router.get("/{id}", response_model=AdvisoryResponse)
async def get_advisory(id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Advisory).filter(Advisory.advisory_id == id))
    advisory = result.scalars().first()
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    return advisory

@router.post("/{id}/release", response_model=AdvisoryResponse)
async def release_advisory(id: UUID, request: AdvisoryReleaseRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Advisory).filter(Advisory.advisory_id == id))
    advisory = result.scalars().first()
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    
    advisory.state = "RELEASED"
    advisory.released_by = request.officer_name
    advisory.released_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(advisory)
    return advisory

@router.get("/{id}/broadcast", response_class=PlainTextResponse)
async def broadcast_advisory(id: UUID, format: str = "sms", db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Advisory).filter(Advisory.advisory_id == id))
    advisory = result.scalars().first()
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    
    if format == "sms":
        return f"ALERT: Verdict {advisory.verdict}. Return by {advisory.turn_back_time}."
    elif format == "vhf":
        return f"PAN PAN. All vessels in inlet {advisory.inlet_id}, advisory verdict {advisory.verdict}."
    elif format == "slip":
        return f"PORT SLIP\nBoat: {advisory.boat_id}\nVerdict: {advisory.verdict}\nReturn: {advisory.turn_back_time}"
    elif format == "board":
        return f"[ {advisory.verdict} ] INLET {advisory.inlet_id}"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
