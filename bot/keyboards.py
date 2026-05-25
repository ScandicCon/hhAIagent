from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

BTN_SEARCH = "🔍 Искать вакансии"
BTN_MY_RESUME = "📄 Моё резюме"
BTN_RESUME = "✏️ Обновить резюме"
BTN_RESUME_HISTORY = "📚 История резюме"
BTN_ANALYSES = "📋 Мои анализы"
BTN_HELP = "ℹ️ Помощь"
BTN_PLAN = "💳 Тариф"
BTN_DIGEST_ON = "🔔 Дайджест: вкл"
BTN_DIGEST_OFF = "🔕 Дайджест: выкл"
BTN_BUY_PRO = "💎 Купить Pro"
BTN_INVITE = "👥 Пригласить друга"
BTN_ADMIN = "⚙️ Админ"
# hh.ru отключил API соискателя (дек 2024) — кнопки убраны из меню
BTN_CONNECT_HH = "🔗 Подключить hh.ru"
BTN_SYNC_HH = "📥 Синхронизировать резюме"
BTN_AUTO_APPLY = "🚀 Автоотклик"


def main_menu_keyboard(telegram_id: int | None = None) -> ReplyKeyboardMarkup:
    from bot.config import ADMIN_TELEGRAM_IDS

    rows = [
        [KeyboardButton(text=BTN_SEARCH), KeyboardButton(text=BTN_MY_RESUME)],
        [KeyboardButton(text=BTN_RESUME), KeyboardButton(text=BTN_RESUME_HISTORY)],
        [KeyboardButton(text=BTN_ANALYSES), KeyboardButton(text=BTN_PLAN)],
        [KeyboardButton(text=BTN_BUY_PRO), KeyboardButton(text=BTN_INVITE)],
    ]

    if telegram_id is not None and telegram_id in ADMIN_TELEGRAM_IDS:
        rows.append([KeyboardButton(text=BTN_ADMIN)])

    rows.append([KeyboardButton(text=BTN_HELP)])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def vacancy_inline_keyboard(analysis_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подробнее",
                    callback_data=f"detail:{analysis_id}",
                ),
                InlineKeyboardButton(
                    text="Сопроводительное",
                    callback_data=f"cover:{analysis_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отклик на hh.ru",
                    callback_data=f"apply:{analysis_id}",
                ),
            ],
        ]
    )


def cover_letter_inline_keyboard(cover_letter_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Улучшить письмо",
                    callback_data=f"improve:{cover_letter_id}",
                ),
            ],
        ]
    )
