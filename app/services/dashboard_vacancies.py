import json
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config.settings import AUTO_APPLY_DAILY_LIMIT
from app.models.hh_applications import HhApplication
from app.models.profiles import Profile
from app.models.vacancy_analyses import VacancyAnalysis


def _posted_label(created_at: datetime | None) -> str:
    if created_at is None:
        return "недавно"
    delta = datetime.utcnow() - created_at
    days = delta.days
    if days <= 0:
        return "сегодня"
    if days == 1:
        return "1 день назад"
    return f"{days} дня назад"


def _applied_analysis_ids(profile_id: int, session: Session) -> set[int]:
    rows = session.execute(
        select(HhApplication.analysis_id).where(
            HhApplication.profile_id == profile_id,
            HhApplication.status.in_(("applied", "prepared")),
            HhApplication.analysis_id.isnot(None),
        )
    ).all()
    return {row[0] for row in rows if row[0] is not None}


def list_vacancy_groups(profile: Profile, session: Session) -> dict:
    applied_ids = _applied_analysis_ids(profile.id, session)
    week_ago = datetime.utcnow() - timedelta(days=14)

    stmt = (
        select(VacancyAnalysis)
        .options(joinedload(VacancyAnalysis.vacancy))
        .where(
            VacancyAnalysis.profile_id == profile.id,
            VacancyAnalysis.created_at >= week_ago,
        )
        .order_by(VacancyAnalysis.match_score.desc(), VacancyAnalysis.created_at.desc())
        .limit(80)
    )
    analyses = session.execute(stmt).scalars().unique().all()

    pending = [a for a in analyses if a.id not in applied_ids]

    group_title = (profile.last_search_query or "Подборка вакансий").strip()[:80]
    cards = []
    for analysis in pending[:40]:
        vacancy = analysis.vacancy
        meta: dict = {}
        try:
            # optional cached meta in summary only
            pass
        except json.JSONDecodeError:
            pass

        cards.append(
            {
                "analysis_id": analysis.id,
                "hh_id": vacancy.hh_id,
                "title": vacancy.title,
                "company": vacancy.company,
                "url": vacancy.url,
                "match_score": analysis.match_score,
                "should_apply": analysis.should_apply,
                "summary": analysis.summary,
                "experience": meta.get("experience"),
                "schedule": meta.get("schedule"),
                "area": meta.get("area"),
                "salary": meta.get("salary"),
                "source_label": "HH",
                "posted_label": _posted_label(analysis.created_at),
                "already_applied": False,
                "created_at": analysis.created_at,
            }
        )

    groups = [{"title": group_title, "total": len(cards), "vacancies": cards}]
    left = max(0, AUTO_APPLY_DAILY_LIMIT - profile.applications_today)
    return {"groups": groups, "applications_left": left}
