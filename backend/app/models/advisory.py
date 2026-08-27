import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import String, Float, DateTime, ForeignKey
from backend.app.db.session import Base

class Advisory(Base):
    __tablename__ = "advisories"
    
    advisory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    boat_id: Mapped[str] = mapped_column(String, ForeignKey("boats.boat_id"))
    inlet_id: Mapped[str] = mapped_column(String)
    verdict: Mapped[str] = mapped_column(String)
    index_value: Mapped[float] = mapped_column(Float)
    return_window: Mapped[dict] = mapped_column(JSONB)
    turn_back_time: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    guard_result: Mapped[str] = mapped_column(String)
    released_by: Mapped[str] = mapped_column(String, nullable=True)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
