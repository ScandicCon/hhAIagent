from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import (
    BTN_HELP,
    BTN_RESUME,
    BTN_SEARCH,
    main_menu_keyboard,
)
from bot.services.profile_session import ensure_profile_id
from bot.states.user_states import UserFlow
from bot.texts import HELP_TEXT


router = Router()


@router.message(F.text == BTN_HELP)
async def menu_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(F.text == BTN_RESUME)
async def menu_resume(message: Message, state: FSMContext):
    profile_id = await ensure_profile_id(state, message.from_user.id)
    if profile_id is None:
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме через /start.")
        return

    await state.set_state(UserFlow.waiting_resume)
    await message.answer(
        "Отправь новый текст резюме.\n"
        "Текущая версия попадёт в «История резюме».",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(F.text == BTN_SEARCH)
async def menu_search(message: Message, state: FSMContext):
    profile_id = await ensure_profile_id(state, message.from_user.id)
    if profile_id is None:
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме.")
        return

    await state.set_state(UserFlow.waiting_search)
    await message.answer(
        "Напиши профессию или стек для поиска.\n"
        "Например: Python backend\n\n"
        "На следующем шаге: уровень, опыт, удалёнка, город и зарплата.",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )

