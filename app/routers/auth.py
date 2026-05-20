import logging

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.core import HH_CLIENT_ID, HH_USER_AGENT
from app.config.settings import HH_REDIRECT_URI
from app.db.session import get_db
from app.models.profiles import Profile
from app.services.hh_oauth_service import (
    build_authorize_url,
    exchange_code_for_tokens,
    parse_state,
    save_oauth_to_profile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _profile_by_telegram(telegram_id: int, session: Session) -> Profile:
    name = f"tg_{telegram_id}"
    profile = session.execute(
        select(Profile).where(Profile.name == name)
    ).scalar_one_or_none()

    if profile is None:
        profile = Profile(
            name=name,
            resume_text="Подключите резюме с hh.ru или отправьте текст в боте.",
            skills="",
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

    return profile


@router.get("/hh/login")
def hh_login_legacy():
    return RedirectResponse("/auth/hh/link-info")


@router.get("/hh/link-info")
def hh_link_info():
    return {
        "message": "Use GET /hh/link/{telegram_id} from bot",
        "redirect_uri": HH_REDIRECT_URI,
        "client_id_set": bool(HH_CLIENT_ID),
    }


def _handle_hh_oauth_callback(
    code: str | None,
    state: str | None,
    error: str | None,
    session: Session,
) -> HTMLResponse:
    if error:
        return HTMLResponse(
            f"<h2>Ошибка авторизации hh.ru</h2><p>{error}</p>",
            status_code=400,
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    telegram_id = parse_state(state)
    token_data = exchange_code_for_tokens(code)
    profile = _profile_by_telegram(telegram_id, session)
    save_oauth_to_profile(profile, token_data, session)

    logger.info("HH OAuth connected for tg_%s profile #%s", telegram_id, profile.id)

    return HTMLResponse(
        """
        <html><body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h2>hh.ru подключён</h2>
        <p>Вернись в Telegram: отправь /start (обновить меню),<br>
        затем «Синхронизировать резюме» или /sync_resume</p>
        <p><small>Если синхронизация не работает — в dev.hh.ru включи права API: резюме и отклики.</small></p>
        </body></html>
        """
    )


@router.get("/callback", response_class=HTMLResponse)
def hh_oauth_callback_legacy(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: Session = Depends(get_db),
):
    """Redirect URI registered on hh.ru: http://localhost:8000/auth/callback"""
    return _handle_hh_oauth_callback(code, state, error, session)


@router.get("/hh/callback", response_class=HTMLResponse)
def hh_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: Session = Depends(get_db),
):
    return _handle_hh_oauth_callback(code, state, error, session)


@router.get("/login")
def login_hh_redirect():
    """Legacy endpoint — open via bot /connect_hh instead."""
    raise HTTPException(
        status_code=400,
        detail="Open /hh/link/{telegram_id} from Telegram bot (/connect_hh)",
    )
