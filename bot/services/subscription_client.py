import httpx

from bot.config import BACKEND_URL
from bot.services.http_client import async_client


async def get_usage(profile_id: int) -> dict:
    async with async_client(timeout=15) as client:
        response = await client.get(f"{BACKEND_URL}/subscription/usage/{profile_id}")
    response.raise_for_status()
    return response.json()


async def redeem_promo(profile_id: int, code: str) -> dict:
    async with async_client(timeout=15) as client:
        response = await client.post(
            f"{BACKEND_URL}/subscription/redeem/{profile_id}",
            json={"code": code},
        )
    response.raise_for_status()
    return response.json()


async def toggle_digest(profile_id: int, enabled: bool) -> dict:
    async with async_client(timeout=15) as client:
        response = await client.post(
            f"{BACKEND_URL}/subscription/digest/{profile_id}",
            json={"enabled": enabled},
        )
    response.raise_for_status()
    return response.json()
