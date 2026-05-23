from bot.config import ADMIN_API_KEY, BACKEND_URL
from bot.services.http_client import get_http_client


async def get_usage(profile_id: int) -> dict:
    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}/subscription/usage/{profile_id}",
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


async def redeem_promo(profile_id: int, code: str) -> dict:
    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/subscription/redeem/{profile_id}",
        json={"code": code},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


async def toggle_digest(profile_id: int, enabled: bool) -> dict:
    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/subscription/digest/{profile_id}",
        json={"enabled": enabled},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


async def mark_digest_sent(profile_id: int) -> None:
    if not ADMIN_API_KEY:
        return
    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/subscription/digest-mark/{profile_id}",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        timeout=15.0,
    )
    response.raise_for_status()
