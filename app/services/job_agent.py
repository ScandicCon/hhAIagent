import json
import logging
import time

from openai import APIStatusError, RateLimitError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import (
    AI_REQUEST_DELAY_SEC,
    VACANCY_HH_PAGE_SIZE,
    VACANCY_MAX_HH_PAGES,
)
from app.models.profiles import Profile
from app.models.vacancies import Vacancy
from app.models.vacancy_analyses import VacancyAnalysis
from app.services.ai_service import analyze_vacancy
from app.services.hh_service import get_vacancy_by_id, search_vacancies
from app.services.search_filters import VacancySearchFilters, filters_to_json

logger = logging.getLogger(__name__)


def _analyzed_hh_ids(profile_id: int, session: Session) -> set[str]:
    rows = session.execute(
        select(Vacancy.hh_id)
        .join(VacancyAnalysis, VacancyAnalysis.vacancy_id == Vacancy.id)
        .where(VacancyAnalysis.profile_id == profile_id)
    ).all()
    return {row[0] for row in rows if row[0]}


def _hh_start_page(
    profile: Profile,
    search_text: str,
    previous_query: str | None,
    filters: VacancySearchFilters | None,
    previous_filters_json: str | None,
) -> int:
    query = search_text.strip().lower()
    prev = (previous_query or "").strip().lower()
    same_filters = filters_to_json(filters) == (previous_filters_json or None)
    if prev == query and same_filters and profile.searches_this_week > 1:
        return (profile.searches_this_week - 1) % 20
    return 0


def _collect_new_candidates(
    search_text: str,
    profile_id: int,
    session: Session,
    *,
    start_page: int,
    need_count: int,
    filters: VacancySearchFilters | None = None,
) -> list[dict]:
    seen = _analyzed_hh_ids(profile_id, session)
    candidates: list[dict] = []

    for page_offset in range(VACANCY_MAX_HH_PAGES):
        page = start_page + page_offset
        batch = search_vacancies(
            text=search_text,
            per_page=VACANCY_HH_PAGE_SIZE,
            page=page,
            filters=filters,
        )
        if not batch:
            break

        for item in batch:
            hh_id = item.get("hh_id")
            if not hh_id or hh_id in seen:
                continue
            seen.add(hh_id)
            candidates.append(item)
            if len(candidates) >= need_count:
                return candidates

    return candidates


def find_best_vacancies(
    resume: str,
    search_text: str,
    profile_id: int,
    session: Session,
    per_page: int = 7,
    previous_query: str | None = None,
    filters: VacancySearchFilters | None = None,
    previous_filters_json: str | None = None,
):
    profile = session.get(Profile, profile_id)
    start_page = (
        _hh_start_page(profile, search_text, previous_query, filters, previous_filters_json)
        if profile
        else 0
    )

    candidates = _collect_new_candidates(
        search_text,
        profile_id,
        session,
        start_page=start_page,
        need_count=per_page,
        filters=filters,
    )

    if not candidates:
        logger.info(
            "No new vacancies for profile %s query=%r page=%s",
            profile_id,
            search_text,
            start_page,
        )
        return []

    results = []

    for vacancy_data in candidates:
        logger.info("Processing: %s", vacancy_data["title"])

        full_vacancy = get_vacancy_by_id(vacancy_data["hh_id"])

        vacancy = session.execute(
            select(Vacancy).where(Vacancy.hh_id == full_vacancy["hh_id"])
        ).scalar_one_or_none()

        if vacancy is None:
            vacancy = Vacancy(
                hh_id=full_vacancy["hh_id"],
                title=full_vacancy["title"],
                company=full_vacancy["company"],
                url=full_vacancy["url"],
            )
            session.add(vacancy)
            session.commit()
            session.refresh(vacancy)

        existing_analysis = session.execute(
            select(VacancyAnalysis).where(
                VacancyAnalysis.profile_id == profile_id,
                VacancyAnalysis.vacancy_id == vacancy.id,
            )
        ).scalar_one_or_none()

        if existing_analysis:
            continue

        logger.info("Calling AI for: %s", full_vacancy["title"])

        try:
            analysis = analyze_vacancy(
                resume=resume,
                vacancy_title=full_vacancy["title"],
                company=full_vacancy["company"],
                vacancy_description=full_vacancy["description"],
            )
        except (RateLimitError, APIStatusError) as error:
            logger.error("AI failed for %s: %s", full_vacancy["title"], error)
            if results:
                break
            raise
        except Exception:
            logger.exception("AI failed for %s", full_vacancy["title"])
            continue

        if AI_REQUEST_DELAY_SEC > 0:
            time.sleep(AI_REQUEST_DELAY_SEC)

        db_analysis = VacancyAnalysis(
            profile_id=profile_id,
            vacancy_id=vacancy.id,
            match_score=analysis.match_score,
            should_apply=analysis.should_apply,
            summary=analysis.summary,
            pros=json.dumps(analysis.pros, ensure_ascii=False),
            cons=json.dumps(analysis.cons, ensure_ascii=False),
        )
        session.add(db_analysis)
        session.commit()
        session.refresh(db_analysis)

        results.append({
            "analysis_id": db_analysis.id,
            "hh_id": vacancy.hh_id,
            "title": vacancy.title,
            "company": vacancy.company,
            "url": vacancy.url,
            "experience": full_vacancy.get("experience"),
            "schedule": full_vacancy.get("schedule"),
            "employment": full_vacancy.get("employment"),
            "area": full_vacancy.get("area"),
            "salary": full_vacancy.get("salary"),
            "match_score": analysis.match_score,
            "should_apply": analysis.should_apply,
            "summary": analysis.summary,
            "pros": analysis.pros,
            "cons": analysis.cons,
            "cached": False,
        })

    results.sort(key=lambda item: item["match_score"], reverse=True)
    return results
