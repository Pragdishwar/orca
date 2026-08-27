import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base
from backend.app.db.types import GUID, JSONColumn


class Alert(Base):
    """A Sentinel-triggered instance of the same advisory object a query makes.

    It enters the same PENDING_RELEASE gate (R-4) and the same four-format
    broadcast renderer, so there is no separate delivery path for alerts.
    """

    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    boat_id: Mapped[str] = mapped_column(String, ForeignKey("boats.boat_id"))
    trigger_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String, nullable=True)
    verdict: Mapped[str] = mapped_column(String, nullable=True)
    index_value: Mapped[float] = mapped_column(Float, nullable=True)
    hull_class: Mapped[str] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONColumn, nullable=True)
    state: Mapped[str] = mapped_column(String, default="PENDING_RELEASE")
    released_by: Mapped[str] = mapped_column(String, nullable=True)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
