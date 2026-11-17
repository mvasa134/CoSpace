from datetime import datetime
from pydantic import BaseModel, Field

class PaymentRequest(BaseModel):
    booking_id: int
    amount: float
    payment_method: str = Field(..., example="credit_card")

class Receipt(BaseModel):
    receipt_id: str
    booking_id: int
    user_id: int
    amount: float
    timestamp: datetime
    pdf_url: str