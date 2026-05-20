import logging

import requests

from app.config.core import HH_USER_AGENT

logger = logging.getLogger(__name__)

POPULAR_AREAS = {
    "moscow": (1, "Москва"),
    "spb": (2, "Санкт-Петербург"),
    "kazan": (88, "Казань"),
    "novosibirsk": (4, "Новосибирск"),
    "ekb": (3, "Екатеринбург"),
}


def resolve_area_by_name(text: str) -> tuple[int, str] | None:
    query = (text or "").strip()
    if not query:
        return None

    for area_id, name in POPULAR_AREAS.values():
        if query.lower() in (name.lower(), name.split()[0].lower()):
            return area_id, name

    try:
        response = requests.get(
            "https://api.hh.ru/suggests/areas",
            params={"text": query},
            headers={"User-Agent": HH_USER_AGENT},
            timeout=15,
        )
        if response.status_code != 200:
            logger.warning("HH areas suggest failed: %s", response.status_code)
            return None

        items = response.json().get("items") or []
        if not items:
            return None

        first = items[0]
        area_id = first.get("id")
        name = first.get("text") or query
        if area_id is None:
            return None
        return int(area_id), str(name)
    except requests.RequestException:
        logger.exception("HH areas suggest request failed")
        return None
