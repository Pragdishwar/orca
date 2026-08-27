import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.types import GUID, JSONColumn
from sqlalchemy import String, DateTime
from backend.app.db.session import Base

class OfficialAdvisory(Base):
    __tablename__ = "official_advisories"
    
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    issue_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    issuer: Mapped[str] = mapped_column(String)
    region: Mapped[str] = mapped_column(String)
    text_en: Mapped[str] = mapped_column(String)
    text_ml: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
