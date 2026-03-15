import datetime
import typing

from aiogram.types.message import Message, ContentType
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.dispatcher.filters.state import State

from tgbot.models.database.users import RegTemp, Client, User
from tgbot.handlers.client import auth as client_auth, main as client_main
from tgbot.keyboards.auth import get_auth_btns, get_local_btns


async def first_message_handler(
        message: Message,
):
    # НЕ используем переводы в первом сообщении, так как язык еще не выбран
    # Показываем оба языка, чтобы пользователь мог выбрать
    await message.answer(
'''Сәлем! Сізді Qazaq Republic және QR+ бонустық бағдарламасы бойынша жеке көмекшіңіз қарсы алады.
Мен сізге кэшбэк пен басқа да мүмкіндіктер туралы ақпаратты жылдам әрі оңай алуға көмектесемін.

Сәлем! Вас приветствует Qazaq Republic и ваш персональный помощник по бонусной программе QR+.
Я помогу вам быстро получить информацию о кэшбэке и многом другом.'''
    )
    await message.answer(
        text="Тілді таңдаңыз:\nВыберите язык:\n\nҚазақ тілі\nРусский язык",
        reply_markup=get_local_btns()
    )


# async def welcome_message_handler(
#         query: CallbackQuery,
#         callback_data: dict,
#         session: AsyncSession,
#         user: Client
# ):
#     user.local = callback_data.get('lang')
#     await user.save(session)
#     _ = query.bot.get('i18n')
#     text = _('''Сәлем! Сізді Qazaq Republic және QR+ бонустық бағдарламасы бойынша жеке көмекшіңіз қарсы алады.
# Мен сізге кэшбэк пен басқа да мүмкіндіктер туралы ақпаратты жылдам әрі оңай алуға көмектесемін.
#
# Сәлем! Вас приветствует Qazaq Republic и ваш персональный помощник по бонусной программе QR+.
# Я помогу вам быстро получить информацию о кэшбэке и многом другом.''', locale=user.local)
#     btns = get_auth_btns(_, local=user.local)
#     await query.message.edit_text(
#         text=text,
#         reply_markup=btns
#     )


async def authorization_handler(
        callback: CallbackQuery,
        callback_data: dict,
        state: FSMContext,
        user: Client,
        reg: RegTemp,
        session: AsyncSession
):
    await callback.message.delete()
    
    # ИСПРАВЛЕНИЕ: Сохраняем выбранный язык
    selected_lang = callback_data.get('lang')
    
    # ПРИОРИТЕТ 1: Устанавливаем временный язык в сессии
    await state.update_data(session_locale=selected_lang)
    
    # ПРИОРИТЕТ 2: Сохраняем в БД для будущих сессий
    user.local = selected_lang
    await user.save(session=session)
    
    # Получаем локализованную функцию с выбранным языком
    _ = callback.bot.get('i18n')
    
    if isinstance(user, Client) and user.is_active:
        return await client_main.start_handler(
            message=callback.message,
            user=user,
            state=state,
            session=session
        )

    await client_auth.auth_phone_handler(callback.message, state, reg, user, session)


async def continue_auth_handler(
        callback: CallbackQuery,
        callback_data: dict,
        user: Client,
        state: FSMContext,
        reg: RegTemp,
        session: AsyncSession
):
    #await state.set_state(reg.state)
    #methods = {
    #    "AuthClientState:waiting_phone": client_auth.auth_phone_handler,
    #    "AuthClientState:waiting_name": client_auth.auth_fio_handler,
    #    "AuthClientState:waiting_birthday_date": client_auth.get_years_handler,
    #    "AuthClientState:waiting_gender": client_auth.auth_gender_handler,
    #}

    if reg.state == "AuthClientState:waiting_phone":
        await client_auth.auth_phone_handler(
            message=callback.message,
            state=state,
            reg=reg,
            session=session,
            user=user
        )
    elif reg.state == "AuthClientState:waiting_name":
        await client_auth.auth_fio_handler(
            message=callback.message,
            user=user,
            state=state,
            reg=reg,
            session=session
        )
    elif reg.state == "AuthClientState:waiting_birthday_date":
        await client_auth.get_years_handler(
            message=callback.message,
            user=user,
            session=session,
            state=state,
            reg=reg
        )
    elif reg.state == "AuthClientState:waiting_gender":
        await client_auth.auth_gender_handler(
            query=callback,
            user=user,
            session=session,
            state=state,
            callback_data=callback_data,
            reg=reg
        )
    elif reg.state == "AuthClientState:waiting_email":
        await client_auth.auth_email_handler(
            query=callback,
            user=user,
            session=session,
            state=state,
            callback_data=callback_data,
            reg=reg
        )
