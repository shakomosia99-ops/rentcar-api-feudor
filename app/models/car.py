import enum
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transmission(str, enum.Enum):
    automatic = "automatic"
    manual = "manual"
    tiptronic = "tiptronic"


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(index=True)
    price_per_day: Mapped[float]
    capacity: Mapped[int] = mapped_column(index=True)
    transmission: Mapped[Transmission] = mapped_column(Enum(Transmission))
    city: Mapped[str] = mapped_column(String(50), index=True)
    fuel_tank: Mapped[int]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    is_hidden: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    owner = relationship("User")
    images = relationship(
        "CarImage", back_populates="car", cascade="all, delete-orphan"
    )

    @property
    def owner_phone(self) -> str:
        return self.owner.phone

    @property
    def image_urls(self) -> list[str]:
        return [f"/uploads/{image.path}" for image in self.images]


class CarImage(Base):
    __tablename__ = "car_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    path: Mapped[str] = mapped_column(String(255))

    car = relationship("Car", back_populates="images")