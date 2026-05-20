import json
import logging
import threading
import time
from pathlib import Path

import requests
from fastapi import HTTPException

from app.config.core import HH_CLIENT_ID, HH_CLIENT_SECRET, HH_USER_AGENT

logger = logging.getLogger(__name__)

_token_lock = threading.Lock()

# Shared across uvicorn workers / CLI inside one container (Docker volume /app/data).
_token_cache_path = Path(__file__).resolve().parents[2] / "data" / "hh_token.json"
if Path("/app/data").exists():
    _token_cache_path = Path("/app/data/hh_token.json")

_memory_cache: dict = {
    "access_token": None,
    "expires_at": 0,
}


def _load_cache() -> dict:
    if _memory_cache.get("access_token") and _memory_cache["expires_at"] > int(time.time()):
        return _memory_cache

    if not _token_cache_path.exists():
        return _memory_cache

    try:
        data = json.loads(_token_cache_path.read_text(encoding="utf-8"))
        _memory_cache.update(data)
    except (json.JSONDecodeError, OSError) as error:
        logger.warning("Could not read HH token cache: %s", error)

    return _memory_cache


def _save_cache(access_token: str, expires_at: int) -> None:
    _memory_cache["access_token"] = access_token
    _memory_cache["expires_at"] = expires_at

    try:
        _token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        _token_cache_path.write_text(
            json.dumps(_memory_cache),
            encoding="utf-8",
        )
    except OSError as error:
        logger.warning("Could not write HH token cache: %s", error)


def get_hh_app_token(*, force_refresh: bool = False, _wait_retry: bool = True) -> str:
    """
    Application access token for hh.ru API.
    Uses file cache to avoid "token refresh too early" when multiple workers start.
    """
    if not HH_CLIENT_ID or not HH_CLIENT_SECRET:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "hh_config",
                "message": "HH_CLIENT_ID / HH_CLIENT_SECRET не заданы в .env",
            },
        )

    now = int(time.time())
    cache = _load_cache()

    if (
        not force_refresh
        and cache.get("access_token")
        and int(cache.get("expires_at") or 0) > now
    ):
        return cache["access_token"]

    with _token_lock:
        cache = _load_cache()
        if (
            not force_refresh
            and cache.get("access_token")
            and int(cache.get("expires_at") or 0) > now
        ):
            return cache["access_token"]

        stale_token = cache.get("access_token")

        try:
            response = requests.post(
                "https://api.hh.ru/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": HH_CLIENT_ID,
                    "client_secret": HH_CLIENT_SECRET,
                },
                headers={"User-Agent": HH_USER_AGENT},
                timeout=30,
            )
        except requests.exceptions.Timeout as error:
            if stale_token:
                logger.warning("HH token timeout, using stale token")
                return stale_token
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "hh_timeout",
                    "message": "hh.ru не ответил при получении токена.",
                },
            ) from error

        if response.status_code == 403 and "refresh too early" in response.text:
            if stale_token:
                logger.warning("HH token refresh too early, using cached token")
                return stale_token
            if _wait_retry:
                logger.warning("HH token rate limit, waiting 45s and retrying once")
                time.sleep(45)
                return get_hh_app_token(
                    force_refresh=force_refresh,
                    _wait_retry=False,
                )
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "hh_token_rate_limit",
                    "message": "hh.ru: слишком частый запрос токена. Подожди 1–2 минуты.",
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "hh_token",
                    "message": "Не удалось получить токен hh.ru",
                    "hh_status": response.status_code,
                    "hh_response": response.text[:300],
                },
            )

        data = response.json()
        access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        # Refresh only in the last 5 minutes of lifetime.
        expires_at = now + max(expires_in - 300, 60)

        _save_cache(access_token, expires_at)
        logger.info("HH token refreshed, valid until %s", expires_at)
        return access_token
