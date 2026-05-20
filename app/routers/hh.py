from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.profiles import Profile
from app.models.vacancy_analyses import VacancyAnalysis
from app.schemas.hh import (
    HhApplyRequest,
    HhApplyResponse,
    HhAutoApplyToggle,
    HhConnectionStatus,
    HhResumeItem,
    HhSyncResumeRequest,
    HhSyncResumeResponse,
)
from app.services.hh_user_service import (
    apply_to_vacancy,
    hh_connection_status,
    list_resumes,
    sync_resume_from_hh,
)
from app.services.hh_oauth_service import build_authorize_url
from sqlalchemy import select

router = APIRouter(prefix="/hh", tags=["hh"])


def _get_profile(profile_id: int, session: Session) -> Profile:
    profile = session.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/link/{telegram_id}")
def hh_oauth_link(telegram_id: int):
    return {"url": build_authorize_url(telegram_id)}


@router.get("/status/{profile_id}", response_model=HhConnectionStatus)
def hh_status(profile_id: int, session: Session = Depends(get_db)):
    profile = _get_profile(profile_id, session)
    return hh_connection_status(profile)


@router.get("/resumes/{profile_id}", response_model=list[HhResumeItem])
def hh_resumes(profile_id: int, session: Session = Depends(get_db)):
    profile = _get_profile(profile_id, session)
    return list_resumes(profile, session)


@router.post("/sync-resume/{profile_id}", response_model=HhSyncResumeResponse)
def hh_sync_resume(
    profile_id: int,
    body: HhSyncResumeRequest | None = None,
    session: Session = Depends(get_db),
):
    profile = _get_profile(profile_id, session)
    resume_id = body.resume_id if body else None
    result = sync_resume_from_hh(profile, session, resume_id=resume_id)
    return HhSyncResumeResponse(**result)


@router.post("/auto-apply/{profile_id}", response_model=HhConnectionStatus)
def hh_auto_apply_toggle(
    profile_id: int,
    body: HhAutoApplyToggle,
    session: Session = Depends(get_db),
):
    profile = _get_profile(profile_id, session)
    if body.enabled and not profile.hh_access_token:
        raise HTTPException(status_code=400, detail="Connect hh.ru first")

    profile.auto_apply_enabled = body.enabled
    session.commit()
    session.refresh(profile)
    return hh_connection_status(profile)


@router.post("/apply/{analysis_id}", response_model=HhApplyResponse)
def hh_apply_to_analysis(
    analysis_id: int,
    body: HhApplyRequest | None = None,
    session: Session = Depends(get_db),
):
    analysis = session.get(VacancyAnalysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    profile = analysis.profile
    message = body.message if body else None

    if not message:
        from app.models.cover_letters import CoverLetter

        cover = session.execute(
            select(CoverLetter).where(CoverLetter.analysis_id == analysis.id)
        ).scalar_one_or_none()
        if cover:
            message = cover.text

    result = apply_to_vacancy(
        profile,
        session,
        vacancy_hh_id=analysis.vacancy.hh_id,
        message=message,
        analysis_id=analysis.id,
    )
    return HhApplyResponse(**result)
