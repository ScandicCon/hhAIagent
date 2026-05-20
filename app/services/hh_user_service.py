import logging
from datetime import datetime

import requests
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.core import HH_USER_AGENT
from app.config.settings import AUTO_APPLY_DAILY_LIMIT, AUTO_APPLY_MIN_MATCH
from app.models.hh_applications import HhApplication
from app.models.profiles import Profile
from app.models.vacancy_analyses import VacancyAnalysis
from app.services.hh_oauth_service import get_valid_user_token

logger = logging.getLogger(__name__)


def _user_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": HH_USER_AGENT,
    }


def _user_request(
    profile: Profile,
    session: Session,
    method: str,
    url: str,
    *,
    params: dict | None = None,
    data: dict | None = None,
    json_body: dict | None = None,
) -> requests.Response:
    token = get_valid_user_token(profile, session)
    response = requests.request(
        method,
        url,
        params=params,
        data=data,
        json=json_body,
        headers=_user_headers(token),
        timeout=30,
    )

    if response.status_code == 401:
        from app.services.hh_oauth_service import refresh_user_token

        token = refresh_user_token(profile, session)
        response = requests.request(
            method,
            url,
            params=params,
            data=data,
            json=json_body,
            headers=_user_headers(token),
            timeout=30,
        )

    return response


def hh_connection_status(profile: Profile) -> dict:
    connected = bool(profile.hh_access_token)
    return {
        "connected": connected,
        "resume_id": profile.hh_resume_id,
        "resume_title": profile.hh_resume_title,
        "auto_apply_enabled": bool(profile.auto_apply_enabled),
        "applications_today": profile.applications_today,
        "applications_daily_limit": AUTO_APPLY_DAILY_LIMIT,
    }


def list_resumes(profile: Profile, session: Session) -> list[dict]:
    response = _user_request(
        profile,
        session,
        "GET",
        "https://api.hh.ru/resumes/mine",
    )

    if response.status_code == 403:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "hh_resumes_forbidden",
                "message": (
                    "<b>hh.ru ещё не открыл API резюме для приложения</b>\n\n"
                    "OAuth прошёл, но /resumes/mine = 403.\n"
                    "Обычно нужна <b>модерация приложения</b> на dev.hh.ru (2–4 дня, письмо на почту).\n\n"
                    "Пока: отправь резюме <b>текстом</b> в боте (/start).\n"
                    "Отклик — кнопка «Открыть на hh.ru» под вакансией."
                ),
                "hh_status": 403,
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "hh_resumes",
                "message": "Не удалось получить список резюме",
                "hh_status": response.status_code,
                "hh_response": response.text[:300],
            },
        )

    items = response.json().get("items", [])
    return [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "url": item.get("alternate_url"),
            "updated_at": item.get("updated_at"),
        }
        for item in items
    ]


def resume_to_text(data: dict) -> str:
    parts: list[str] = []

    title = data.get("title")
    if title:
        parts.append(f"Желаемая должность: {title}")

    skills = data.get("skill_set") or []
    if skills:
        parts.append("Навыки: " + ", ".join(skills))

    for exp in data.get("experience") or []:
        company = exp.get("company") or exp.get("employer", {}).get("name", "")
        position = exp.get("position", "")
        desc = (exp.get("description") or "").strip()
        block = f"{position} — {company}".strip(" —")
        if desc:
            block += f"\n{desc}"
        if block:
            parts.append(block)

    about = (data.get("skills") or data.get("about") or "").strip()
    if isinstance(about, str) and about:
        parts.append(about)

    education = data.get("education", {})
    for item in (education.get("primary") or [])[:3]:
        name = item.get("name", "")
        org = item.get("organization", "")
        year = item.get("year", "")
        line = ", ".join(x for x in [name, org, str(year) if year else ""] if x)
        if line:
            parts.append(f"Образование: {line}")

    text = "\n\n".join(parts).strip()
    return text or title or "Резюме с hh.ru"


