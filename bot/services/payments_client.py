from bot.config import BACKEND_URL
from bot.services.http_client import get_http_client


async def create_pro_payment(profile_id: int) -> dict:
    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}/payments/pro/{profile_id}",
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


async def get_referral_info(profile_id: int) -> dict:
    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}/referrals/info/{profile_id}",
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()
