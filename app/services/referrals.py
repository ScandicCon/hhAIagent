import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import BOT_USERNAME, REFERRAL_BONUS_SEARCHES
from app.models.profiles import Profile


def _generate_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def ensure_referral_code(profile: Profile, session: Session) -> str:
    if profile.referral_code:
        return profile.referral_code

    for _ in range(10):
        code = _generate_code()
        exists = session.execute(
            select(Profile).where(Profile.referral_code == code)
        ).scalar_one_or_none()
        if exists is None:
            profile.referral_code = code
            session.commit()
            session.refresh(profile)
            return code

    raise RuntimeError("Could not generate referral code")


def referral_link(code: str) -> str:
    return f"https://t.me/{BOT_USERNAME}?start=ref_{code}"


def apply_referral(profile: Profile, referral_code: str, session: Session) -> dict:
    code = referral_code.strip().upper().removeprefix("REF_")

    if profile.referral_applied:
        return {"ok": False, "message": "Referral already applied"}

    if profile.referral_code and profile.referral_code == code:
        return {"ok": False, "message": "Cannot use own referral code"}

    referrer = session.execute(
        select(Profile).where(Profile.referral_code == code)
    ).scalar_one_or_none()

    if referrer is None:
        return {"ok": False, "message": "Invalid referral code"}

    if referrer.id == profile.id:
        return {"ok": False, "message": "Cannot use own referral code"}

    profile.referred_by_id = referrer.id
    profile.referral_applied = True
    referrer.bonus_searches += REFERRAL_BONUS_SEARCHES

    session.commit()
    session.refresh(profile)
    session.refresh(referrer)

    return {
        "ok": True,
        "message": f"Referral applied. Friend gets +{REFERRAL_BONUS_SEARCHES} searches.",
        "referrer_profile_id": referrer.id,
        "bonus_searches": referrer.bonus_searches,
    }


def get_referral_info(profile: Profile, session: Session) -> dict:
    code = ensure_referral_code(profile, session)
    invited = session.execute(
        select(Profile).where(Profile.referred_by_id == profile.id)
    ).scalars().all()

    return {
        "referral_code": code,
        "referral_link": referral_link(code),
        "invited_count": len(invited),
        "bonus_searches": profile.bonus_searches,
        "reward_per_friend": REFERRAL_BONUS_SEARCHES,
    }
