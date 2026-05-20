import html
import re


def escape_html(text: str) -> str:
    return html.escape(text or "")


def _vacancy_meta_lines(vacancy: dict) -> list[str]:
    lines = []
    if vacancy.get("experience"):
        lines.append(f"Опыт: {escape_html(vacancy['experience'])}")
    if vacancy.get("schedule"):
        lines.append(f"График: {escape_html(vacancy['schedule'])}")
    if vacancy.get("employment"):
        lines.append(f"Занятость: {escape_html(vacancy['employment'])}")
    if vacancy.get("area"):
        lines.append(f"Город: {escape_html(vacancy['area'])}")
    if vacancy.get("salary"):
        lines.append(f"Зарплата: {escape_html(vacancy['salary'])}")
    return lines


def format_vacancy_card(vacancy: dict, index: int) -> str:
    apply_label = "да" if vacancy.get("should_apply") else "нет"
    cached = " (кэш)" if vacancy.get("cached") else ""

    lines = [
        f"<b>{index}. {escape_html(vacancy['title'])}</b>",
        f"Компания: {escape_html(vacancy['company'])}",
        *_vacancy_meta_lines(vacancy),
        f"Match: {vacancy['match_score']}%{cached}",
        f"Откликаться: {apply_label}",
        f'<a href="{vacancy["url"]}">Открыть на hh.ru</a>',
    ]

    summary = vacancy.get("summary")
    if summary:
        lines.append(f"\n{escape_html(summary[:600])}")

    return "\n".join(lines)


def format_vacancy_detail(vacancy: dict) -> str:
    pros = vacancy.get("pros") or []
    cons = vacancy.get("cons") or []

    pros_text = "\n".join(f"• {escape_html(item)}" for item in pros[:5]) or "—"
    cons_text = "\n".join(f"• {escape_html(item)}" for item in cons[:5]) or "—"

    meta = "\n".join(_vacancy_meta_lines(vacancy))
    meta_block = f"{meta}\n" if meta else ""

    return (
        f"<b>{escape_html(vacancy['title'])}</b>\n"
        f"Компания: {escape_html(vacancy['company'])}\n"
        f"{meta_block}"
        f"Match: {vacancy['match_score']}%\n"
        f"Откликаться: {'да' if vacancy.get('should_apply') else 'нет'}\n"
        f'<a href="{vacancy["url"]}">Открыть на hh.ru</a>\n\n'
        f"<b>Кратко</b>\n{escape_html(vacancy.get('summary') or '—')}\n\n"
        f"<b>Плюсы</b>\n{pros_text}\n\n"
        f"<b>Минусы</b>\n{cons_text}"
    )


def split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    for paragraph in re.split(r"\n{2,}", text):
        block = paragraph + "\n\n"
        if len(block) > limit:
            for line in paragraph.split("\n"):
                piece = line + "\n"
                if len(current) + len(piece) > limit:
                    if current:
                        chunks.append(current.rstrip())
                    current = piece
                else:
                    current += piece
            continue

        if len(current) + len(block) > limit:
            chunks.append(current.rstrip())
            current = block
        else:
            current += block

    if current.strip():
        chunks.append(current.rstrip())

    return chunks or [text[:limit]]
