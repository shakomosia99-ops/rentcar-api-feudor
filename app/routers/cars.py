from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import Car, CarImage, Rental, Role, Transmission, User
from app.schemas.car import CarOut
from app.services import cars as cars_service

router = APIRouter(prefix="/cars", tags=["cars"])
staff_only = require_role(Role.moderator, Role.admin)


@router.post("", response_model=CarOut, status_code=status.HTTP_201_CREATED)
def add_car(
    brand: str = Form(min_length=1, max_length=50, examples=["Mercedes"]),
    model: str = Form(min_length=1, max_length=50, examples=["E320"]),
    year: int = Form(ge=1950, le=date.today().year + 1, examples=[2015]),
    price_per_day: float = Form(gt=0, examples=[90]),
    capacity: int = Form(ge=1, le=60, examples=[4]),
    transmission: Transmission = Form(),
    city: str = Form(min_length=1, max_length=50, examples=["Tbilisi"]),
    fuel_tank: int = Form(ge=10, le=300, examples=[90]),
    latitude: float | None = Form(None, ge=-90, le=90),
    longitude: float | None = Form(None, ge=-180, le=180),
    photo1: UploadFile = File(description=".png, .jpg or .jpeg"),
    photo2: UploadFile = File(description=".png, .jpg or .jpeg"),
    photo3: UploadFile = File(description=".png, .jpg or .jpeg"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validated = cars_service.read_photos([photo1, photo2, photo3])
    car = Car(
        owner_id=user.id,  
        brand=brand.strip(),
        model=model.strip(),
        year=year,
        price_per_day=price_per_day,
        capacity=capacity,
        transmission=transmission,
        city=city.strip(),
        fuel_tank=fuel_tank,
        latitude=latitude,
        longitude=longitude,
    )
    car.images = [CarImage(path=name) for name in cars_service.save_photos(validated)]
    db.add(car)
    db.commit()
    db.refresh(car)
    return car


@router.get("", response_model=list[CarOut])
def filter_cars(
    city: str | None = None,
    year_from: int | None = Query(None, ge=1950),
    year_to: int | None = Query(None, ge=1950),
    capacity: int | None = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "year_from cannot be after year_to"
        )
    return cars_service.filter_cars(db, city, year_from, year_to, capacity, page, page_size)


@router.get("/popular", response_model=list[CarOut])
def popular(limit: int = Query(6, ge=1, le=50), db: Session = Depends(get_db)):
    return cars_service.popular_cars(db, limit)


@router.get("/random", response_model=list[CarOut])
def random(limit: int = Query(6, ge=1, le=50), db: Session = Depends(get_db)):
    return cars_service.random_cars(db, limit)


@router.get("/{car_id}", response_model=CarOut)
def car_detail(car_id: int, db: Session = Depends(get_db)):
    return cars_service.get_visible_car(db, car_id)


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(
    car_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.get(Car, car_id)
    if car is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Car not found")

    if car.owner_id != user.id and user.role not in (Role.moderator, Role.admin):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This is not your car")
    
    if db.scalar(select(Rental.id).where(Rental.car_id == car.id).limit(1)):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Car has rentals; it can be hidden, not deleted"
        )
    cars_service.delete_photo_files(car)
    db.delete(car)
    db.commit()


@router.patch("/{car_id}/visibility", response_model=CarOut)
def set_visibility(
    car_id: int,
    hidden: bool = True,
    staff: User = Depends(staff_only),
    db: Session = Depends(get_db),
):
    car = db.get(Car, car_id)
    if car is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Car not found")
    car.is_hidden = hidden
    db.commit()
    return car