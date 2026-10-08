from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Car, Favorite, Notification, Rental, User
from app.schemas.car import CarOut
from app.schemas.user import NotificationOut, ProfileOut, UserOut
from app.services import cars as cars_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/me/profile", response_model=ProfileOut)
def profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rentals = db.scalars(
        select(Rental)
        .where(Rental.renter_id == user.id)
        .order_by(Rental.created_at.desc())
    ).all()
    favorites = db.scalars(
        select(Car)
        .join(Favorite, Favorite.car_id == Car.id)
        .where(Favorite.user_id == user.id, Car.is_hidden.is_(False))
    ).all()
    my_cars = db.scalars(select(Car).where(Car.owner_id == user.id)).all()
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "rentals": rentals,
        "favorites": favorites,
        "my_cars": my_cars,
    }


@router.post(
    "/me/favorites/{car_id}",
    response_model=CarOut,
    status_code=status.HTTP_201_CREATED,
)
def add_favorite(
    car_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = cars_service.get_visible_car(db, car_id)
    already = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.car_id == car_id)
    )
    if already:
        raise HTTPException(status.HTTP_409_CONFLICT, "Car is already in favorites")
    db.add(Favorite(user_id=user.id, car_id=car_id))
    db.commit()
    return car


@router.delete("/me/favorites/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    car_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.car_id == car_id)
    )
    if favorite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Car is not in favorites")
    db.delete(favorite)
    db.commit()


@router.get("/me/notifications", response_model=list[NotificationOut])
def my_notifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    ).all()


@router.patch("/me/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    notification.is_read = True
    db.commit()
    return notification