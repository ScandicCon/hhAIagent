from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config.settings import (
    AUTO_APPLY_DAILY_LIMIT,
    AUTO_APPLY_HOUR_END,
    AUTO_APPLY_HOUR_START,
)
from app.models.hh_applications import HhApplication
from app.models.profiles import Profile
from app.models.vacancy_analyses import VacancyAnalysis
from app.services.apply_modes import APPLY_MODE_AUTO
from app.services.limits import get_limits


def _day_start(dt: datetime | None = None) -> datetime:
    dt = dt or datetime.utcnow()
    return datetime(dt.year, dt.month, dt.day)


def _pct_delta(today: int, yesterday: int) -> int | None:
    if yesterday <= 0:
        return 100 if today > 0 else None
    return int(round((today - yesterday) / yesterday * 100))


def _applications_on_day(profile_id: int, day: datetime, session: Session) -> int:
    start = _day_start(day)
    end = start + timedelta(days=1)
    stmt = (
        select(func.count())
        .select_from(HhApplication)
        .where(
            HhApplication.profile_id == profile_id,
            HhApplication.created_at >= start,
            HhApplication.created_at < end,
            HhApplication.status.in_(("applied", "prepared")),
        )
    )
    return int(session.execute(stmt).scalar() or 0)


def _vacancies_found_on_day(profile_id: int, day: datetime, session: Session) -> int:
    start = _day_start(day)
    end = start + timedelta(days=1)
    stmt = (
        select(func.count())
        .select_from(VacancyAnalysis)
        .where(
            VacancyAnalysis.profile_id == profile_id,
            VacancyAnalysis.created_at >= start,
            VacancyAnalysis.created_at < end,
        )
    )
    return int(session.execute(stmt).scalar() or 0)


def build_dashboard_stats(profile: Profile, session: Session) -> dict:
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)

    vacancies_today = _vacancies_found_on_day(profile.id, today, session)
    vacancies_yesterday = _vacancies_found_on_day(profile.id, yesterday, session)
    apps_today = _applications_on_day(profile.id, today, session)
    apps_yesterday = _applications_on_day(profile.id, yesterday, session)

    limits = get_limits(profile)
    applications_left = max(0, AUTO_APPLY_DAILY_LIMIT - profile.applications_today)

    total_apps_stmt = (
        select(func.count())
        .select_from(HhApplication)
        .where(
            HhApplication.profile_id == profile.id,
            HhApplication.status.in_(("applied", "prepared")),
        )
    )
    total_apps = int(session.execute(total_apps_stmt).scalar() or 0)
    progress = min(99, max(5, total_apps * 4))

    directions_stmt = (
        select(func.count(func.distinct(VacancyAnalysis.id)))
        .where(VacancyAnalysis.profile_id == profile.id)
    )
    # Уникальные «направления» — по последнему запросу + активные анализы за 7 дней
    week_ago = today - timedelta(days=7)
    recent_analyses = session.execute(
        select(VacancyAnalysis.id).where(
            VacancyAnalysis.profile_id == profile.id,
            VacancyAnalysis.created_at >= week_ago,
        )
    ).all()
    active_directions = 1 if profile.last_search_query else 0
    active_directions = max(active_directions, min(3, len(recent_analyses) // 20 + 1))

    chart: list[dict] = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        chart.append(
            {
                "date": day.strftime("%d.%m"),
                "applications": _applications_on_day(profile.id, day, session),
                "vacancies_found": _vacancies_found_on_day(profile.id, day, session),
            }
        )

    mode = getattr(profile, "apply_mode", None) or (
        APPLY_MODE_AUTO if profile.auto_apply_enabled else "semi_auto"
    )

    return {
        "vacancies_found_today": vacancies_today,
        "vacancies_found_delta_pct": _pct_delta(vacancies_today, vacancies_yesterday),
        "applications_today": apps_today,
        "applications_delta_pct": _pct_delta(apps_today, apps_yesterday),
        "applications_daily_limit": AUTO_APPLY_DAILY_LIMIT,
        "applications_left": applications_left,
        "active_directions": active_directions,
        "progress_percent": progress,
        "progress_label": "Активный поиск" if progress >= 50 else "Разгон",
        "apply_mode": mode,
        "auto_schedule_label": f"Автоотклики с {AUTO_APPLY_HOUR_START}:00 до {AUTO_APPLY_HOUR_END}:00 МСК",
        "plan_label": limits["plan_label"],
        "searches_left": limits["searches_left"],
        "daily_chart": chart,
    }
