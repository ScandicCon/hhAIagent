from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import cover_letter_inline_keyboard, main_menu_keyboard
from bot.services.backend_client import create_cover_letter, improve_cover_letter
from bot.states.user_states import UserFlow
from bot.utils.formatters import format_vacancy_detail, split_message


router = Router()


@router.callback_query(F.data.startswith("detail:"))
async def vacancy_detail_callback(callback: CallbackQuery, state: FSMContext):
    analysis_id = callback.data.split(":", 1)[1]
    data = await state.get_data()
    vacancies = data.get("last_vacancies") or {}
    vacancy = vacancies.get(analysis_id)

    if vacancy is None:
        await callback.answer("Данные устарели. Выполни поиск заново.", show_alert=True)
        return

    text = format_vacancy_detail(vacancy)
    await callback.message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data.startswith("cover:"))
async def cover_letter_callback(callback: CallbackQuery, state: FSMContext):
    analysis_id = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await callback.message.answer("Генерирую сопроводительное письмо...")

    try:
        result = await create_cover_letter(analysis_id)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(callback.message, error)
        return

    cover_letter_id = result["cover_letter_id"]
    title = result.get("title", "вакансия")
    cached = " (из кэша)" if result.get("cached") else ""
    letter_text = result["cover_letter"]

    header = f"<b>Сопроводительное письмо</b>\n{title}{cached}\n\n"
    full_text = header + letter_text

    for index, chunk in enumerate(split_message(full_text)):
        reply_markup = (
            cover_letter_inline_keyboard(cover_letter_id) if index == 0 else None
        )
        parse_mode = "HTML" if index == 0 else None
        await callback.message.answer(
            chunk,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )


@router.callback_query(F.data.startswith("apply:"))
async def apply_vacancy_callback(callback: CallbackQuery, state: FSMContext):
    analysis_id = callback.data.split(":", 1)[1]
    data = await state.get_data()
    vacancies = data.get("last_vacancies") or {}
    vacancy = vacancies.get(analysis_id)

    if vacancy is None:
        await callback.answer("Данные устарели. Выполни поиск заново.", show_alert=True)
        return

    url = vacancy.get("url")
    keyboard = None
    if url:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Открыть вакансию на hh.ru", url=url)],
            ]
        )

    await callback.answer()
    await callback.message.answer(
        "<b>Отклик вручную на hh.ru</b>\n\n"
        "Автоотклик через API недоступен: hh.ru не даёт токен соискателя.\n\n"
        "1. Нажми «Сопроводительное» — сгенерируй письмо\n"
        "2. Открой вакансию на hh.ru\n"
        "3. Вставь письмо в форму отклика",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("improve:"))
async def improve_cover_callback(callback: CallbackQuery, state: FSMContext):
    cover_letter_id = int(callback.data.split(":", 1)[1])

    await state.update_data(improve_cover_letter_id=cover_letter_id)
    await state.set_state(UserFlow.waiting_improve_instruction)

    await callback.message.answer(
        "Напиши, как улучшить письмо.\n"
        "Например: сделай короче и добавь опыт с FastAPI",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.message(UserFlow.waiting_improve_instruction)
async def improve_instruction_handler(message: Message, state: FSMContext):
    instruction = (message.text or "").strip()
    data = await state.get_data()
    cover_letter_id = data.get("improve_cover_letter_id")

    if not instruction:
        await message.answer("Нужна инструкция текстом.")
        return

    if not cover_letter_id:
        await state.set_state(UserFlow.waiting_search)
        await message.answer("Сессия сброшена. Начни с поиска вакансий.")
        return

    status_message = await message.answer("Улучшаю письмо...")

    try:
        result = await improve_cover_letter(cover_letter_id, instruction)
    except (HTTPStatusError, RequestError) as error:
        await status_message.delete()
        await reply_backend_error(message, error)
        return

    await status_message.delete()
    await state.set_state(UserFlow.waiting_search)

    improved_text = result["improved_text"]
    header = "<b>Обновлённое сопроводительное письмо</b>\n\n"

    for index, chunk in enumerate(split_message(header + improved_text)):
        reply_markup = (
            cover_letter_inline_keyboard(cover_letter_id) if index == 0 else None
        )
        parse_mode = "HTML" if index == 0 else None
        await message.answer(
            chunk,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
