import httpx

from bot.config import BACKEND_URL
from bot.services.http_client import async_client


def profile_name(telegram_id: int) -> str:
    return f"tg_{telegram_id}"


async def upsert_profile(
    telegram_id: int,
    resume_text: str,
    referral_code: str | None = None,
) -> dict:
    payload = {
        "name": profile_name(telegram_id),
        "resume_text": resume_text,
        "skills": resume_text[:255],
    }
    if referral_code:
        payload["referral_code"] = referral_code

    async with async_client(timeout=30) as client:
        response = await client.post(
            f"{BACKEND_URL}/profiles/upsert",
            json=payload,
        )

    response.raise_for_status()
    return response.json()


async def find_best_vacancies(
    profile_id: int,
    search_text: str,
    per_page: int = 7,
    filters: dict | None = None,
) -> dict:
    payload: dict = {
        "text": search_text,
        "per_page": per_page,
    }
    if filters:
        payload["filters"] = filters

    async with async_client(timeout=180) as client:
        response = await client.post(
            f"{BACKEND_URL}/vacancies/best/{profile_id}",
            json=payload,
        )

    response.raise_for_status()
    return response.json()


async def get_analyses(profile_id: int) -> list[dict]:
    async with async_client(timeout=30) as client:
        response = await client.get(
            f"{BACKEND_URL}/vacancies/analyses/{profile_id}",
        )

    response.raise_for_status()
    return response.json()


async def create_cover_letter(analysis_id: int) -> dict:
    async with async_client(timeout=120) as client:
        response = await client.post(
            f"{BACKEND_URL}/vacancies/cover-letter/{analysis_id}",
        )

    response.raise_for_status()
    return response.json()


async def improve_cover_letter(cover_letter_id: int, instruction: str) -> dict:
    async with async_client(timeout=120) as client:
        response = await client.post(
            f"{BACKEND_URL}/vacancies/cover-letter/{cover_letter_id}/improve",
            json={"instruction": instruction},
        )

    response.raise_for_status()
    return response.json()
