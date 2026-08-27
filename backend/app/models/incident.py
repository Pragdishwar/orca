import uuid
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.types import GUID, JSONColumn
from sqlalchemy import String, Date, Float
from backend.app.db.session import Base

class Incident(Base):
    __tablename__ = "incidents"
    
    incident_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date)
    location: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
