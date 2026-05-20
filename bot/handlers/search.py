from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from httpx import HTTPStatusError, RequestError

from app.services.hh_areas import POPULAR_AREAS, resolve_area_by_name
from app.services.search_filters import VacancySearchFilters
from bot.handlers.common import reply_backend_error
from bot.keyboards import main_menu_keyboard, vacancy_inline_keyboard
from bot.keyboards_search import SF_GO, search_filters_keyboard
from bot.services.backend_client import find_best_vacancies
from bot.states.user_states import UserFlow
from bot.utils.formatters import format_vacancy_card, split_message
from bot.utils.usage_text import format_usage


router = Router()


def _filters_from_state(data: dict) -> VacancySearchFilters:
    raw = data.get("search_filters") or {}
    return VacancySearchFilters.model_validate(raw)


def _filters_message(query: str, filters: VacancySearchFilters) -> str:
    summary = "\n".join(filters.summary_lines())
    return (
        f"<b>Запрос:</b> {query}\n\n"
        f"{summary}\n\n"
        "Выбери уровень, опыт, формат, город и зарплату "
        "(повторное нажатие снимает фильтр), затем «Искать»."
    )


async def _run_search(
    message: Message,
    state: FSMContext,
    *,
    search_text: str,
    filters: VacancySearchFilters,
) -> None:
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме через /start.")
        return

    filter_lines = filters.summary_lines()
    filter_hint = f"\n{' | '.join(filter_lines)}" if not filters.is_empty() else ""

    status_message = await message.answer(
        "Ищу вакансии и анализирую их через AI. Это может занять 1–3 минуты..."
        f"{filter_hint}"
    )

    try:
        result = await find_best_vacancies(
            profile_id=profile_id,
            search_text=search_text,
            per_page=7,
            filters=None if filters.is_empty() else filters.model_dump(),
        )
        vacancies = result.get("vacancies", [])
        usage = result.get("usage")
    except (HTTPStatusError, RequestError) as error:
        await status_message.delete()
        await reply_backend_error(message, error)
        return

    await status_message.delete()
    await state.set_state(None)

    if not vacancies:
        await message.answer(
            "Новых вакансий по этому запросу не нашёл — ты уже видел похожие.\n"
            "Попробуй другой запрос, смени фильтры "
            "(уровень, опыт, город, зарплата) или измени формулировку.",
            reply_markup=main_menu_keyboard(message.from_user.id),
        )
        return

    vacancies_map = {
        str(item["analysis_id"]): item for item in vacancies if item.get("analysis_id")
    }
    await state.update_data(last_vacancies=vacancies_map)

    filters_note = ""
    if not filters.is_empty():
        filters_note = f"\nФильтры: {' | '.join(filters.summary_lines())}"

    usage_line = f"\n\n{format_usage(usage)}" if usage else ""
    await message.answer(
        f"Нашёл {len(vacancies)} лучших вакансий по запросу «{search_text}»:{filters_note}",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )
    if usage_line:
        await message.answer(usage_line, parse_mode="HTML")

    for index, vacancy in enumerate(vacancies, start=1):
        text = format_vacancy_card(vacancy, index)
        analysis_id = vacancy.get("analysis_id")

        keyboard = (
            vacancy_inline_keyboard(analysis_id)
            if analysis_id is not None
            else None
        )

        for chunk_index, chunk in enumerate(split_message(text)):
            reply_markup = keyboard if chunk_index == 0 else None
            await message.answer(
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=reply_markup,
            )


@router.message(UserFlow.waiting_search)
async def search_query_handler(message: Message, state: FSMContext):
    search_text = (message.text or "").strip()
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not search_text:
        await message.answer("Введи текст запроса, например: Python backend")
        return

    if not profile_id:
        await state.set_state(UserFlow.waiting_resume)
        await message.answer("Сначала отправь резюме через /start.")
        return

    filters = VacancySearchFilters()
    await state.update_data(
        search_query=search_text,
        search_filters=filters.model_dump(),
    )
    await state.set_state(UserFlow.waiting_search_filters)
    await message.answer(
        _filters_message(search_text, filters),
        reply_markup=search_filters_keyboard(filters),
        parse_mode="HTML",
    )


@router.message(UserFlow.waiting_search_city)
async def search_city_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    search_text = (data.get("search_query") or "").strip()
    city_text = (message.text or "").strip()

    if not city_text:
        await message.answer("Напиши название города, например: Казань")
        return

    resolved = resolve_area_by_name(city_text)
    if not resolved:
        await message.answer(
            "Город не найден. Попробуй другое название или выбери из кнопок."
        )
        return

    area_id, area_name = resolved
    filters = _filters_from_state(data)
    filters.area_id = area_id
    filters.area_name = area_name
    await state.update_data(search_filters=filters.model_dump())
    await state.set_state(UserFlow.waiting_search_filters)
    await message.answer(
        _filters_message(search_text, filters),
        reply_markup=search_filters_keyboard(filters),
        parse_mode="HTML",
    )


@router.callback_query(UserFlow.waiting_search_filters, F.data.startswith("sf:"))
async def search_filters_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    search_text = (data.get("search_query") or "").strip()
    if not search_text:
        await callback.answer("Сначала введи запрос поиска", show_alert=True)
        await state.set_state(UserFlow.waiting_search)
        return

    filters = _filters_from_state(data)
    payload = callback.data or ""

    if payload == SF_GO:
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await _run_search(callback.message, state, search_text=search_text, filters=filters)
        return

    parts = payload.split(":")
    if len(parts) != 3:
        await callback.answer()
        return

    _, kind, value = parts
    if kind == "g":
        filters.grade = None if filters.grade == value else value
    elif kind == "e":
        filters.experience = None if filters.experience == value else value
    elif kind == "s":
        filters.schedule = None if filters.schedule == value else value
    elif kind == "a":
        if value == "custom":
            await state.set_state(UserFlow.waiting_search_city)
            await callback.answer()
            await callback.message.answer(
                "Напиши город одним сообщением, например: Новосибирск"
            )
            return
        if value == "none":
            filters.area_id = None
            filters.area_name = None
        elif value in POPULAR_AREAS:
            area_id, area_name = POPULAR_AREAS[value]
            if filters.area_id == area_id:
                filters.area_id = None
                filters.area_name = None
            else:
                filters.area_id = area_id
                filters.area_name = area_name
    elif kind == "pay":
        if value == "only":
            filters.only_with_salary = not filters.only_with_salary
            if filters.only_with_salary:
                filters.salary_from = None
        else:
            try:
                amount = int(value)
            except ValueError:
                await callback.answer()
                return
            filters.salary_from = None if filters.salary_from == amount else amount
            if filters.salary_from:
                filters.only_with_salary = False
    else:
        await callback.answer()
        return

    await state.update_data(search_filters=filters.model_dump())
    await callback.message.edit_text(
        _filters_message(search_text, filters),
        reply_markup=search_filters_keyboard(filters),
        parse_mode="HTML",
    )
    await callback.answer()
