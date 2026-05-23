from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.config import ADMIN_API_KEY, ADMIN_TELEGRAM_IDS, BACKEND_URL
from bot.handlers.common import reply_backend_error
from bot.keyboards import BTN_ADMIN, main_menu_keyboard
from bot.services.http_client import get_http_client
from bot.utils.usage_text import format_usage

router = Router()

ADMIN_HELP = (
    "<b>Панель администратора</b>\n\n"
    "<b>Для себя</b>\n"
    "/pro — включить Pro на своём аккаунте\n"
    "/reset_me — сбросить свои лимиты на неделю\n"
    "/plan — тариф и лимиты\n\n"
    "<b>Для пользователей</b>\n"
    "/activate_pro TELEGRAM_ID — выдать Pro\n"
    "/user TELEGRAM_ID — инфо о пользователе\n"
    "/stats — статистика бота\n\n"
    "<b>Промо</b>\n"
    "/promo КОД — активировать промокод на себе\n\n"
    "У админа лимиты поисков и писем не списываются."
)


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_TELEGRAM_IDS


async def _profile_id_by_telegram(telegram_id: int) -> int | None:
    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}/profiles/telegram/{telegram_id}",
        timeout=15.0,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["id"]


async def _admin_post(path: str) -> dict:
    client = get_http_client()
    response = await client.post(
        f"{BACKEND_URL}{path}",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


async def _admin_get(path: str) -> dict:
    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}{path}",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


@router.message(Command("admin"))
@router.message(F.text == BTN_ADMIN)
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "Команда только для администратора.\n\n"
            f"Твой Telegram ID: <code>{message.from_user.id}</code>\n"
            "Добавь его в <code>ADMIN_TELEGRAM_IDS</code> в .env на сервере, "
            "затем: <code>docker compose up -d --force-recreate bot api</code>",
            parse_mode="HTML",
        )
        return

    await message.answer(
        ADMIN_HELP,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("pro"))
async def admin_pro_self(message: Message):
    if not is_admin(message.from_user.id):
        return

    if not ADMIN_API_KEY:
        await message.answer("Задай ADMIN_API_KEY в .env")
        return

    profile_id = await _profile_id_by_telegram(message.from_user.id)
    if profile_id is None:
        await message.answer("Сначала нажми /start и отправь резюме.")
        return

    try:
        usage = await _admin_post(f"/subscription/activate-pro/{profile_id}")
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    await message.answer(
        f"Pro активирован на твоём аккаунте.\n\n{format_usage(usage)}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("reset_me"))
async def admin_reset_self(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    if not ADMIN_API_KEY:
        await message.answer("Задай ADMIN_API_KEY в .env")
        return

    data = await state.get_data()
    profile_id = data.get("profile_id")
    if profile_id is None:
        profile_id = await _profile_id_by_telegram(message.from_user.id)

    if profile_id is None:
        await message.answer("Сначала /start и резюме.")
        return

    try:
        usage = await _admin_post(f"/subscription/reset-usage/{profile_id}")
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    await message.answer(
        f"Лимиты сброшены.\n\n{format_usage(usage)}",
        parse_mode="HTML",
    )


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    if not ADMIN_API_KEY:
        await message.answer("Задай ADMIN_API_KEY в .env")
        return

    try:
        stats = await _admin_get("/subscription/admin/stats")
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    await message.answer(
        "<b>Статистика</b>\n\n"
        f"Пользователей: {stats['total_profiles']}\n"
        f"Pro: {stats['pro_profiles']}\n"
        f"Дайджест включён: {stats['digest_enabled']}",
        parse_mode="HTML",
    )


@router.message(Command("user"))
async def admin_user_info(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Формат: /user TELEGRAM_ID")
        return

    target_id = int(parts[1])
    profile_id = await _profile_id_by_telegram(target_id)
    if profile_id is None:
        await message.answer("Пользователь не найден.")
        return

    try:
        client = get_http_client()
        usage_response = await client.get(
            f"{BACKEND_URL}/subscription/usage/{profile_id}",
            timeout=15.0,
        )
        usage_response.raise_for_status()
        usage = usage_response.json()
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    await message.answer(
        f"<b>Пользователь</b> tg_{target_id}\n"
        f"Profile ID: {profile_id}\n\n"
        f"{format_usage(usage)}",
        parse_mode="HTML",
    )


@router.message(Command("activate_pro"))
async def activate_pro_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Команда только для администратора.")
        return

    if not ADMIN_API_KEY:
        await message.answer("ADMIN_API_KEY не задан в .env")
        return

    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(
            "Формат: /activate_pro TELEGRAM_ID\n"
            "Или для себя: /pro"
        )
        return

    target_telegram_id = int(parts[1])
    profile_id = await _profile_id_by_telegram(target_telegram_id)

    if profile_id is None:
        await message.answer(
            "Пользователь не найден. Пусть сначала нажмёт /start в боте."
        )
        return

    try:
        usage = await _admin_post(f"/subscription/activate-pro/{profile_id}")
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    await message.answer(
        f"Pro активирован для tg_{target_telegram_id} (profile #{profile_id}).\n\n"
        f"{format_usage(usage)}",
        parse_mode="HTML",
    )
