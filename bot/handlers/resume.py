from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.handlers.promo import send_pro_checkout
from bot.keyboards import main_menu_keyboard
from bot.services.backend_client import upsert_profile
from bot.services.subscription_client import get_usage
from bot.utils.usage_text import format_usage
from bot.states.user_states import UserFlow


router = Router()

MIN_RESUME_LENGTH = 20


@router.message(UserFlow.waiting_resume)
async def resume_handler(message: Message, state: FSMContext):
    resume_text = (message.text or "").strip()

    if not resume_text:
        await message.answer("Нужен текст резюме, не файл и не стикер.")
        return

    if len(resume_text) < MIN_RESUME_LENGTH:
        await message.answer(
            "Резюме слишком короткое. Напиши хотя бы стек, опыт и проекты."
        )
        return

    data = await state.get_data()
    referral_code = data.get("pending_referral_code")

    try:
        profile = await upsert_profile(
            telegram_id=message.from_user.id,
            resume_text=resume_text,
            referral_code=referral_code,
        )
    except HTTPStatusError as error:
        if referral_code and error.response.status_code == 400:
            profile = await upsert_profile(
                telegram_id=message.from_user.id,
                resume_text=resume_text,
            )
            referral_note = "\n\n⚠️ Реферальный код не применился (уже использован или неверный)."
        else:
            await reply_backend_error(message, error)
            return
    except RequestError as error:
        await reply_backend_error(message, error)
        return
    else:
        referral_note = ""
        if referral_code:
            referral_note = "\n\n✅ Реферальный код друга учтён — ему начислены бонусные поиски."

    update = {"profile_id": profile["id"]}
    if referral_code:
        update["pending_referral_code"] = None
    await state.update_data(**update)
    await state.set_state(UserFlow.waiting_search)

    try:
        usage = await get_usage(profile["id"])
        usage_line = f"\n\n{format_usage(usage)}"
    except (HTTPStatusError, RequestError):
        usage_line = ""

    await message.answer(
        "Резюме сохранил.\n\n"
        "Напиши поисковый запрос или нажми «Искать вакансии».\n"
        "Например: Python backend"
        f"{referral_note}"
        f"{usage_line}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )

    if data.get("pending_pay"):
        await state.update_data(pending_pay=False)
        await send_pro_checkout(message, state)
