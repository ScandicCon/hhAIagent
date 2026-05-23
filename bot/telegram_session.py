import socket

from aiogram.client.session.aiohttp import AiohttpSession


class IPv4AiohttpSession(AiohttpSession):
    """Сессия Telegram API только через IPv4 (фикс timeout в Docker на VPS)."""

    def __init__(self, proxy: str | None = None, limit: int = 100) -> None:
        super().__init__(proxy=proxy, limit=limit)
        self._connector_init["family"] = socket.AF_INET
