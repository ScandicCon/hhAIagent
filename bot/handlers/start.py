from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import main_menu_keyboard
from bot.services.checkout import send_pro_checkout
from bot.services.profile_session import ensure_profile_id
from bot.services.subscription_client import get_usage
from bot.states.user_states import UserFlow
from bot.texts import HELP_TEXT
from bot.utils.usage_text import format_usage


router = Router()


def _parse_start_payload(text: str | None) -> tuple[str | None, str | None]:
    if not text:
        return None, None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    arg = parts[1].strip()
    lower = arg.lower()
    if lower.startswith("ref_"):
        return "referral", arg[4:]
    if lower == "pay":
        return "pay", None
    return None, None


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    kind, value = _parse_start_payload(message.text)
    await state.clear()

    invite_hint = ""
    if kind == "referral" and value:
        await state.update_data(pending_referral_code=value)
        invite_hint = "\n\nПо ссылке друга — после сохранения резюме он получит бонусные поиски."

    pending_pay = kind == "pay"
    if pending_pay:
        await state.update_data(pending_pay=True)
        invite_hint = "\n\nПосле резюме откроется оплата тарифа Pro (490 ₽)."

    try:
        profile_id = await ensure_profile_id(state, message.from_user.id)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    if profile_id is not None:
        await state.set_state(None)
        usage_line = ""
        try:
            usage = await get_usage(profile_id)
            usage_line = f"\n\n{format_usage(usage)}"
        except (HTTPStatusError, RequestError):
            pass

        await message.answer(
            "С возвращением! Резюме уже сохранено — можно сразу искать вакансии.\n"
            "«Моё резюме» — посмотреть текст, «Обновить резюме» — заменить "
            "(старая версия попадёт в историю)."
            f"{usage_line}{invite_hint}",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(message.from_user.id),
        )
        if pending_pay:
            await state.update_data(pending_pay=False)
            await send_pro_checkout(message, state)
        return

    await state.set_state(UserFlow.waiting_resume)
    await message.answer(
        "Привет! Я AI-бот для поиска вакансий на hh.ru.\n\n"
        "Пришли резюме текстом: опыт, навыки, стек и проекты "
        f"(минимум 20 символов).{invite_hint}",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("myid"))
async def myid_handler(message: Message):
    await message.answer(
        f"Твой Telegram ID: <code>{message.from_user.id}</code>\n"
        "Его нужно указать в ADMIN_TELEGRAM_IDS в .env.",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("resume"))
async def resume_command(message: Message, state: FSMContext):
    profile_id = await ensure_profile_id(state, message.from_user.id)
    if profile_id is None:
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме через /start.")
        return

    await state.set_state(UserFlow.waiting_resume)
    await message.answer(
        "Отправь обновлённое резюме одним сообщением.\n"
        "Текущая версия сохранится в «История резюме».",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext):
    profile_id = await ensure_profile_id(state, message.from_user.id)
    if profile_id is None:
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме.")
        return

    await state.set_state(UserFlow.waiting_search)
    await message.answer(
        "Напиши профессию или стек.\n"
        "Например: Python backend\n\n"
        "Дальше выберешь уровень, опыт, город и зарплату.",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
