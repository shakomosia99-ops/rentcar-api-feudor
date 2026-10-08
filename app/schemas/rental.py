from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RentalCreate(BaseModel):
    start_date: date
    end_date: date


class RentalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    car_id: int
    city: str
    start_date: date
    end_date: date
    days: int
    total_price: float
    created_at: datetime