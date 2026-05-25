"""Команды и кнопки меню во время FSM (поиск, резюме) — иначе текст уходит в search_handler."""

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import (
    BTN_ANALYSES,
    BTN_BUY_PRO,
    BTN_HELP,
    BTN_INVITE,
    BTN_MY_RESUME,
    BTN_PLAN,
    BTN_RESUME,
    BTN_RESUME_HISTORY,
    BTN_SEARCH,
    main_menu_keyboard,
)
from bot.services.checkout import send_pro_checkout
from bot.states.user_states import UserFlow


router = Router()


async def _leave_flow(state: FSMContext) -> None:
    await state.set_state(None)


@router.message(StateFilter(UserFlow), Command("cancel"))
@router.message(StateFilter(UserFlow), F.text.casefold() == "отмена")
async def cancel_during_flow(message: Message, state: FSMContext) -> None:
    await _leave_flow(state)
    await message.answer(
        "Действие отменено. Выбери пункт в меню или команду (/search, /buy, /plan).",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(StateFilter(UserFlow), Command("buy"))
@router.message(StateFilter(UserFlow), F.text == BTN_BUY_PRO)
async def buy_during_flow(message: Message, state: FSMContext) -> None:
    await _leave_flow(state)
    await send_pro_checkout(message, state)


@router.message(StateFilter(UserFlow), Command("plan"))
@router.message(StateFilter(UserFlow), F.text == BTN_PLAN)
async def plan_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.subscription import show_plan

    await _leave_flow(state)
    await show_plan(message, state)


@router.message(StateFilter(UserFlow), Command("start"))
async def start_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.start import start_handler

    await start_handler(message, state)


@router.message(StateFilter(UserFlow), Command("help"))
@router.message(StateFilter(UserFlow), F.text == BTN_HELP)
async def help_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.start import help_handler

    await _leave_flow(state)
    await help_handler(message)


@router.message(StateFilter(UserFlow), Command("search"))
@router.message(StateFilter(UserFlow), F.text == BTN_SEARCH)
async def search_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.start import search_command

    await search_command(message, state)


@router.message(StateFilter(UserFlow), Command("resume"))
@router.message(StateFilter(UserFlow), F.text == BTN_RESUME)
async def resume_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.start import resume_command

    await resume_command(message, state)


@router.message(StateFilter(UserFlow), Command("invite"))
@router.message(StateFilter(UserFlow), F.text == BTN_INVITE)
async def invite_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.invite import invite_handler

    await _leave_flow(state)
    await invite_handler(message, state)


@router.message(StateFilter(UserFlow), Command("tariffs"))
async def tariffs_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.promo import tariffs_command

    await _leave_flow(state)
    await tariffs_command(message)


@router.message(StateFilter(UserFlow), Command("promo"))
async def promo_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.promo import promo_command

    await _leave_flow(state)
    await promo_command(message, state)


@router.message(StateFilter(UserFlow), Command("myresume"))
@router.message(StateFilter(UserFlow), F.text == BTN_MY_RESUME)
async def myresume_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.resume_view import show_my_resume

    await _leave_flow(state)
    await show_my_resume(message, state)


@router.message(StateFilter(UserFlow), Command("resumehistory"))
@router.message(StateFilter(UserFlow), F.text == BTN_RESUME_HISTORY)
async def resume_history_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.resume_view import show_resume_history

    await _leave_flow(state)
    await show_resume_history(message, state)


@router.message(StateFilter(UserFlow), Command("analyses"))
@router.message(StateFilter(UserFlow), F.text == BTN_ANALYSES)
async def analyses_during_flow(message: Message, state: FSMContext) -> None:
    from bot.handlers.analyses import send_analyses_list

    await _leave_flow(state)
    await send_analyses_list(message, state)
