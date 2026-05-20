from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.hh_areas import POPULAR_AREAS
from app.services.search_filters import (
    EXPERIENCE_LABELS,
    GRADE_LABELS,
    SALARY_LABELS,
    SCHEDULE_LABELS,
    VacancySearchFilters,
)

SF_GO = "sf:go"
SF_CITY_CUSTOM = "sf:a:custom"


def _toggle_label(label: str, selected: bool) -> str:
    return f"✓ {label}" if selected else label


def search_filters_keyboard(filters: VacancySearchFilters) -> InlineKeyboardMarkup:
    def grade_btn(key: str):
        return InlineKeyboardButton(
            text=_toggle_label(GRADE_LABELS[key], filters.grade == key),
            callback_data=f"sf:g:{key}",
        )

    def exp_btn(key: str):
        return InlineKeyboardButton(
            text=_toggle_label(EXPERIENCE_LABELS[key], filters.experience == key),
            callback_data=f"sf:e:{key}",
        )

    def sched_btn(key: str):
        return InlineKeyboardButton(
            text=_toggle_label(SCHEDULE_LABELS[key], filters.schedule == key),
            callback_data=f"sf:s:{key}",
        )

    def area_btn(key: str, label: str):
        area_id, area_name = POPULAR_AREAS[key]
        selected = filters.area_id == area_id
        return InlineKeyboardButton(
            text=_toggle_label(label, selected),
            callback_data=f"sf:a:{key}",
        )

    def salary_btn(amount: int):
        return InlineKeyboardButton(
            text=_toggle_label(SALARY_LABELS[amount], filters.salary_from == amount),
            callback_data=f"sf:pay:{amount}",
        )

    popular_ids = {area_id for area_id, _ in POPULAR_AREAS.values()}
    area_custom_selected = (
        filters.area_id is not None and filters.area_id not in popular_ids
    )
    area_label = filters.area_name if area_custom_selected else "Другой город"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [grade_btn("junior"), grade_btn("middle"), grade_btn("senior")],
            [grade_btn("intern")],
            [
                exp_btn("noExperience"),
                exp_btn("between1And3"),
            ],
            [
                exp_btn("between3And6"),
                exp_btn("moreThan6"),
            ],
            [sched_btn("remote"), sched_btn("office")],
            [
                area_btn("moscow", "Москва"),
                area_btn("spb", "СПб"),
            ],
            [
                area_btn("kazan", "Казань"),
                InlineKeyboardButton(
                    text=_toggle_label(area_label[:20], area_custom_selected),
                    callback_data=SF_CITY_CUSTOM,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Без города" if filters.area_id else "Сбросить город",
                    callback_data="sf:a:none",
                ),
            ],
            [salary_btn(100000), salary_btn(150000)],
            [salary_btn(200000), salary_btn(250000)],
            [
                InlineKeyboardButton(
                    text=_toggle_label(
                        "Только с зарплатой",
                        filters.only_with_salary and not filters.salary_from,
                    ),
                    callback_data="sf:pay:only",
                ),
            ],
            [
                InlineKeyboardButton(text="🔍 Искать", callback_data=SF_GO),
            ],
        ]
    )
