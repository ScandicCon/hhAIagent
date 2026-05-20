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


def upgrade_message() -> str:
    return (
        "Лимит Free исчерпан.\n\n"
        "<b>Pro</b>: 100 поисков и 50 писем в неделю + дайджест.\n"
        "Нажми «Купить Pro» или /invite — пригласи друга за бонусные поиски."
    )
