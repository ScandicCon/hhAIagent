from aiogram.fsm.state import State, StatesGroup


class UserFlow(StatesGroup):
    waiting_resume = State()
    waiting_search = State()
    waiting_search_filters = State()
    waiting_search_city = State()
    waiting_improve_instruction = State()
