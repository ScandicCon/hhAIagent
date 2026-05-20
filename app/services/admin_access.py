from app.config.settings import ADMIN_TELEGRAM_IDS
from app.models.profiles import Profile


def telegram_id_from_profile(profile: Profile) -> int | None:
    if not profile.name.startswith("tg_"):
        return None
    raw = profile.name.removeprefix("tg_")
    return int(raw) if raw.isdigit() else None


def is_admin_telegram_id(telegram_id: int) -> bool:
    return telegram_id in ADMIN_TELEGRAM_IDS


def is_admin_profile(profile: Profile) -> bool:
    telegram_id = telegram_id_from_profile(profile)
    return telegram_id is not None and is_admin_telegram_id(telegram_id)
