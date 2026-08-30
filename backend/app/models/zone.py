from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float
from backend.app.db.types import JSONColumn
from backend.app.db.session import Base


class Zone(Base):
    """Geofence polygon (IMBL / MPA / SENSITIVE / RESTRICTED).

    The ring is stored as GeoJSON rather than a PostGIS geometry so the
    prototype runs without a spatial database; point-in-polygon is evaluated
    in `backend.app.core.geo`.
    """

    __tablename__ = "zones"

    zone_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    geojson: Mapped[dict] = mapped_column(JSONColumn)
    buffer_km: Mapped[float] = mapped_column(Float)
    provenance: Mapped[str] = mapped_column(String, default="ORCA_LIVE")
