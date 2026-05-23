import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import YOOKASSA_ENABLED
from app.db.session import get_db
from app.models.profiles import Profile
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


@router.get("/go/telegram")
def pay_redirect_by_telegram(
    telegram_id: int = Query(..., ge=1),
    session: Session = Depends(get_db),
):
    if not YOOKASSA_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="YooKassa not configured",
        )

    profile = session.execute(
        select(Profile).where(Profile.name == f"tg_{telegram_id}")
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Сначала откройте бота @HHSearchVacanciesBot, нажмите /start и отправьте резюме.",
        )

    try:
        result = create_pro_payment(profile.id, session)
    except Exception as error:
        logger.exception("Payment redirect failed")
        raise HTTPException(status_code=500, detail=str(error)) from error

    return RedirectResponse(result["confirmation_url"], status_code=302)


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request, session: Session = Depends(get_db)):
    try:
        body = await request.json()
    except Exception as error:
        raise HTTPException(status_code=400, detail="Invalid JSON") from error

    logger.info("YooKassa webhook: %s", body.get("event"))
    handle_webhook_event(body, session)
    return {"ok": True}
