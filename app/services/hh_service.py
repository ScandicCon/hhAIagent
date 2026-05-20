import logging
import time

import requests
from fastapi import HTTPException

from app.config.core import HH_USER_AGENT
from app.services.hh_auth_service import get_hh_app_token
from app.services.search_filters import VacancySearchFilters, build_hh_search_params

logger = logging.getLogger(__name__)

HH_REQUEST_TIMEOUT_SEC = 30
HH_REQUEST_RETRIES = 3


def get_hh_headers(*, force_token_refresh: bool = False) -> dict:
    access_token = get_hh_app_token(force_refresh=force_token_refresh)

    return {
        "User-Agent": HH_USER_AGENT,
        "Authorization": f"Bearer {access_token}",
    }


def _hh_get(url: str, *, params: dict | None = None) -> requests.Response:
    last_error: Exception | None = None
    refreshed_token = False

    for attempt in range(1, HH_REQUEST_RETRIES + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=get_hh_headers(force_token_refresh=refreshed_token),
                timeout=HH_REQUEST_TIMEOUT_SEC,
            )
            if response.status_code == 401 and not refreshed_token:
                refreshed_token = True
                logger.info("HH 401, refreshing token and retrying")
                continue
            return response
        except requests.exceptions.Timeout as error:
            last_error = error
            logger.warning("HH timeout attempt %s/%s: %s", attempt, HH_REQUEST_RETRIES, url)
            if attempt < HH_REQUEST_RETRIES:
                time.sleep(1.5 * attempt)

    raise HTTPException(
        status_code=502,
        detail={
            "code": "hh_timeout",
            "message": "hh.ru не ответил вовремя. Повтори поиск через минуту.",
        },
    ) from last_error


def _vacancy_preview(item: dict) -> dict:
    salary = item.get("salary") or {}
    salary_from = salary.get("from")
    salary_to = salary.get("to")
    currency = salary.get("currency", "")

    salary_text = None
    if salary_from or salary_to:
        parts = []
        if salary_from:
            parts.append(str(salary_from))
        if salary_to:
            parts.append(str(salary_to))
        salary_text = "–".join(parts) + (f" {currency}" if currency else "")

    experience = item.get("experience") or {}
    schedule = item.get("schedule") or {}
    employment = item.get("employment") or {}
    area = item.get("area") or {}

    return {
        "hh_id": item.get("id"),
        "title": item.get("name"),
        "company": item.get("employer", {}).get("name"),
        "url": item.get("alternate_url"),
        "experience": experience.get("name"),
        "schedule": schedule.get("name"),
        "employment": employment.get("name"),
        "area": area.get("name"),
        "salary": salary_text,
    }


def search_vacancies(
    text: str,
    per_page: int = 10,
    page: int = 0,
    filters: VacancySearchFilters | None = None,
):
    response = _hh_get(
        "https://api.hh.ru/vacancies",
        params=build_hh_search_params(
            text,
            filters,
            per_page=per_page,
            page=page,
        ),
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "HH vacancies search error",
                "hh_status": response.status_code,
                "hh_response": response.text,
                "request_url": response.url,
            },
        )

    data = response.json()

    vacancies = []

    for item in data.get("items", []):
        vacancies.append(_vacancy_preview(item))

    return vacancies


def get_vacancy_by_id(hh_id: str):
    response = _hh_get(f"https://api.hh.ru/vacancies/{hh_id}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "HH vacancy detail error",
                "hh_status": response.status_code,
                "hh_response": response.text,
                "request_url": response.url,
            },
        )

    item = response.json()

    preview = _vacancy_preview(item)
    preview.update({
        "description": item.get("description"),
        "skills": [skill["name"] for skill in item.get("key_skills", [])],
    })
    return preview
