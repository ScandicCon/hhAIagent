from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from httpx import HTTPStatusError, RequestError

from bot.config import PRO_CONTACT, PRO_PRICE_RUB, YOOKASSA_ENABLED
from bot.handlers.common import reply_backend_error
from bot.keyboards import main_menu_keyboard
from bot.services.payments_client import create_pro_payment
from bot.utils.product_cards import format_pro_checkout_card


async def send_pro_checkout(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer(
            "Сначала отправь резюме через /start — затем снова «Купить Pro».",
            reply_markup=main_menu_keyboard(message.from_user.id),
        )
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
            format_pro_checkout_card(),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return

    await _buy_pro_manual(message)


async def _buy_pro_manual(message: Message) -> None:
    await message.answer(
        f"<b>Тариф Pro — {PRO_PRICE_RUB} ₽</b>\n\n"
        "Что входит:\n"
        "• 100 поисков в неделю\n"
        "• 50 сопроводительных писем\n"
        "• Утренний дайджест вакансий\n\n"
        f"1. Напиши {PRO_CONTACT} «Хочу Pro»\n"
        "2. Оплати (СБП / карта)\n"
        "3. Получи промокод: <code>/promo КОД</code>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
