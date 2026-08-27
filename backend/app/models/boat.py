from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float
from backend.app.db.session import Base

class Boat(Base):
    __tablename__ = "boats"
    
    boat_id: Mapped[str] = mapped_column(String, primary_key=True)
    hull_class: Mapped[str] = mapped_column(String, index=True)
    length_m: Mapped[float] = mapped_column(Float)
    engine_hp: Mapped[int] = mapped_column(Integer)
    crew: Mapped[int] = mapped_column(Integer)
    home_harbour: Mapped[str] = mapped_column(String)
    threshold_bucket: Mapped[str] = mapped_column(String)
