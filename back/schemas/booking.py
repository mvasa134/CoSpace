from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class BookingType(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"

class BookingCreate(BaseModel):
    workspace_id: int
    booking_type: BookingType
    start_time: datetime
    duration: int = Field(..., description="Количество часов, дней или месяцев")

class BookingResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    booking_type: BookingType
    start_time: datetime
    end_time: datetime
    total_price: float
    status: str = "confirmed"