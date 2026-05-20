from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from httpx import HTTPStatusError, RequestError

from bot.handlers.common import reply_backend_error
from bot.keyboards import BTN_ANALYSES, vacancy_inline_keyboard
from bot.services.backend_client import get_analyses
from bot.utils.formatters import format_vacancy_card, split_message


router = Router()


async def send_analyses_list(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    profile_id = data.get("profile_id")

    if not profile_id:
        await message.answer("Сначала отправь резюме через /start.")
        return

    try:
        analyses = await get_analyses(profile_id)
    except HTTPStatusError as error:
        if error.response.status_code == 404:
            await message.answer("Пока нет сохранённых анализов. Сначала выполни поиск.")
            return
        await reply_backend_error(message, error)
        return
    except RequestError as error:
        await reply_backend_error(message, error)
        return

    analyses = sorted(analyses, key=lambda item: item["match_score"], reverse=True)

    vacancies_map = {}
    for analysis in analyses[:10]:
        analysis_id = analysis.get("id")
        if analysis_id is not None:
            vacancies_map[str(analysis_id)] = {
                "analysis_id": analysis_id,
                "title": analysis["title"],
                "company": analysis["company"],
                "url": analysis["url"],
                "match_score": analysis["match_score"],
                "should_apply": analysis["should_apply"],
                "summary": analysis.get("summary"),
                "pros": analysis.get("pros", []),
                "cons": analysis.get("cons", []),
                "cached": True,
            }

    await state.update_data(last_vacancies=vacancies_map)

    await message.answer(
        f"Сохранённые анализы ({len(analyses)}).\n"
        "Нажми «Сопроводительное» под вакансией для генерации письма."
    )

    for index, analysis in enumerate(analyses[:10], start=1):
        vacancy = {
            "title": analysis["title"],
            "company": analysis["company"],
            "url": analysis["url"],
            "match_score": analysis["match_score"],
            "should_apply": analysis["should_apply"],
            "summary": analysis.get("summary"),
            "cached": True,
        }
        text = format_vacancy_card(vacancy, index)
        analysis_id = analysis.get("id")
        keyboard = (
            vacancy_inline_keyboard(analysis_id)
            if analysis_id is not None
            else None
        )

        for chunk_index, chunk in enumerate(split_message(text)):
            await message.answer(
                chunk,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=keyboard if chunk_index == 0 else None,
            )


@router.message(Command("analyses"))
@router.message(F.text == BTN_ANALYSES)
async def analyses_handler(message: Message, state: FSMContext):
    await send_analyses_list(message, state)
