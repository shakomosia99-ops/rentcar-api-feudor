from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import Role
from app.schemas.car import CarOut
from app.schemas.rental import RentalOut


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    phone: str
    email: str
    role: Role
    is_active: bool


class RoleUpdate(BaseModel):
    role: Role


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    is_read: bool
    created_at: datetime


class ProfileOut(BaseModel):
    first_name: str
    last_name: str
    rentals: list[RentalOut]
    favorites: list[CarOut]
    my_cars: list[CarOut]