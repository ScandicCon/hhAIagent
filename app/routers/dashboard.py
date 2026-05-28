from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import get_current_profile
from app.models.profiles import Profile
from app.schemas.dashboard import (
    BatchApplyRequest,
    BatchApplyResponse,
    DashboardModeUpdate,
    DashboardSearchRequest,
    DashboardStats,
    DashboardVacanciesResponse,
)
from app.schemas.vacancies import VacancySearchResponse
from app.services.apply_modes import set_apply_mode
from app.services.dashboard_apply import process_batch_apply
from app.services.dashboard_stats import build_dashboard_stats
from app.services.dashboard_vacancies import list_vacancy_groups
from app.config.settings import VACANCY_RESULTS_COUNT
from app.services.limits import ensure_search_allowed, register_search, usage_payload
from app.services.job_agent import find_best_vacancies

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class ResumeUpdateBody(BaseModel):
    resume_text: str = Field(..., min_length=20)


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_db),
):
    return build_dashboard_stats(profile, session)


@router.get("/vacancies", response_model=DashboardVacanciesResponse)
def dashboard_vacancies(
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_db),
):
    return list_vacancy_groups(profile, session)


@router.patch("/mode", response_model=DashboardStats)
def dashboard_set_mode(
    body: DashboardModeUpdate,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_db),
):
    set_apply_mode(profile, body.mode)
    session.commit()
    session.refresh(profile)
    return build_dashboard_stats(profile, session)


@router.post("/search", response_model=VacancySearchResponse)
def dashboard_search(
    body: DashboardSearchRequest,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_db),
):
    ensure_search_allowed(profile)
    previous_query = profile.last_search_query
    previous_filters = profile.last_search_filters
    result_count = body.per_page or VACANCY_RESULTS_COUNT

    results = find_best_vacancies(
        resume=profile.resume_text,
        search_text=body.text,
        profile_id=profile.id,
        session=session,
        per_page=result_count,
        previous_query=previous_query,
        filters=None,
        previous_filters_json=previous_filters,
    )

    register_search(profile, body.text, session, search_filters_json=None)

    return VacancySearchResponse(
        vacancies=results,
        usage=usage_payload(profile),
    )


@router.post("/applications/batch", response_model=BatchApplyResponse)
def dashboard_batch_apply(
    body: BatchApplyRequest,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_db),
):
    if len((profile.resume_text or "").strip()) < 20:
        raise HTTPException(status_code=400, detail="Сначала заполни резюме в профиле")
    return process_batch_apply(profile, body.analysis_ids, session)


@router.put("/resume")
def dashboard_update_resume(
    body: ResumeUpdateBody,
    profile: Profile = Depends(get_current_profile),
    session: Session = Depends(get_db),
):
    from app.services.resume_versions import archive_current_resume

    if profile.resume_text.strip() and profile.resume_text.strip() != body.resume_text.strip():
        archive_current_resume(profile.id, profile.resume_text, session)
    profile.resume_text = body.resume_text.strip()
    profile.skills = body.resume_text.strip()[:255]
    session.commit()
    return {"ok": True, "length": len(profile.resume_text)}
