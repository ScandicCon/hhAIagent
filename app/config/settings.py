import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "9090"))


def _normalize_database_url(url: str) -> str:
    url = url.strip().strip('"').strip("'")
    if url.startswith("sqlite:///./"):
        relative = url.removeprefix("sqlite:///./")
        absolute = (PROJECT_ROOT / relative).resolve()
        return f"sqlite:///{absolute.as_posix()}"
    return url


_db_default = f"sqlite:///{(PROJECT_ROOT / 'hh_agent.db').resolve().as_posix()}"
DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL") or _db_default)

BACKEND_URL = (
    os.getenv("BACKEND_URL") or f"http://{API_HOST}:{API_PORT}"
).strip().rstrip("/")

ADMIN_API_KEY = (os.getenv("ADMIN_API_KEY") or "").strip()

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

DIGEST_HOUR_MSK = int(os.getenv("DIGEST_HOUR_MSK", "9"))

OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()

_default_models = "google/gemini-2.0-flash-001,openai/gpt-4o-mini,meta-llama/llama-3.1-8b-instruct"
_models_raw = os.getenv("OPENROUTER_MODELS", _default_models)
OPENROUTER_MODELS = [m.strip() for m in _models_raw.split(",") if m.strip()]

OPENROUTER_RETRY_ATTEMPTS = int(os.getenv("OPENROUTER_RETRY_ATTEMPTS", "3"))
OPENROUTER_RETRY_DELAY_SEC = float(os.getenv("OPENROUTER_RETRY_DELAY_SEC", "2"))
AI_REQUEST_DELAY_SEC = float(os.getenv("AI_REQUEST_DELAY_SEC", "1"))

VACANCY_RESULTS_COUNT = int(os.getenv("VACANCY_RESULTS_COUNT", "7"))
VACANCY_HH_PAGE_SIZE = int(os.getenv("VACANCY_HH_PAGE_SIZE", "20"))
VACANCY_MAX_HH_PAGES = int(os.getenv("VACANCY_MAX_HH_PAGES", "5"))

PRO_PRICE_RUB = int(os.getenv("PRO_PRICE_RUB", "490"))
PRO_CONTACT = (os.getenv("PRO_CONTACT") or "@your_username").strip()

_promo_raw = os.getenv("PROMO_CODES", "LAUNCH2026:pro")
PUBLIC_URL = (os.getenv("PUBLIC_URL") or BACKEND_URL).strip().rstrip("/")
BOT_USERNAME = (os.getenv("BOT_USERNAME") or "HHSearchVacanciesBot").strip().lstrip("@")

YOOKASSA_SHOP_ID = (os.getenv("YOOKASSA_SHOP_ID") or "").strip()
YOOKASSA_SECRET_KEY = (os.getenv("YOOKASSA_SECRET_KEY") or "").strip()
YOOKASSA_ENABLED = bool(YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY)

REFERRAL_BONUS_SEARCHES = int(os.getenv("REFERRAL_BONUS_SEARCHES", "3"))

HH_REDIRECT_URI = (
    os.getenv("HH_REDIRECT_URI") or "http://localhost:8000/auth/callback"
).strip()

AUTO_APPLY_MIN_MATCH = int(os.getenv("AUTO_APPLY_MIN_MATCH", "70"))
AUTO_APPLY_DAILY_LIMIT = int(os.getenv("AUTO_APPLY_DAILY_LIMIT", "10"))

PROMO_CODES: dict[str, str] = {}
for item in _promo_raw.split(","):
    item = item.strip()
    if ":" in item:
        code, plan = item.split(":", 1)
        PROMO_CODES[code.strip().upper()] = plan.strip().lower()
