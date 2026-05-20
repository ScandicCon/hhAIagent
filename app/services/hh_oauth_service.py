import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config.core import HH_CLIENT_ID, HH_CLIENT_SECRET, HH_USER_AGENT
from app.config.settings import HH_REDIRECT_URI
from app.models.profiles import Profile

logger = logging.getLogger(__name__)


def _sign_state(telegram_id: int) -> str:
    payload = str(telegram_id).encode()
    secret = (HH_CLIENT_SECRET or HH_CLIENT_ID or "hh-ai").encode()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()[:16]
    return f"{telegram_id}.{signature}"


def parse_state(state: str) -> int:
    try:
        telegram_part, signature = state.split(".", 1)
        telegram_id = int(telegram_part)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from error

    expected = _sign_state(telegram_id).split(".", 1)[1]
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid OAuth state signature")

    return telegram_id


def build_authorize_url(telegram_id: int) -> str:
    if not HH_CLIENT_ID or not HH_REDIRECT_URI:
        raise HTTPException(
            status_code=503,
            detail="HH OAuth not configured (HH_CLIENT_ID, HH_REDIRECT_URI)",
        )

    params = {
        "response_type": "code",
        "client_id": HH_CLIENT_ID,
        "redirect_uri": HH_REDIRECT_URI,
        "state": _sign_state(telegram_id),
    }
    return "https://hh.ru/oauth/authorize?" + urlencode(params)


def exchange_code_for_tokens(code: str) -> dict:
    response = requests.post(
        "https://hh.ru/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": HH_CLIENT_ID,
            "client_secret": HH_CLIENT_SECRET,
            "code": code,
            "redirect_uri": HH_REDIRECT_URI,
        },
        headers={"User-Agent": HH_USER_AGENT},
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "hh_oauth",
                "message": "Не удалось получить токен hh.ru",
                "hh_status": response.status_code,
                "hh_response": response.text[:300],
            },
        )

    return response.json()


def refresh_user_token(profile: Profile, session: Session) -> str:
    if not profile.hh_refresh_token:
        raise HTTPException(
            status_code=401,
            detail="HH account not connected or refresh token missing",
        )

    response = requests.post(
        "https://hh.ru/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": HH_CLIENT_ID,
            "client_secret": HH_CLIENT_SECRET,
            "refresh_token": profile.hh_refresh_token,
        },
        headers={"User-Agent": HH_USER_AGENT},
        timeout=30,
    )

    if response.status_code != 200:
        logger.warning("HH refresh failed: %s", response.text[:200])
        raise HTTPException(
            status_code=401,
            detail="HH token expired. Reconnect via /connect_hh",
        )

    data = response.json()
    _save_tokens(profile, data, session)
    return profile.hh_access_token  # type: ignore[return-value]


def _save_tokens(profile: Profile, token_data: dict, session: Session) -> None:
    expires_in = int(token_data.get("expires_in", 3600))
    profile.hh_access_token = token_data["access_token"]
    profile.hh_refresh_token = token_data.get("refresh_token") or profile.hh_refresh_token
    profile.hh_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    session.commit()
    session.refresh(profile)


def save_oauth_to_profile(profile: Profile, token_data: dict, session: Session) -> None:
    _save_tokens(profile, token_data, session)


def get_valid_user_token(profile: Profile, session: Session) -> str:
    if not profile.hh_access_token:
        raise HTTPException(
            status_code=401,
            detail="HH account not connected",
        )

    if profile.hh_token_expires_at and profile.hh_token_expires_at > datetime.utcnow():
        return profile.hh_access_token

    return refresh_user_token(profile, session)
