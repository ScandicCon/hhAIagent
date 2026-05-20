import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config.settings import YOOKASSA_ENABLED
from app.db.session import get_db
from app.schemas.payments import PaymentCreateResponse
from app.services.yookassa_service import create_pro_payment, handle_webhook_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/pro/{profile_id}", response_model=PaymentCreateResponse)
def create_pro_payment_endpoint(profile_id: int, session: Session = Depends(get_db)):
    if not YOOKASSA_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="YooKassa not configured. Set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY.",
        )

    try:
        result = create_pro_payment(profile_id, session)
    except Exception as error:
        logger.exception("Payment creation failed")
        raise HTTPException(status_code=500, detail=str(error)) from error

    return PaymentCreateResponse(
        payment_id=result["payment_id"],
        confirmation_url=result["confirmation_url"],
        amount_rub=result["amount_rub"],
    )


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request, session: Session = Depends(get_db)):
    try:
        body = await request.json()
    except Exception as error:
        raise HTTPException(status_code=400, detail="Invalid JSON") from error

    logger.info("YooKassa webhook: %s", body.get("event"))
    handle_webhook_event(body, session)
    return {"ok": True}
