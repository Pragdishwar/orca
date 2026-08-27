import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Float
from geoalchemy2 import Geometry
from backend.app.db.session import Base

class Zone(Base):
    __tablename__ = "zones"
    
    zone_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    geom = mapped_column(Geometry('POLYGON', srid=4326, spatial_index=True))
    buffer_km: Mapped[float] = mapped_column(Float)
