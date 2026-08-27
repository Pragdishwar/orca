from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float
from backend.app.db.session import Base

class HullThreshold(Base):
    __tablename__ = "hull_thresholds"
    
    hull_class: Mapped[str] = mapped_column(String, primary_key=True)
    hs_marginal: Mapped[float] = mapped_column(Float)
    hs_unsafe: Mapped[float] = mapped_column(Float)
    index_marginal: Mapped[float] = mapped_column(Float)
    index_unsafe: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String)
