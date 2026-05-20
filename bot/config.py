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

_admin_ids_raw = os.getenv("ADMIN_TELEGRAM_IDS", "")
ADMIN_TELEGRAM_IDS = {
    int(value.strip())
    for value in _admin_ids_raw.split(",")
    if value.strip().isdigit()
}

ADMIN_API_KEY = (os.getenv("ADMIN_API_KEY") or "").strip()

PRO_PRICE_RUB = int(os.getenv("PRO_PRICE_RUB", "490"))
PRO_CONTACT = (os.getenv("PRO_CONTACT") or "@your_username").strip()
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "HHSearchVacanciesBot").strip().lstrip("@")
YOOKASSA_ENABLED = bool(
    (os.getenv("YOOKASSA_SHOP_ID") or "").strip()
    and (os.getenv("YOOKASSA_SECRET_KEY") or "").strip()
)
