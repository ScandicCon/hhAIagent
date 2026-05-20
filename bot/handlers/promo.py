from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import PRO_CONTACT, PRO_PRICE_RUB, YOOKASSA_ENABLED
from bot.handlers.common import reply_backend_error
from bot.keyboards import BTN_BUY_PRO, main_menu_keyboard
from bot.services.payments_client import create_pro_payment
from bot.services.subscription_client import get_usage, redeem_promo
from bot.utils.usage_text import format_usage

router = Router()


@router.message(Command("promo"))
async def promo_command(message: Message, state: FSMContext):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /promo КОД\nПример: /promo LAUNCH2026")
        return

    await _redeem(message, state, parts[1].strip())


@router.message(F.text == BTN_BUY_PRO)
async def buy_pro_button(message: Message, state: FSMContext):
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer("Сначала отправь резюме через /start.")
        return

    if YOOKASSA_ENABLED:
        try:
            payment = await create_pro_payment(profile_id)
        except HTTPStatusError as error:
            if error.response.status_code == 503:
                await _buy_pro_manual(message)
                return
            await reply_backend_error(message, error)
            return
        except RequestError as error:
            await reply_backend_error(message, error)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"Оплатить {payment['amount_rub']} ₽",
                        url=payment["confirmation_url"],
                    )
                ],
            ]
        )
        await message.answer(
            f"<b>Тариф Pro — {PRO_PRICE_RUB} ₽</b>\n\n"
            "После оплаты тариф активируется автоматически (обычно за 1–2 минуты).\n"
            "Проверить: /plan",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await _buy_pro_manual(message)


async def _buy_pro_manual(message: Message) -> None:
    await message.answer(
        f"<b>Тариф Pro — {PRO_PRICE_RUB} ₽/мес</b>\n\n"
        "Что входит:\n"
        "• 100 поисков в неделю\n"
        "• 50 сопроводительных писем\n"
        "• Утренний дайджест вакансий\n\n"
        f"1. Напиши {PRO_CONTACT} «Хочу Pro»\n"
        "2. Оплати (СБП / карта)\n"
        "3. Получи промокод: <code>/promo КОД</code>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


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
        reply_markup=main_menu_keyboard(),
    )
