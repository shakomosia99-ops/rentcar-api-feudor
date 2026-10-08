from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models import Transmission


class CarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int
    price_per_day: float
    capacity: int
    transmission: Transmission
    city: str
    fuel_tank: int
    latitude: float | None
    longitude: float | None
    owner_phone: str
    image_urls: list[str]
    is_hidden: bool
    created_at: datetime