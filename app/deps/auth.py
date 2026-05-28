from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.profiles import Profile
from app.services.web_auth import decode_access_token


def _token_from_request(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get("hh_session")


def get_current_profile(
    request: Request,
    session: Session = Depends(get_db),
) -> Profile:
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Требуется вход")

    payload = decode_access_token(token)
    profile_id = int(payload["sub"])
    profile = session.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=401, detail="Профиль не найден")
    return profile
