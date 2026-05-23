from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import ADMIN_API_KEY, PROMO_CODES
from app.services.plans import PLAN_PRO
from app.schemas.promo import PromoRedeemRequest, PromoRedeemResponse
from app.db.session import get_db
from app.models.profiles import Profile
from app.schemas.subscription import DigestToggle, UsageResponse
from app.services.limits import activate_pro, usage_payload

router = APIRouter(prefix="/subscription", tags=["subscription"])


def _require_admin_key(x_admin_key: str | None) -> None:
    if not ADMIN_API_KEY or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin key required")


def _get_profile(profile_id: int, session: Session) -> Profile:
    profile = session.execute(
        select(Profile).where(Profile.id == profile_id)
    ).scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.post("/redeem/{profile_id}", response_model=PromoRedeemResponse)
def redeem_promo_code(
    profile_id: int,
    body: PromoRedeemRequest,
    session: Session = Depends(get_db),
):
    profile = _get_profile(profile_id, session)
    code = body.code.strip().upper()

    if not code:
        raise HTTPException(status_code=400, detail="Empty promo code")

    plan = PROMO_CODES.get(code)
    if plan is None:
        raise HTTPException(status_code=404, detail="Invalid promo code")

    if plan == "pro":
        activate_pro(profile, session)

    from app.services.plans import PLAN_LABELS

    return PromoRedeemResponse(
        ok=True,
        message=f"Promo {code} activated",
        plan=profile.plan,
        plan_label=PLAN_LABELS.get(profile.plan, profile.plan),
    )


@router.get("/usage/{profile_id}", response_model=UsageResponse)
def get_usage(profile_id: int, session: Session = Depends(get_db)):
    profile = _get_profile(profile_id, session)
    return usage_payload(profile)


@router.post("/digest/{profile_id}", response_model=UsageResponse)
def toggle_digest(
    profile_id: int,
    body: DigestToggle,
    session: Session = Depends(get_db),
):
    profile = _get_profile(profile_id, session)
    profile.digest_enabled = body.enabled
    session.commit()
    session.refresh(profile)
    return usage_payload(profile)


@router.get("/digest-recipients")
def list_digest_recipients(
    session: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None),
):
    _require_admin_key(x_admin_key)

    today = datetime.utcnow().date()
    profiles = session.execute(
        select(Profile).where(
            Profile.digest_enabled.is_(True),
            Profile.last_search_query.isnot(None),
        )
    ).scalars().all()

    recipients = []
    for profile in profiles:
        if profile.last_digest_at and profile.last_digest_at.date() >= today:
            continue
        if not profile.name.startswith("tg_"):
            continue
        telegram_id = profile.name.removeprefix("tg_")
        if not telegram_id.isdigit():
            continue
        recipients.append(
            {
                "profile_id": profile.id,
                "telegram_id": int(telegram_id),
                "last_search_query": profile.last_search_query,
                "last_search_filters": profile.last_search_filters,
            }
        )

    return recipients


@router.post("/digest-mark/{profile_id}")
def mark_digest_sent(
    profile_id: int,
    session: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None),
):
    _require_admin_key(x_admin_key)
    profile = _get_profile(profile_id, session)
    profile.last_digest_at = datetime.utcnow()
    session.commit()
    return {"ok": True, "profile_id": profile.id}


@router.post("/activate-pro/{profile_id}", response_model=UsageResponse)
def activate_pro_plan(
    profile_id: int,
    session: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None),
):
    _require_admin_key(x_admin_key)

    profile = _get_profile(profile_id, session)
    activate_pro(profile, session)
    return usage_payload(profile)


@router.post("/reset-usage/{profile_id}", response_model=UsageResponse)
def reset_usage(
    profile_id: int,
    session: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None),
):
    _require_admin_key(x_admin_key)
    profile = _get_profile(profile_id, session)
    profile.searches_this_week = 0
    profile.cover_letters_this_week = 0
    profile.usage_week_start = None
    session.commit()
    session.refresh(profile)
    return usage_payload(profile)


@router.get("/admin/stats")
def admin_stats(
    session: Session = Depends(get_db),
    x_admin_key: str | None = Header(default=None),
):
    _require_admin_key(x_admin_key)

    total = session.execute(select(func.count(Profile.id))).scalar_one()
    pro_count = session.execute(
        select(func.count(Profile.id)).where(Profile.plan == PLAN_PRO)
    ).scalar_one()
    digest_count = session.execute(
        select(func.count(Profile.id)).where(Profile.digest_enabled.is_(True))
    ).scalar_one()

    return {
        "total_profiles": total,
        "pro_profiles": pro_count,
        "digest_enabled": digest_count,
    }
