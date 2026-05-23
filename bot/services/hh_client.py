from bot.config import BACKEND_URL
from bot.services.http_client import get_http_client


async def get_hh_link(telegram_id: int) -> str:
    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}/hh/link/{telegram_id}",
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["url"]


async def get_hh_status(profile_id: int) -> dict:
    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}/hh/status/{profile_id}",
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


async def sync_resume(profile_id: int, resume_id: str | None = None) -> dict:
    payload = {}
    if resume_id:
        payload["resume_id"] = resume_id

    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/hh/sync-resume/{profile_id}",
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


async def toggle_auto_apply(profile_id: int, enabled: bool) -> dict:
    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/hh/auto-apply/{profile_id}",
        json={"enabled": enabled},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


async def apply_to_vacancy(analysis_id: int, message: str | None = None) -> dict:
    payload = {}
    if message:
        payload["message"] = message

    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/hh/apply/{analysis_id}",
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()
