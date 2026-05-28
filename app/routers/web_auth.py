from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config.settings import BOT_USERNAME, PUBLIC_URL

_COOKIE_SECURE = PUBLIC_URL.lower().startswith("https")
from app.db.session import get_db
from app.deps.auth import get_current_profile
from app.models.profiles import Profile
from app.schemas.dashboard import DashboardMeResponse
from app.schemas.web_auth import AuthTokenResponse, TelegramLoginPayload
from app.services.apply_modes import APPLY_MODE_SEMI
from app.services.limits import get_limits
from app.services.web_auth import (
    create_access_token,
    get_or_create_profile,
    verify_telegram_login,
)

router = APIRouter(prefix="/web", tags=["web-auth"])

SESSION_COOKIE = "hh_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30


@router.get("/config")
def web_public_config():
    return {"bot_username": BOT_USERNAME, "public_url": PUBLIC_URL}


@router.post("/auth/telegram", response_model=AuthTokenResponse)
def login_telegram(
    payload: TelegramLoginPayload,
    response: Response,
    session: Session = Depends(get_db),
):
    verified = verify_telegram_login(
        payload.model_dump(mode="json", exclude_none=True)
    )
    telegram_id = verified["telegram_id"]
    profile = get_or_create_profile(telegram_id, session)
    token = create_access_token(profile.id, telegram_id)

    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=_COOKIE_SECURE,
    )

    resume_ready = len((profile.resume_text or "").strip()) >= 20
    return AuthTokenResponse(
        access_token=token,
        profile_id=profile.id,
        telegram_id=telegram_id,
        resume_ready=resume_ready,
    )


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/auth/me", response_model=DashboardMeResponse)
def auth_me(profile: Profile = Depends(get_current_profile)):
    telegram_id = int(profile.name.removeprefix("tg_"))
    limits = get_limits(profile)
    mode = getattr(profile, "apply_mode", None) or APPLY_MODE_SEMI
    return DashboardMeResponse(
        profile_id=profile.id,
        telegram_id=telegram_id,
        resume_ready=len((profile.resume_text or "").strip()) >= 20,
        apply_mode=mode,
        plan_label=limits["plan_label"],
        bot_username=BOT_USERNAME,
    )
