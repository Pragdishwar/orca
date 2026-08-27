from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.schemas.trace import TraceResponse
from backend.app.db.session import get_db
from backend.app.models.trace import Trace

router = APIRouter()

@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: UUID, db: AsyncSession = Depends(get_db)):
    """Returns ordered execution trace nodes with hinge event metadata."""
    result = await db.execute(select(Trace).filter(Trace.trace_id == trace_id))
    trace = result.scalars().first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace
