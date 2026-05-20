from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.profiles import Profile
from app.services.admin_access import is_admin_profile
from app.services.plans import LIMITS, PLAN_FREE, PLAN_LABELS


def _week_start(now: datetime | None = None) -> datetime:
    now = now or datetime.utcnow()
    return now - timedelta(days=now.weekday())


def reset_usage_if_needed(profile: Profile) -> None:
    week_start = _week_start()

    if profile.usage_week_start is None or profile.usage_week_start.date() < week_start.date():
        profile.usage_week_start = week_start
        profile.searches_this_week = 0
        profile.cover_letters_this_week = 0


def get_limits(profile: Profile) -> dict:
    reset_usage_if_needed(profile)
    plan = profile.plan or PLAN_FREE
    plan_limits = LIMITS.get(plan, LIMITS[PLAN_FREE])

    return {
        "plan": plan,
        "plan_label": PLAN_LABELS.get(plan, plan),
        "searches_per_week": plan_limits["searches_per_week"],
        "cover_letters_per_week": plan_limits["cover_letters_per_week"],
        "searches_used": profile.searches_this_week,
        "cover_letters_used": profile.cover_letters_this_week,
        "searches_left": max(
            0,
            plan_limits["searches_per_week"]
            + getattr(profile, "bonus_searches", 0)
            - profile.searches_this_week,
        ),
        "bonus_searches": getattr(profile, "bonus_searches", 0),
        "cover_letters_left": max(
            0,
            plan_limits["cover_letters_per_week"] - profile.cover_letters_this_week,
        ),
        "digest_enabled": bool(profile.digest_enabled),
    }


def usage_payload(profile: Profile) -> dict:
    limits = get_limits(profile)
    return {
        "profile_id": profile.id,
        **limits,
    }


def ensure_search_allowed(profile: Profile) -> dict:
    if is_admin_profile(profile):
        return get_limits(profile)

    reset_usage_if_needed(profile)
    limits = get_limits(profile)

    if limits["searches_left"] <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "search_limit",
                "message": "Лимит поисков на этой неделе исчерпан",
                "usage": limits,
            },
        )

    return limits


def register_search(
    profile: Profile,
    search_text: str,
    session: Session,
    *,
    search_filters_json: str | None = None,
) -> dict:
    ensure_search_allowed(profile)
    if not is_admin_profile(profile):
        profile.searches_this_week += 1
    profile.last_search_query = search_text
    profile.last_search_filters = search_filters_json
    session.commit()
    session.refresh(profile)
    return get_limits(profile)


def ensure_cover_letter_allowed(profile: Profile) -> dict:
    if is_admin_profile(profile):
        return get_limits(profile)

    reset_usage_if_needed(profile)
    limits = get_limits(profile)

    if limits["cover_letters_left"] <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "cover_letter_limit",
                "message": "Лимит сопроводительных писем на этой неделе исчерпан",
                "usage": limits,
            },
        )

    return limits


def register_cover_letter(profile: Profile, session: Session) -> dict:
    ensure_cover_letter_allowed(profile)
    if not is_admin_profile(profile):
        profile.cover_letters_this_week += 1
    session.commit()
    session.refresh(profile)
    return get_limits(profile)


def activate_pro(profile: Profile, session: Session) -> dict:
    from app.services.plans import PLAN_PRO

    profile.plan = PLAN_PRO
    session.commit()
    session.refresh(profile)
    return usage_payload(profile)
