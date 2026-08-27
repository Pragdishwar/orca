import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime, ForeignKey, func
from backend.app.db.session import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    boat_id: Mapped[str] = mapped_column(String, ForeignKey("boats.boat_id"))
    trigger_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String, ForeignKey("source_registries.source_id"))
    state: Mapped[str] = mapped_column(String)
    released_by: Mapped[str] = mapped_column(String, nullable=True)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
