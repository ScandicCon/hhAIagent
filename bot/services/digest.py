import asyncio
import logging
import os
from datetime import datetime

from aiogram import Bot
from zoneinfo import ZoneInfo

from bot.config import ADMIN_API_KEY, BACKEND_URL
from bot.services.backend_client import find_best_vacancies
from bot.services.http_client import get_http_client
from bot.services.subscription_client import mark_digest_sent
from app.services.search_filters import VacancySearchFilters, parse_filters_json
from bot.utils.formatters import format_vacancy_card, split_message

logger = logging.getLogger(__name__)
MSK = ZoneInfo("Europe/Moscow")
DIGEST_CONCURRENCY = int(os.getenv("DIGEST_CONCURRENCY", "3"))
TELEGRAM_SEND_DELAY_SEC = float(os.getenv("TELEGRAM_SEND_DELAY_SEC", "0.05"))


async def fetch_digest_recipients() -> list[dict]:
    if not ADMIN_API_KEY:
        return []

    client = get_http_client()
    response = await client.get(
        f"{BACKEND_URL}/subscription/digest-recipients",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


async def _send_digest_to_recipient(bot: Bot, recipient: dict) -> None:
    telegram_id = recipient["telegram_id"]
    profile_id = recipient["profile_id"]
    query = recipient["last_search_query"]
    filters = parse_filters_json(recipient.get("last_search_filters"))
    filters_payload = None if not filters or filters.is_empty() else filters.model_dump()

    try:
        result = await find_best_vacancies(
            profile_id=profile_id,
            search_text=query,
            per_page=2,
            filters=filters_payload,
        )
        vacancies = result.get("vacancies", [])
    except Exception:
        logger.exception("Digest search failed for %s", telegram_id)
        return

    if not vacancies:
        await mark_digest_sent(profile_id)
        return

    filters_note = ""
    if filters and not filters.is_empty():
        filters_note = "\n" + " | ".join(filters.summary_lines())

    await bot.send_message(
        telegram_id,
        f"<b>Утренний дайджест</b>\nЗапрос: «{query}»{filters_note}",
        parse_mode="HTML",
    )
    await asyncio.sleep(TELEGRAM_SEND_DELAY_SEC)

    for index, vacancy in enumerate(vacancies, start=1):
        text = format_vacancy_card(vacancy, index)
        for chunk in split_message(text):
            await bot.send_message(
                telegram_id,
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            await asyncio.sleep(TELEGRAM_SEND_DELAY_SEC)

    await mark_digest_sent(profile_id)


async def send_daily_digest(bot: Bot) -> None:
    try:
        recipients = await fetch_digest_recipients()
    except Exception:
        logger.exception("Failed to load digest recipients")
        return

    if not recipients:
        return

    logger.info("Digest: %s recipients, concurrency=%s", len(recipients), DIGEST_CONCURRENCY)
    semaphore = asyncio.Semaphore(DIGEST_CONCURRENCY)

    async def _run_one(recipient: dict) -> None:
        async with semaphore:
            try:
                await _send_digest_to_recipient(bot, recipient)
            except Exception:
                logger.exception("Digest failed for profile %s", recipient.get("profile_id"))

    await asyncio.gather(*[_run_one(r) for r in recipients])


async def digest_scheduler(bot: Bot, hour_msk: int = 9) -> None:
    last_run_date = None

    while True:
        now = datetime.now(MSK)
        if now.hour == hour_msk and last_run_date != now.date():
            logger.info("Running daily digest")
            await send_daily_digest(bot)
            last_run_date = now.date()

        await asyncio.sleep(60)
