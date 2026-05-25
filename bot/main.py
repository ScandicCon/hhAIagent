import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from app.config.settings import DIGEST_HOUR_MSK
from bot.config import BOT_TOKEN, TELEGRAM_PROXY
from bot.handlers import (
    admin,
    analyses,
    callbacks,
    fallback,
    fsm_commands,
    hh,
    invite,
    menu,
    promo,
    resume,
    resume_view,
    search,
    start,
    subscription,
)
from bot.services.digest import digest_scheduler
from bot.telegram_session import IPv4AiohttpSession


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    session = IPv4AiohttpSession(proxy=TELEGRAM_PROXY)
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        me = await bot.get_me()
        logging.info("Bot connected: @%s", me.username)
    except TelegramNetworkError as error:
        await session.close()
        logging.error(
            "Cannot reach Telegram API (api.telegram.org). "
            "Or set TELEGRAM_PROXY in .env. Error: %s",
            error,
        )
        raise SystemExit(1) from error
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(fsm_commands.router)
    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(promo.router)
    dp.include_router(hh.router)
    dp.include_router(invite.router)
    dp.include_router(analyses.router)
    dp.include_router(menu.router)
    dp.include_router(resume_view.router)
    dp.include_router(resume.router)
    dp.include_router(search.router)
    dp.include_router(callbacks.router)
    dp.include_router(fallback.router)

    asyncio.create_task(digest_scheduler(bot, hour_msk=DIGEST_HOUR_MSK))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
