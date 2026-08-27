from uuid import UUID
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.schemas.alert import AlertResponse, AlertReleaseRequest
from backend.app.db.session import get_db
from backend.app.models.alert import Alert

router = APIRouter()

@router.get("", response_model=List[AlertResponse])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert))
    return result.scalars().all()

@router.post("/{id}/release", response_model=AlertResponse)
async def release_alert(id: UUID, request: AlertReleaseRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).filter(Alert.alert_id == id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.state = "RELEASED"
    alert.released_by = request.officer_name
    alert.released_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(alert)
    return alert
