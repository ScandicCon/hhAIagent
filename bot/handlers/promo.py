from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import BTN_BUY_PRO, main_menu_keyboard
from bot.services.checkout import send_pro_checkout
from bot.services.subscription_client import get_usage, redeem_promo
from bot.utils.product_cards import format_product_catalog
from bot.utils.usage_text import format_usage

router = Router()


@router.message(Command("tariffs"))
async def tariffs_command(message: Message):
    await message.answer(
        format_product_catalog(),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("buy"))
@router.message(F.text == BTN_BUY_PRO)
async def buy_pro_button(message: Message, state: FSMContext):
    await send_pro_checkout(message, state)


@router.message(Command("promo"))
async def promo_command(message: Message, state: FSMContext):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /promo КОД\nПример: /promo LAUNCH2026")
        return

    await _redeem(message, state, parts[1].strip())


async def _redeem(message: Message, state: FSMContext, code: str) -> None:
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        result = await redeem_promo(profile_id, code)
        usage = await get_usage(profile_id)
    except HTTPStatusError as error:
        if error.response.status_code == 404:
            await message.answer("Промокод не найден или недействителен.")
            return
        await reply_backend_error(message, error)
        return
    except RequestError as error:
        await reply_backend_error(message, error)
        return

    await message.answer(
        f"Готово. {result['message']}\n\n{format_usage(usage)}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
