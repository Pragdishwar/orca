import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.types import GUID, JSONColumn
from sqlalchemy import DateTime, func
from backend.app.db.session import Base

class Trace(Base):
    __tablename__ = "traces"
    
    trace_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nodes: Mapped[dict] = mapped_column(JSONColumn)
    hinge_events: Mapped[dict] = mapped_column(JSONColumn)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
