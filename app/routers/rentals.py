from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.rental import RentalCreate, RentalOut
from app.services import cars as cars_service
from app.services import rentals as rentals_service

router = APIRouter(tags=["rentals"])


@router.post(
    "/cars/{car_id}/rent",
    response_model=RentalOut,
    status_code=status.HTTP_201_CREATED,
)
def rent(
    car_id: int,
    data: RentalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = cars_service.get_visible_car(db, car_id)
    return rentals_service.rent_car(db, car, user, data.start_date, data.end_date)