from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_menu_keyboard


router = Router()


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "Напиши /start, чтобы начать работу с ботом.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        "Используй кнопки меню или команды /search, /resume, /help.",
        reply_markup=main_menu_keyboard(),
    )
