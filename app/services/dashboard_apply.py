import json
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import AUTO_APPLY_DAILY_LIMIT
from app.models.cover_letters import CoverLetter
from app.models.hh_applications import HhApplication
from app.models.profiles import Profile
from app.models.vacancy_analyses import VacancyAnalysis
from app.services.ai_service import generate_cover_letter
from app.services.hh_service import get_vacancy_by_id
from app.services.hh_user_service import apply_to_vacancy
from app.services.limits import register_cover_letter

logger = logging.getLogger(__name__)


def _has_application(profile_id: int, analysis_id: int, session: Session) -> bool:
    row = session.execute(
        select(HhApplication).where(
            HhApplication.profile_id == profile_id,
            HhApplication.analysis_id == analysis_id,
            HhApplication.status.in_(("applied", "prepared")),
        )
    ).scalar_one_or_none()
    return row is not None


def _ensure_cover_letter(
    profile: Profile, analysis: VacancyAnalysis, session: Session
) -> str:
    existing = session.execute(
        select(CoverLetter).where(CoverLetter.analysis_id == analysis.id)
    ).scalar_one_or_none()
    if existing:
        return existing.text

    register_cover_letter(profile, session)
    vacancy = analysis.vacancy
    full_vacancy = get_vacancy_by_id(vacancy.hh_id)
    generated = generate_cover_letter(
        resume=profile.resume_text,
        vacancy_title=vacancy.title,
        company=vacancy.company,
        vacancy_description=full_vacancy["description"],
    )
    letter = CoverLetter(
        analysis_id=analysis.id,
        text=generated.cover_letter,
    )
    session.add(letter)
    session.commit()
    session.refresh(letter)
    return letter.text


def _record_prepared(
    profile: Profile,
    analysis: VacancyAnalysis,
    message: str,
    session: Session,
) -> None:
    profile.applications_today += 1
    profile.applications_day = datetime.utcnow()
    record = HhApplication(
        profile_id=profile.id,
        vacancy_hh_id=analysis.vacancy.hh_id,
        analysis_id=analysis.id,
        status="prepared",
        message=message[:5000],
    )
    session.add(record)
    session.commit()


def process_batch_apply(
    profile: Profile,
    analysis_ids: list[int],
    session: Session,
) -> dict:
    if profile.applications_today >= AUTO_APPLY_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Лимит откликов на сегодня: {AUTO_APPLY_DAILY_LIMIT}",
        )

    results: list[dict] = []
    sent = 0
    failed = 0

    for analysis_id in analysis_ids:
        if profile.applications_today >= AUTO_APPLY_DAILY_LIMIT:
            results.append(
                {
                    "analysis_id": analysis_id,
                    "ok": False,
                    "status": "limit",
                    "message": "Достигнут дневной лимит",
                }
            )
            failed += 1
            continue

        analysis = session.get(VacancyAnalysis, analysis_id)
        if analysis is None or analysis.profile_id != profile.id:
            results.append(
                {
                    "analysis_id": analysis_id,
                    "ok": False,
                    "status": "not_found",
                    "message": "Вакансия не найдена",
                }
            )
            failed += 1
            continue

        vacancy = analysis.vacancy
        if _has_application(profile.id, analysis.id, session):
            results.append(
                {
                    "analysis_id": analysis_id,
                    "ok": True,
                    "status": "already",
                    "title": vacancy.title,
                    "url": vacancy.url,
                    "message": "Уже откликались",
                }
            )
            continue

        try:
            cover = _ensure_cover_letter(profile, analysis, session)
        except HTTPException as error:
            results.append(
                {
                    "analysis_id": analysis_id,
                    "ok": False,
                    "status": "letter_failed",
                    "title": vacancy.title,
                    "message": str(error.detail),
                }
            )
            failed += 1
            continue

        hh_ready = bool(profile.hh_access_token and profile.hh_resume_id)
        if hh_ready:
            try:
                apply_to_vacancy(
                    profile,
                    session,
                    vacancy_hh_id=vacancy.hh_id,
                    message=cover,
                    analysis_id=analysis.id,
                )
                results.append(
                    {
                        "analysis_id": analysis_id,
                        "ok": True,
                        "status": "applied",
                        "title": vacancy.title,
                        "url": vacancy.url,
                        "cover_letter": cover,
                        "message": "Отклик отправлен на hh.ru",
                    }
                )
                sent += 1
                continue
            except HTTPException as error:
                logger.warning("HH apply failed, fallback to prepared: %s", error.detail)

        _record_prepared(profile, analysis, cover, session)
        results.append(
            {
                "analysis_id": analysis_id,
                "ok": True,
                "status": "prepared",
                "title": vacancy.title,
                "url": vacancy.url,
                "cover_letter": cover,
                "message": "Письмо готово — открой вакансию на hh.ru и вставь текст",
            }
        )
        sent += 1

    session.refresh(profile)
    left = max(0, AUTO_APPLY_DAILY_LIMIT - profile.applications_today)
    return {
        "sent": sent,
        "failed": failed,
        "results": results,
        "applications_today": profile.applications_today,
        "applications_left": left,
    }
