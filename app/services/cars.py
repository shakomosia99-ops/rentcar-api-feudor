import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Car, Rental

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
REQUIRED_PHOTOS = 3


def read_photos(photos: list[UploadFile]) -> list[tuple[str, bytes]]:
    if len(photos) != REQUIRED_PHOTOS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Exactly {REQUIRED_PHOTOS} photos are required",
        )
    validated = []
    for photo in photos:
        extension = Path(photo.filename or "").suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Only png/jpg phoos are allowed",
            )
        content = photo.file.read()
        if not content or len(content) > MAX_PHOTO_BYTES:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Each photo must be between 1-5 MB",
            )
        validated.append((extension, content))
    return validated


def save_photos(validated: list[tuple[str, bytes]]) -> list[str]:
    names = []
    for extension, content in validated:
        name = f"{uuid.uuid4().hex}{extension}"
        (Path(settings.upload_dir) / name).write_bytes(content)
        names.append(name)
    return names


def delete_photo_files(car: Car) -> None:
    for image in car.images:
        (Path(settings.upload_dir) / image.path).unlink(missing_ok=True)


def _visible():
    return select(Car).where(Car.is_hidden.is_(False))


def get_visible_car(db: Session, car_id: int) -> Car:
    car = db.scalar(_visible().where(Car.id == car_id))
    if car is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Car not found")
    return car


def filter_cars(
    db: Session,
    city: str | None,
    year_from: int | None,
    year_to: int | None,
    capacity: int | None,
    page: int,
    page_size: int,
) -> list[Car]:
    query = _visible()
    if city:
        query = query.where(func.lower(Car.city) == city.strip().lower())
    if year_from is not None:
        query = query.where(Car.year >= year_from)
    if year_to is not None:
        query = query.where(Car.year <= year_to)
    if capacity is not None:
        query = query.where(Car.capacity == capacity)
    query = (
        query.order_by(Car.created_at.desc(), Car.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(query).all())


def popular_cars(db: Session, limit: int) -> list[Car]:
    query = (
        _visible()
        .outerjoin(Rental, Rental.car_id == Car.id)
        .group_by(Car.id)
        .order_by(func.count(Rental.id).desc(), Car.id.desc())
        .limit(limit)
    )
    return list(db.scalars(query).all())


def random_cars(db: Session, limit: int) -> list[Car]:
    return list(db.scalars(_visible().order_by(func.random()).limit(limit)).all())