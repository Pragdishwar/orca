import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float
from backend.app.db.types import GUID
from backend.app.db.session import Base


class Ground(Base):
    """A named fishing ground.

    R-6: a boat is only ever associated with a ground *name*. The centroid
    lives here, on the ground itself, and is never persisted against a boat.
    """

    __tablename__ = "grounds"

    ground_id: Mapped[str] = mapped_column(String, primary_key=True)
    local_name: Mapped[str] = mapped_column(String)
    centroid_lat: Mapped[float] = mapped_column(Float)
    centroid_lon: Mapped[float] = mapped_column(Float)
    radius_km: Mapped[float] = mapped_column(Float)
