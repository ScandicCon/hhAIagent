from aiogram.fsm.context import FSMContext
from httpx import HTTPStatusError, RequestError

from bot.services.backend_client import get_profile_by_telegram


async def ensure_profile_id(state: FSMContext, telegram_id: int) -> int | None:
    data = await state.get_data()
    profile_id = data.get("profile_id")
    if profile_id is not None:
        return int(profile_id)

    try:
        profile = await get_profile_by_telegram(telegram_id)
    except HTTPStatusError as error:
        if error.response.status_code == 404:
            return None
        raise
    except RequestError:
        raise

    await state.update_data(profile_id=profile["id"])
    return int(profile["id"])
