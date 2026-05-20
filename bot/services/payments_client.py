import httpx

from bot.config import BACKEND_URL
from bot.services.http_client import async_client


async def create_pro_payment(profile_id: int) -> dict:
    async with async_client(timeout=30) as client:
        response = await client.post(f"{BACKEND_URL}/payments/pro/{profile_id}")
    response.raise_for_status()
    return response.json()


async def get_referral_info(profile_id: int) -> dict:
    async with async_client(timeout=15) as client:
        response = await client.get(f"{BACKEND_URL}/referrals/info/{profile_id}")
    response.raise_for_status()
    return response.json()
