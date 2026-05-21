import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

API_HOST = os.getenv("API_HOST", "127.0.0.1").strip()
API_PORT = int(os.getenv("API_PORT", "9090"))

BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
TELEGRAM_PROXY = (os.getenv("TELEGRAM_PROXY") or "").strip() or None

_env_backend = (os.getenv("BACKEND_URL") or "").strip().rstrip("/")
_expected = f"http://{API_HOST}:{API_PORT}"
BACKEND_URL = _env_backend or _expected

def _parse_admin_telegram_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        token = part.strip().strip('"').strip("'")
        if token.isdigit():
            ids.add(int(token))
    return ids


ADMIN_TELEGRAM_IDS = _parse_admin_telegram_ids(
    os.getenv("ADMIN_TELEGRAM_IDS", ""),
)

ADMIN_API_KEY = (os.getenv("ADMIN_API_KEY") or "").strip()

PRO_PRICE_RUB = int(os.getenv("PRO_PRICE_RUB", "490"))
PRO_CONTACT = (os.getenv("PRO_CONTACT") or "@your_username").strip()
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "HHSearchVacanciesBot").strip().lstrip("@")
YOOKASSA_ENABLED = bool(
    (os.getenv("YOOKASSA_SHOP_ID") or "").strip()
    and (os.getenv("YOOKASSA_SECRET_KEY") or "").strip()
)
