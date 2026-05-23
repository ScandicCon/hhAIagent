from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from app.services.hh_service import search_vacancies, get_vacancy_by_id
from app.services.ai_service import analyze_vacancy
from app.schemas.vacancies import VacancySearchRequest, VacancySearchResponse
from app.services.limits import (
    ensure_search_allowed,
    register_cover_letter,
    register_search,
    usage_payload,
)
from app.db.session import get_db
from app.config.settings import VACANCY_RESULTS_COUNT
from app.services.job_agent import find_best_vacancies
from app.services.search_filters import filters_to_json
from app.models.vacancies import Vacancy
from app.models.vacancy_analyses import VacancyAnalysis
from sqlalchemy import select
from app.models.profiles import Profile
from app.services.ai_service import generate_cover_letter, improve_cover_letter
from app.models.vacancy_analyses import VacancyAnalysis
from app.services.hh_service import get_vacancy_by_id
from app.schemas.vacancy_analysis import VacancyAnalysisResponse
from app.models.cover_letters import CoverLetter
from app.schemas.cover_letters import CoverLetterImproveRequest
from app.models.cover_letter_versions import CoverLetterVersion


router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.post("/search")
def post_vacancies(
    request: VacancySearchRequest,
    session: Session = Depends(get_db)
):
    vacancies = search_vacancies(
        text=request.text,
        per_page=request.per_page,
        filters=request.filters,
    )

    for vacancy_data in vacancies:
        exists = session.query(Vacancy).filter(
            Vacancy.hh_id == vacancy_data["hh_id"]
        ).first()

        if exists:
            continue

        vacancy = Vacancy(
            hh_id=vacancy_data["hh_id"],
            title=vacancy_data["title"],
            company=vacancy_data["company"],
            url=vacancy_data["url"],
        )

        session.add(vacancy)

    session.commit()

    return vacancies


@router.get("/{hh_id}")
def get_vacancy(hh_id: str):
    vacancy = get_vacancy_by_id(hh_id)
    resume = """
    Python developer.
    FastAPI.
    PostgreSQL.
    Redis.
    """
    analysis = analyze_vacancy(
    resume=resume,
    vacancy_title=vacancy["title"],
    company=vacancy["company"],
    vacancy_description=vacancy["description"],
    )
    return analysis

@router.post("/best")
def get_best_vacancies():

    resume = """
    Python developer.
    FastAPI.
    PostgreSQL.
    Redis.
    """

    results = find_best_vacancies(
        resume=resume,
        search_text="Python backend",
        per_page=5,
    )

    return results

@router.post("/best/{profile_id}", response_model=VacancySearchResponse)
def get_best_vacancies_for_profile(
    profile_id: int,
    request: VacancySearchRequest,
    session: Session = Depends(get_db),
):
    stmt = select(Profile).where(Profile.id == profile_id)
    profile = session.execute(stmt).scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    previous_query = profile.last_search_query
    previous_filters = profile.last_search_filters
    ensure_search_allowed(profile)

    result_count = request.per_page or VACANCY_RESULTS_COUNT

    results = find_best_vacancies(
        resume=profile.resume_text,
        search_text=request.text,
        profile_id=profile.id,
        session=session,
        per_page=result_count,
        previous_query=previous_query,
        filters=request.filters,
        previous_filters_json=previous_filters,
    )

    register_search(
        profile,
        request.text,
        session,
        search_filters_json=filters_to_json(request.filters),
    )

    return VacancySearchResponse(
        vacancies=results,
        usage=usage_payload(profile),
    )


@router.get("/analyses/{profile_id}")
def get_ai_response(
    profile_id: int,
    session: Session = Depends(get_db)
):
    stmt = select(VacancyAnalysis).where(
        VacancyAnalysis.profile_id == profile_id
    )

    analyses = session.execute(stmt).scalars().all()

    if not analyses:
        raise HTTPException(
            status_code=404,
            detail="You don't have analyses"
        )

    result = []

    for analysis in analyses:
        vacancy = analysis.vacancy

        result.append({
            "id": analysis.id,
            "profile_id": analysis.profile_id,

            "vacancy_id": analysis.vacancy_id,
            "hh_id": vacancy.hh_id,
            "title": vacancy.title,
            "company": vacancy.company,
            "url": vacancy.url,

            "match_score": analysis.match_score,
            "should_apply": analysis.should_apply,
            "summary": analysis.summary,
            "pros": json.loads(analysis.pros),
            "cons": json.loads(analysis.cons),
            "created_at": analysis.created_at,
        })

    return result


