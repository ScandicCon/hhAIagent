from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import BTN_MY_RESUME, BTN_RESUME_HISTORY, main_menu_keyboard
from bot.services.backend_client import get_resume_versions
from bot.services.profile_session import ensure_profile_id
from bot.utils.formatters import escape_html, split_message


router = Router()

PREVIEW_LEN = 800


def _format_version_date(created_at: str | datetime) -> str:
    if isinstance(created_at, str):
        raw = created_at.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return created_at[:16]
    else:
        dt = created_at
    return dt.strftime("%d.%m.%Y %H:%M")


async def _send_resume_chunks(message: Message, header: str, body: str) -> None:
    text = f"{header}\n\n<pre>{escape_html(body)}</pre>"
    for chunk in split_message(text, limit=4000):
        await message.answer(chunk, parse_mode="HTML")


@router.message(Command("myresume"))
@router.message(F.text == BTN_MY_RESUME)
async def show_my_resume(message: Message, state: FSMContext):
    profile_id = await ensure_profile_id(state, message.from_user.id)
    if profile_id is None:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        data = await get_resume_versions(message.from_user.id)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    current = (data.get("current") or "").strip()
    if not current:
        await message.answer("Резюме пустое. Нажми «Обновить резюме» и отправь текст.")
        return

    await _send_resume_chunks(
        message,
        "<b>Твоё актуальное резюме</b>",
        current,
    )
    await message.answer(
        "Чтобы изменить — «Обновить резюме». Старые версии — «История резюме».",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Command("resumehistory"))
@router.message(F.text == BTN_RESUME_HISTORY)
async def show_resume_history(message: Message, state: FSMContext):
    profile_id = await ensure_profile_id(state, message.from_user.id)
    if profile_id is None:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        data = await get_resume_versions(message.from_user.id)
    except (HTTPStatusError, RequestError) as error:
        await reply_backend_error(message, error)
        return

    versions = data.get("versions") or []
    if not versions:
        await message.answer(
            "Пока нет сохранённых версий — они появятся после первого обновления резюме.",
            reply_markup=main_menu_keyboard(message.from_user.id),
        )
        return

    lines = ["<b>История резюме</b> (от новых к старым):\n"]
    for index, item in enumerate(versions, start=1):
        when = _format_version_date(item["created_at"])
        preview = (item.get("resume_text") or "").strip()
        if len(preview) > 120:
            preview = preview[:120] + "…"
        lines.append(
            f"{index}. <b>{when}</b> — {escape_html(preview)}"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")

    for index, item in enumerate(versions[:5], start=1):
        body = (item.get("resume_text") or "").strip()
        when = _format_version_date(item["created_at"])
        header = f"<b>Версия {index}</b> ({when})"
        if len(body) > PREVIEW_LEN:
            body = body[:PREVIEW_LEN] + "\n\n… (обрезано, полный текст в БД)"
        await _send_resume_chunks(message, header, body)

    if len(versions) > 5:
        await message.answer(
            f"Показаны 5 из {len(versions)} версий. Остальные хранятся в базе.",
            reply_markup=main_menu_keyboard(message.from_user.id),
        )
