from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import BTN_INVITE, main_menu_keyboard
from bot.services.payments_client import get_referral_info

router = Router()


@router.message(Command("invite"))
@router.message(F.text == BTN_INVITE)
async def invite_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        info = await get_referral_info(profile_id)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    reward = info["reward_per_friend"]
    await message.answer(
        "<b>Приведи друга</b>\n\n"
        f"Твоя ссылка:\n{info['referral_link']}\n\n"
        f"За каждого друга, который сохранит резюме, "
        f"ты получишь <b>+{reward}</b> поисков на неделю.\n\n"
        f"Приглашено: {info['invited_count']}\n"
        f"Бонусных поисков сейчас: {info['bonus_searches']}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
