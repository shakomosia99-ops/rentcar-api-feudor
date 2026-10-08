from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Car, Notification, Rental, User


def rent_car(
    db: Session, car: Car, renter: User, start_date: date, end_date: date
) -> Rental:
    
    if car.owner_id == renter.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot rent your own car")

    
    if start_date < date.today():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Start date cannot be in the past"
        )
    if end_date < start_date:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "End date cannot be before start date"
        )

    
    overlapping = db.scalar(
        select(Rental.id)
        .where(
            Rental.car_id == car.id,
            Rental.start_date <= end_date,
            Rental.end_date >= start_date,
        )
        .limit(1)
    )
    if overlapping:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Car is already rented for these dates"
        )

    
    days = (end_date - start_date).days + 1
    rental = Rental(
        car_id=car.id,
        renter_id=renter.id,
        start_date=start_date,
        end_date=end_date,
        days=days,
        total_price=round(days * car.price_per_day, 2),
        city=car.city,
    )
    db.add(rental)


    db.add(
        Notification(
            user_id=car.owner_id,
            message=(
                f"{renter.first_name} {renter.last_name} rented your "
                f"{car.brand} {car.model} from {start_date} to {end_date}"
            ),
        )
    )
    db.commit()
    db.refresh(rental)
    return rental