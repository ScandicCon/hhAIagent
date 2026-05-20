import httpx

from bot.config import BACKEND_URL
from bot.services.http_client import async_client


async def get_hh_link(telegram_id: int) -> str:
    async with async_client(timeout=15) as client:
        response = await client.get(f"{BACKEND_URL}/hh/link/{telegram_id}")
    response.raise_for_status()
    return response.json()["url"]


async def get_hh_status(profile_id: int) -> dict:
    async with async_client(timeout=15) as client:
        response = await client.get(f"{BACKEND_URL}/hh/status/{profile_id}")
    response.raise_for_status()
    return response.json()


async def sync_resume(profile_id: int, resume_id: str | None = None) -> dict:
    payload = {}
    if resume_id:
        payload["resume_id"] = resume_id

    async with async_client(timeout=60) as client:
        response = await client.post(
            f"{BACKEND_URL}/hh/sync-resume/{profile_id}",
            json=payload,
        )
    response.raise_for_status()
    return response.json()


async def toggle_auto_apply(profile_id: int, enabled: bool) -> dict:
    async with async_client(timeout=15) as client:
        response = await client.post(
            f"{BACKEND_URL}/hh/auto-apply/{profile_id}",
            json={"enabled": enabled},
        )
    response.raise_for_status()
    return response.json()


async def apply_to_vacancy(analysis_id: int, message: str | None = None) -> dict:
    payload = {}
    if message:
        payload["message"] = message

    async with async_client(timeout=60) as client:
        response = await client.post(
            f"{BACKEND_URL}/hh/apply/{analysis_id}",
            json=payload,
        )
    response.raise_for_status()
    return response.json()
