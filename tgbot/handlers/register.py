from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from tgbot.handlers import client
from tgbot.handlers import authorization
from tgbot.misc.states.client import AuthClientState
from tgbot.keyboards import query_cb


def register_staff(dp: Dispatcher):
    # Один вход на /start для неавторизованных, чтобы исключить дубли приветствия.
    dp.register_message_handler(
        authorization.first_message_handler,
        commands=['start'],
        is_client_auth=False,
        state="*"
    )

    # dp.register_callback_query_handler(
    #     authorization.welcome_message_handler,
    #     query_cb.LocalCallback.filter(action='local'),
    #     is_client_auth=False,
    #     state="*"
    # )

    dp.register_callback_query_handler(
        authorization.authorization_handler,
        query_cb.LocalCallback.filter(action='local'),
        is_client_auth=False,
        state="*"
    )

    dp.register_callback_query_handler(
        authorization.continue_auth_handler,
        query_cb.ContinueCallback.filter(action='continue'),
        is_client_auth=False,
        state="*"
    )

    register_client(dp)


def register_client(dp):
    dp.register_message_handler(
        client.auth.auth_fio_handler,
        content_types=types.ContentType.CONTACT,
        state=AuthClientState.waiting_phone
    )

    dp.register_callback_query_handler(
        client.auth.get_fio_handler,
        query_cb.UniversalCallback.filter(action='confirm'),
        state=AuthClientState.waiting_phone
    )

    dp.register_message_handler(
        client.auth.get_years_handler,
        state=AuthClientState.waiting_name
    )

    dp.register_callback_query_handler(
        client.auth.auth_get_other_year_handler,
        query_cb.CalendarCallback.filter(action='year'),
        state=AuthClientState.waiting_birthday_date
    )

    dp.register_callback_query_handler(
        client.auth.auth_birthday_date_handler,
        query_cb.CalendarCallback.filter(action='birth_year'),
        state=AuthClientState.waiting_birthday_date
    )

    dp.register_callback_query_handler(
        client.auth.auth_get_other_month_handler,
        query_cb.CalendarCallback.filter(action='calendar'),
        state=AuthClientState.waiting_birthday_date
    )

    dp.register_callback_query_handler(
        client.auth.auth_gender_handler,
        query_cb.CalendarCallback.filter(action='mast'),
        state=AuthClientState.waiting_birthday_date
    )

    dp.register_callback_query_handler(
        client.auth.auth_email_handler,
        query_cb.GenderCallback.filter(action='gender'),
        state=AuthClientState.waiting_gender
    )

    dp.register_callback_query_handler(
        client.auth.auth_client_handler,
        query_cb.UniversalCallback.filter(action='email'),
        state=AuthClientState.waiting_email
    )

    dp.register_message_handler(
        client.auth.auth_client_handler,
        state=AuthClientState.waiting_email
    )
