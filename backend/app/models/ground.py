import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Float
from geoalchemy2 import Geometry
from backend.app.db.session import Base

class Ground(Base):
    __tablename__ = "grounds"
    
    ground_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    local_name: Mapped[str] = mapped_column(String)
    centroid = mapped_column(Geometry('POINT', srid=4326, spatial_index=True))
    radius_km: Mapped[float] = mapped_column(Float)
