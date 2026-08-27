import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base
from backend.app.db.types import GUID, JSONColumn


class Advisory(Base):
    __tablename__ = "advisories"

    advisory_id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    # Nullable: a query can be asked about a hull class before any boat is
    # registered against it.
    boat_id: Mapped[str] = mapped_column(String, ForeignKey("boats.boat_id"), nullable=True)
    inlet_id: Mapped[str] = mapped_column(String)
    hull_class: Mapped[str] = mapped_column(String, nullable=True)
    advisory_date: Mapped[str] = mapped_column(String, nullable=True)
    verdict: Mapped[str] = mapped_column(String)
    index_value: Mapped[float] = mapped_column(Float)
    return_window: Mapped[dict] = mapped_column(JSONColumn)
    turn_back_time: Mapped[str] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="PENDING_RELEASE")
    guard_result: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSONColumn, nullable=True)
    released_by: Mapped[str] = mapped_column(String, nullable=True)
    released_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
