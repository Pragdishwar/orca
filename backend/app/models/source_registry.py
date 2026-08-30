from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.types import GUID, JSONColumn
from sqlalchemy import String, Float, Integer
from backend.app.db.session import Base

class SourceRegistry(Base):
    __tablename__ = "source_registries"
    
    source_id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)
    variables: Mapped[dict] = mapped_column(JSONColumn)
    spatial_coverage: Mapped[str] = mapped_column(String)
    resolution_km: Mapped[float] = mapped_column(Float)
    access_method: Mapped[str] = mapped_column(String)
    access_status: Mapped[str] = mapped_column(String)
    priority_tier: Mapped[int] = mapped_column(Integer)
    provenance: Mapped[str] = mapped_column(String, default="ORCA_LIVE")
    last_pull_ts: Mapped[str] = mapped_column(String, nullable=True)
