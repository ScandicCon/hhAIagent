import socket

from aiohttp import ClientTimeout
from aiogram.client.session.aiohttp import AiohttpSession

# VPS/Docker: медленный или нестабильный путь до api.telegram.org
TELEGRAM_HTTP_TIMEOUT = ClientTimeout(total=90, connect=45, sock_read=45)


class IPv4AiohttpSession(AiohttpSession):
    """Сессия Telegram API только через IPv4 (фикс timeout в Docker на VPS)."""

    def __init__(self, proxy: str | None = None, limit: int = 100) -> None:
        super().__init__(proxy=proxy, limit=limit, timeout=TELEGRAM_HTTP_TIMEOUT)
        self._connector_init["family"] = socket.AF_INET
