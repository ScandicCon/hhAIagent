from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import (
    BTN_AUTO_APPLY,
    BTN_CONNECT_HH,
    BTN_SYNC_HH,
    main_menu_keyboard,
)

router = Router()

HH_APPLICANT_API_MSG = (
    "<b>hh.ru изменил правила API</b>\n\n"
    "С декабря 2024 токен <b>соискателя</b> для API не поддерживается. "
    "Поддержка hh.ru подтвердила: резюме и отклики через API недоступны.\n\n"
    "<b>Что работает в боте:</b>\n"
    "• Резюме — отправь <b>текстом</b> (/start)\n"
    "• Поиск вакансий и AI-анализ\n"
    "• Сопроводительное письмо — кнопка под вакансией\n"
    "• Отклик — «Отклик на hh.ru» → открой вакансию и вставь письмо вручную\n\n"
    "Подробнее: docs/HH_CONNECT.md в проекте"
)


@router.message(Command("connect_hh", "sync_resume", "auto_apply", "hh_status"))
@router.message(F.text.in_({BTN_CONNECT_HH, BTN_SYNC_HH, BTN_AUTO_APPLY}))
async def hh_deprecated(message: Message, state: FSMContext):
    await message.answer(
        HH_APPLICANT_API_MSG,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
