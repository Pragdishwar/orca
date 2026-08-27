from pydantic import BaseModel

class BoatBase(BaseModel):
    hull_class: str
    length_m: float
    engine_hp: int
    crew: int
    home_harbour: str
    threshold_bucket: str

class BoatCreate(BoatBase):
    boat_id: str

class BoatResponse(BoatBase):
    boat_id: str

    class Config:
        from_attributes = True

class BoatUpdate(BaseModel):
    hull_class: str | None = None
    length_m: float | None = None
    engine_hp: int | None = None
    crew: int | None = None
    home_harbour: str | None = None
    threshold_bucket: str | None = None