def sync_resume_from_hh(
    profile: Profile,
    session: Session,
    resume_id: str | None = None,
) -> dict:
    resumes = list_resumes(profile, session)
    if not resumes:
        raise HTTPException(status_code=404, detail="No resumes found on hh.ru")

    chosen = None
    if resume_id:
        chosen = next((r for r in resumes if r["id"] == resume_id), None)
    if chosen is None:
        chosen = resumes[0]

    rid = chosen["id"]
    response = _user_request(
        profile,
        session,
        "GET",
        f"https://api.hh.ru/resumes/{rid}",
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "hh_resume",
                "message": "Не удалось загрузить резюме",
                "hh_status": response.status_code,
            },
        )

    data = response.json()
    resume_text = resume_to_text(data)

    profile.hh_resume_id = rid
    profile.hh_resume_title = chosen.get("title") or data.get("title")
    profile.resume_text = resume_text
    profile.skills = ", ".join((data.get("skill_set") or [])[:20])[:255]
    session.commit()
    session.refresh(profile)

    return {
        "resume_id": rid,
        "resume_title": profile.hh_resume_title,
        "resume_text_length": len(resume_text),
        "resumes_available": len(resumes),
    }


def _reset_daily_counter_if_needed(profile: Profile) -> None:
    today = datetime.utcnow().date()
    if profile.applications_day is None or profile.applications_day.date() < today:
        profile.applications_today = 0
        profile.applications_day = datetime.utcnow()


def _already_applied(profile_id: int, vacancy_hh_id: str, session: Session) -> bool:
    existing = session.execute(
        select(HhApplication).where(
            HhApplication.profile_id == profile_id,
            HhApplication.vacancy_hh_id == vacancy_hh_id,
            HhApplication.status == "applied",
        )
    ).scalar_one_or_none()
    return existing is not None


def apply_to_vacancy(
    profile: Profile,
    session: Session,
    *,
    vacancy_hh_id: str,
    message: str | None = None,
    analysis_id: int | None = None,
) -> dict:
    if not profile.hh_resume_id:
        raise HTTPException(
            status_code=400,
            detail="Select resume first: sync from hh.ru",
        )

    _reset_daily_counter_if_needed(profile)

    if profile.applications_today >= AUTO_APPLY_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "apply_daily_limit",
                "message": f"Лимит откликов в день: {AUTO_APPLY_DAILY_LIMIT}",
            },
        )

    if _already_applied(profile.id, vacancy_hh_id, session):
        return {
            "ok": True,
            "already_applied": True,
            "vacancy_hh_id": vacancy_hh_id,
        }

    payload = {
        "vacancy_id": vacancy_hh_id,
        "resume_id": profile.hh_resume_id,
    }
    if message:
        payload["message"] = message[:5000]

    response = _user_request(
        profile,
        session,
        "POST",
        "https://api.hh.ru/negotiations",
        data=payload,
    )

    if response.status_code not in {201, 303}:
        error_text = response.text[:500]
        record = HhApplication(
            profile_id=profile.id,
            vacancy_hh_id=vacancy_hh_id,
            analysis_id=analysis_id,
            status="failed",
            message=message,
            error=error_text,
        )
        session.add(record)
        session.commit()

        raise HTTPException(
            status_code=502,
            detail={
                "code": "hh_apply_failed",
                "message": "hh.ru отклонил отклик",
                "hh_status": response.status_code,
                "hh_response": error_text,
            },
        )

    profile.applications_today += 1
    profile.applications_day = datetime.utcnow()

    record = HhApplication(
        profile_id=profile.id,
        vacancy_hh_id=vacancy_hh_id,
        analysis_id=analysis_id,
        status="applied",
        message=message,
    )
    session.add(record)
    session.commit()

    return {
        "ok": True,
        "already_applied": False,
        "vacancy_hh_id": vacancy_hh_id,
        "applications_today": profile.applications_today,
    }


def try_auto_apply_after_analysis(
    profile: Profile,
    session: Session,
    analysis: VacancyAnalysis,
    cover_letter_text: str | None = None,
) -> dict | None:
    if not profile.auto_apply_enabled:
        return None

    if not profile.hh_access_token or not profile.hh_resume_id:
        return None

    if analysis.match_score < AUTO_APPLY_MIN_MATCH or not analysis.should_apply:
        return None

    vacancy = analysis.vacancy
    if _already_applied(profile.id, vacancy.hh_id, session):
        return {"skipped": True, "reason": "already_applied"}

    try:
        return apply_to_vacancy(
            profile,
            session,
            vacancy_hh_id=vacancy.hh_id,
            message=cover_letter_text,
            analysis_id=analysis.id,
        )
    except HTTPException as error:
        logger.warning("Auto-apply failed: %s", error.detail)
        return {"skipped": True, "reason": str(error.detail)}
