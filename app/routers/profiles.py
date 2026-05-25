from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.profiles import Profile
from app.schemas.profiles import ProfileCreate, ProfileResponse
from app.schemas.resume_versions import ResumeVersionItem, ResumeVersionsResponse
from app.services.referrals import apply_referral, ensure_referral_code
from app.services.resume_versions import archive_current_resume, list_resume_versions

router = APIRouter(prefix="/profiles", tags=["profiles"])

MAX_SKILLS_LENGTH = 255


def _normalize_skills(skills: str, resume_text: str) -> str:
    value = (skills or resume_text or "").strip()
    return value[:MAX_SKILLS_LENGTH]

@router.post("/", response_model=ProfileResponse, status_code=201)
def create_profile(data: ProfileCreate, session: Session = Depends(get_db)):
    stmt = select(Profile).where(Profile.name == data.name)
    profile = session.execute(stmt).scalar_one_or_none()
    if profile:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    profiles = Profile(
        name=data.name,
        resume_text=data.resume_text,
        skills=_normalize_skills(data.skills, data.resume_text),
    )

    session.add(profiles)
    session.commit()
    session.refresh(profiles)
    return profiles


@router.post("/upsert", response_model=ProfileResponse)
def upsert_profile(data: ProfileCreate, session: Session = Depends(get_db)):
    skills = _normalize_skills(data.skills, data.resume_text)

    try:
        stmt = select(Profile).where(Profile.name == data.name)
        profile = session.execute(stmt).scalar_one_or_none()

        if profile:
            if profile.resume_text.strip() != data.resume_text.strip():
                archive_current_resume(profile.id, profile.resume_text, session)
            profile.resume_text = data.resume_text
            profile.skills = skills
            session.commit()
            session.refresh(profile)
            ensure_referral_code(profile, session)
            if data.referral_code and not profile.referral_applied:
                result = apply_referral(profile, data.referral_code, session)
                if not result["ok"]:
                    raise HTTPException(status_code=400, detail=result["message"])
            return profile

        profile = Profile(
            name=data.name,
            resume_text=data.resume_text,
            skills=skills,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        ensure_referral_code(profile, session)

        if data.referral_code:
            result = apply_referral(profile, data.referral_code, session)
            if not result["ok"]:
                raise HTTPException(status_code=400, detail=result["message"])

        return profile
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(error)) from error

@router.get(
    "/telegram/{telegram_id}/resume-versions",
    response_model=ResumeVersionsResponse,
)
def get_resume_versions(telegram_id: int, session: Session = Depends(get_db)):
    stmt = select(Profile).where(Profile.name == f"tg_{telegram_id}")
    profile = session.execute(stmt).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    versions = list_resume_versions(profile.id, session)
    return ResumeVersionsResponse(
        current=profile.resume_text,
        versions=[
            ResumeVersionItem(
                id=item.id,
                resume_text=item.resume_text,
                created_at=item.created_at,
            )
            for item in versions
        ],
    )


@router.get("/telegram/{telegram_id}", response_model=ProfileResponse)
def get_profile_by_telegram(telegram_id: int, session: Session = Depends(get_db)):
    stmt = select(Profile).where(Profile.name == f"tg_{telegram_id}")
    profile = session.execute(stmt).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile_by_id(profile_id: int, session: Session = Depends(get_db)):
    stmt = select(Profile).where(Profile.id == profile_id)
    profile = session.execute(stmt).scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    return profile