from fastapi import APIRouter, Depends, status
from datetime import datetime
from app.schemas.booking import BookingCreate, BookingResponse
from app.schemas.auth import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/bookings", tags=["booking"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    current_user: User = Depends(get_current_user)  # Получаем пользователя из сессии
):
    base_price = 40.0
    total = base_price * booking.duration

    return BookingResponse(
        id=777,
        workspace_id=booking.workspace_id,
        user_id=current_user.id,
        booking_type=booking.booking_type,
        start_time=booking.start_time,
        end_time=booking.start_time,
        total_price=total,
        status="confirmed"
    )