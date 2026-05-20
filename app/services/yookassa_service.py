import base64
import logging
import uuid
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import (
    BOT_USERNAME,
    PRO_PRICE_RUB,
    YOOKASSA_SECRET_KEY,
    YOOKASSA_SHOP_ID,
)
from app.models.payments import Payment
from app.models.profiles import Profile
from app.services.limits import activate_pro

logger = logging.getLogger(__name__)

YOOKASSA_API = "https://api.yookassa.ru/v3/payments"


def _auth_header() -> str:
    token = base64.b64encode(f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()).decode()
    return f"Basic {token}"


def create_pro_payment(profile_id: int, session: Session) -> dict:
    profile = session.get(Profile, profile_id)
    if profile is None:
        raise ValueError("Profile not found")

    idempotence_key = str(uuid.uuid4())
    return_url = f"https://t.me/{BOT_USERNAME}"

    payload = {
        "amount": {"value": f"{PRO_PRICE_RUB}.00", "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": return_url,
        },
        "description": f"HH AI Pro — profile {profile_id}",
        "metadata": {"profile_id": str(profile_id)},
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(
            YOOKASSA_API,
            json=payload,
            headers={
                "Authorization": _auth_header(),
                "Idempotence-Key": idempotence_key,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

    payment = Payment(
        profile_id=profile_id,
        yookassa_payment_id=data["id"],
        amount_rub=PRO_PRICE_RUB,
        status=data.get("status", "pending"),
    )
    session.add(payment)
    session.commit()

    confirmation_url = data["confirmation"]["confirmation_url"]
    return {
        "payment_id": payment.id,
        "yookassa_payment_id": data["id"],
        "confirmation_url": confirmation_url,
        "amount_rub": PRO_PRICE_RUB,
    }


def handle_webhook_event(event: dict, session: Session) -> bool:
    event_type = event.get("event")
    obj = event.get("object") or {}
    payment_id = obj.get("id")
    status = obj.get("status")
    metadata = obj.get("metadata") or {}

    if not payment_id:
        return False

    db_payment = session.execute(
        select(Payment).where(Payment.yookassa_payment_id == payment_id)
    ).scalar_one_or_none()

    if db_payment is None:
        logger.warning("Unknown payment %s", payment_id)
        return False

    if event_type == "payment.succeeded" and status == "succeeded":
        if db_payment.status == "succeeded":
            return True

        db_payment.status = "succeeded"
        db_payment.paid_at = datetime.utcnow()
        profile = session.get(Profile, db_payment.profile_id)
        if profile:
            activate_pro(profile, session)
        session.commit()
        logger.info("Pro activated for profile %s", db_payment.profile_id)
        return True

    if event_type == "payment.canceled":
        db_payment.status = "canceled"
        session.commit()

    return True
