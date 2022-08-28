from aiogram.dispatcher.filters.state import StatesGroup, State


class UserData(StatesGroup):
    Faculty = State()
    Form = State()
    Step = State()
    Course = State()
    Group = State()
