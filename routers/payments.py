from fastapi import APIRouter
from datetime import datetime
from app.schemas.payment import PaymentRequest, Receipt

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/process", response_model=Receipt)
def process_payment(payment: PaymentRequest):
    """проводит оплату"""
    return Receipt(
        receipt_id=f"REC-{payment.booking_id}-2026",
        booking_id=payment.booking_id,
        user_id=101,
        amount=payment.amount,
        timestamp=datetime.now(),
        pdf_url=f"https://api.coworking.example.com/receipts/REC-{payment.booking_id}.pdf"
    )