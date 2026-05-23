from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import (
    BTN_DIGEST_OFF,
    BTN_DIGEST_ON,
    BTN_PLAN,
    main_menu_keyboard,
)
from bot.services.subscription_client import get_usage, toggle_digest
from bot.utils.product_cards import format_product_catalog
from bot.utils.usage_text import format_usage, upgrade_message


router = Router()


@router.message(Command("plan"))
@router.message(F.text == BTN_PLAN)
async def show_plan(message: Message, state: FSMContext):
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        usage = await get_usage(profile_id)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    digest_hint = "включён" if usage.get("digest_enabled") else "выключен"
    await message.answer(
        f"{format_usage(usage)}\n\n"
        f"Утренний дайджест: <b>{digest_hint}</b>\n\n"
        f"{upgrade_message()}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
    await message.answer(format_product_catalog(), parse_mode="HTML")


@router.message(F.text == BTN_DIGEST_ON)
async def digest_on(message: Message, state: FSMContext):
    await _set_digest(message, state, enabled=True)


@router.message(F.text == BTN_DIGEST_OFF)
async def digest_off(message: Message, state: FSMContext):
    await _set_digest(message, state, enabled=False)


async def _set_digest(message: Message, state: FSMContext, enabled: bool) -> None:
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        usage = await toggle_digest(profile_id, enabled)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    status = "включён" if enabled else "выключен"
    await message.answer(
        f"Дайджест {status} (каждый день в 9:00 МСК).\n\n"
        f"{format_usage(usage)}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
