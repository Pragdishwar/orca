from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.session import SessionCreate, SessionResponse
from backend.app.db.session import get_db
from backend.app.models.session import Session

router = APIRouter()

@router.post("", response_model=SessionResponse)
async def create_session(request: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Initiates a new session and loads persona context."""
    db_session = Session(
        language=request.language,
        persona=request.persona,
        context=request.context
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session