@router.post("/cover-letter/{analysis_id}")
def create_cover_letter(
    analysis_id: int,
    session: Session = Depends(get_db),
):
    stmt = select(VacancyAnalysis).where(
        VacancyAnalysis.id == analysis_id
    )

    analysis = session.execute(stmt).scalar_one_or_none()

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    existing_cover_letter = session.execute(
        select(CoverLetter).where(
            CoverLetter.analysis_id == analysis.id
        )
    ).scalar_one_or_none()

    profile = analysis.profile

    if existing_cover_letter:
        return {
            "analysis_id": analysis.id,
            "cover_letter_id": existing_cover_letter.id,
            "cover_letter": existing_cover_letter.text,
            "cached": True,
            "usage": usage_payload(profile),
        }

    register_cover_letter(profile, session)

    vacancy = analysis.vacancy

    full_vacancy = get_vacancy_by_id(vacancy.hh_id)

    cover_letter = generate_cover_letter(
        resume=profile.resume_text,
        vacancy_title=vacancy.title,
        company=vacancy.company,
        vacancy_description=full_vacancy["description"],
    )

    db_cover_letter = CoverLetter(
        analysis_id=analysis.id,
        text=cover_letter.cover_letter,
    )

    session.add(db_cover_letter)
    session.commit()
    session.refresh(db_cover_letter)

    return {
        "analysis_id": analysis.id,
        "cover_letter_id": db_cover_letter.id,
        "vacancy_id": vacancy.id,
        "hh_id": vacancy.hh_id,
        "title": vacancy.title,
        "company": vacancy.company,
        "cover_letter": db_cover_letter.text,
        "cached": False,
        "usage": usage_payload(profile),
    }

@router.post("/cover-letter/{cover_letter_id}/improve")
def improve_letters(
    cover_letter_id: int,
    request: CoverLetterImproveRequest,
    session: Session = Depends(get_db),
):
    stmt = select(CoverLetter).where(CoverLetter.id == cover_letter_id)

    cover_letter = session.execute(stmt).scalar_one_or_none()

    if cover_letter is None:
        raise HTTPException(
            status_code=404,
            detail="Cover letter not found"
        )

    improve_cover = improve_cover_letter(
        instruction=request.instruction,
        text=cover_letter.text,
    )

    version_number = len(cover_letter.cover_letter_versions) + 1

    version = CoverLetterVersion(
        cover_letter_id=cover_letter.id,
        text=improve_cover.improved_text,
        instruction=request.instruction,
        version_number=version_number,
    )

    session.add(version)

    cover_letter.text = improve_cover.improved_text

    session.commit()
    session.refresh(version)
    session.refresh(cover_letter)

    return {
        "cover_letter_id": cover_letter.id,
        "version_id": version.id,
        "version_number": version.version_number,
        "instruction": request.instruction,
        "improved_text": cover_letter.text,
        "updated": True,
    }

@router.get("/cover-letter/{cover_letter_id}/versions")
def see_version_letter(cover_letter_id: int, session: Session = Depends(get_db)):
    stmt = select(CoverLetterVersion).where(CoverLetterVersion.cover_letter_id == cover_letter_id).order_by(CoverLetterVersion.created_at.asc())
    all_versions = session.execute(stmt).scalars().all()
    if not all_versions:
        raise HTTPException(
            status_code=404,
            detail="Not founded letter"
        )
    result = []
    for version in all_versions:
        result.append({
            "version_id": version.id,
            "version_number": version.version_number,
            "instruction": version.instruction,
            "text": version.text,
            "created_at": version.created_at
        })
    return result

@router.post("/cover-letter/{cover_letter_id}/versions/{version_id}/restore")
def restore_cover_letter_version(
    cover_letter_id: int,
    version_id: int,
    session: Session = Depends(get_db),
):
    cover_letter_stmt = select(CoverLetter).where(CoverLetter.id == cover_letter_id)
    cover_letter = session.execute(cover_letter_stmt).scalar_one_or_none()

    if cover_letter is None:
        raise HTTPException(
            status_code=404,
            detail="Not founded letter"
        )
    
    version_stmt = select(CoverLetterVersion).where(
        CoverLetterVersion.id == version_id,
        CoverLetterVersion.cover_letter_id == cover_letter_id )
    
    version = session.execute(
        version_stmt
    ).scalar_one_or_none()

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Cover letter version not found"
        )

    cover_letter.text = version.text

    session.commit()
    session.refresh(cover_letter)

    return {
        "cover_letter_id": cover_letter.id,
        "restored_version_id": version.id,
        "version_number": version.version_number,
        "text": cover_letter.text,
        "restored": True,
    }