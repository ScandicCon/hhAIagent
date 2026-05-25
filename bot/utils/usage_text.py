def format_usage(usage: dict) -> str:
    bonus = usage.get("bonus_searches", 0)
    bonus_line = f"\nБонус за друзей: +{bonus} поисков" if bonus else ""
    return (
        f"Тариф: <b>{usage.get('plan_label', usage.get('plan', '—'))}</b>\n"
        f"Поиски: {usage.get('searches_used', 0)}/{usage.get('searches_per_week', 0)} "
        f"(осталось {usage.get('searches_left', 0)}){bonus_line}\n"
        f"Письма: {usage.get('cover_letters_used', 0)}/"
        f"{usage.get('cover_letters_per_week', 0)} "
        f"(осталось {usage.get('cover_letters_left', 0)})"
    )


def upgrade_hint(usage: dict | None = None) -> str:
    if not usage:
        return (
            "<b>Pro</b>: 100 поисков и 50 писем в неделю + дайджест.\n"
            "Кнопка «Купить Pro» или /invite."
        )

    if usage.get("plan") == "pro":
        return "Тариф Pro активен — приятного поиска."

    searches_left = usage.get("searches_left", 0)
    letters_left = usage.get("cover_letters_left", 0)

    if searches_left > 0 or letters_left > 0:
        return (
            "Можешь искать вакансии и писать письма в рамках лимита Free.\n"
            "Больше возможностей — тариф <b>Pro</b> (кнопка «Купить Pro»)."
        )

    return (
        "Лимит Free на этой неделе исчерпан.\n\n"
        "<b>Pro</b>: 100 поисков и 50 писем + дайджест.\n"
        "«Купить Pro» или /invite — бонусные поиски."
    )


def upgrade_message() -> str:
    """Совместимость со старыми вызовами."""
    return upgrade_hint(None)
