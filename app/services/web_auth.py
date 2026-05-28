import hashlib
import hmac
import time
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import BOT_TOKEN, JWT_EXPIRE_DAYS, JWT_SECRET
from app.models.profiles import Profile
from app.services.referrals import ensure_referral_code

TELEGRAM_AUTH_MAX_AGE_SEC = 86400


def _telegram_profile_name(telegram_id: int) -> str:
    return f"tg_{telegram_id}"


def verify_telegram_login(payload: dict) -> dict:
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="BOT_TOKEN не задан на сервере — вход через Telegram недоступен",
        )

    data = {key: str(value) for key, value in payload.items() if value is not None}
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=400, detail="hash отсутствует")

    auth_date = int(data.get("auth_date", "0"))
    if time.time() - auth_date > TELEGRAM_AUTH_MAX_AGE_SEC:
        raise HTTPException(status_code=400, detail="Данные входа устарели, попробуй снова")

    check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data.keys()))
    secret = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated = hmac.new(
        secret, check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(status_code=401, detail="Неверная подпись Telegram")

    telegram_id = int(data["id"])
    return {
        "telegram_id": telegram_id,
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "username": data.get("username"),
    }


def get_or_create_profile(telegram_id: int, session: Session) -> Profile:
    name = _telegram_profile_name(telegram_id)
    profile = session.execute(
        select(Profile).where(Profile.name == name)
    ).scalar_one_or_none()

    if profile is None:
        profile = Profile(
            name=name,
            resume_text="",
            skills="",
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        ensure_referral_code(profile, session)

    return profile


def create_access_token(profile_id: int, telegram_id: int) -> str:
    expires = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub": profile_id,
        "tg_id": telegram_id,
        "exp": expires,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail="Сессия недействительна") from error
