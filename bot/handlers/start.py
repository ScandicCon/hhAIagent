from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_menu_keyboard
from bot.states.user_states import UserFlow
from bot.texts import HELP_TEXT


router = Router()


def _parse_referral_code(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    arg = parts[1].strip()
    if arg.lower().startswith("ref_"):
        return arg[4:]
    return None


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    referral_code = _parse_referral_code(message.text)
    await state.clear()

    if referral_code:
        await state.update_data(pending_referral_code=referral_code)

    await state.set_state(UserFlow.waiting_resume)

    invite_hint = ""
    if referral_code:
        invite_hint = "\n\nПо ссылке друга — после сохранения резюме он получит бонусные поиски."

    await message.answer(
        "Привет! Я AI-бот для поиска вакансий на hh.ru.\n\n"
        "Пришли резюме текстом: опыт, навыки, стек и проекты "
        f"(минимум 20 символов).{invite_hint}",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("resume"))
async def resume_command(message: Message, state: FSMContext):
    await state.set_state(UserFlow.waiting_resume)
    await message.answer(
        "Отправь обновлённое резюме одним сообщением.",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("profile_id"):
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме.")
        return

    await state.set_state(UserFlow.waiting_search)
    await message.answer(
        "Напиши профессию или стек.\n"
        "Например: Python backend\n\n"
        "Дальше выберешь уровень, опыт, город и зарплату.",
        reply_markup=main_menu_keyboard(),
    )
