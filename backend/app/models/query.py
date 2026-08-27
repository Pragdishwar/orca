import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import String, ForeignKey
from backend.app.db.session import Base

class Query(Base):
    __tablename__ = "queries"
    
    query_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.session_id"))
    text: Mapped[str] = mapped_column(String)
    lang: Mapped[str] = mapped_column(String)
    intent: Mapped[str] = mapped_column(String)
    slots: Mapped[dict] = mapped_column(JSONB)
    trace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
