from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State


class NotificationState(StatesGroup):
    waiting_review = State()


class FaqState(StatesGroup):
    start = State()
    waiting_time = State()
    waiting_operator = State()


class AuthClientState(StatesGroup):
    waiting_phone = State()
    waiting_name = State()
    waiting_birthday_date = State()
    waiting_gender = State()
    waiting_email = State()
