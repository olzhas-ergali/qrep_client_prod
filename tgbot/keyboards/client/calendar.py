import calendar
import datetime
import typing

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from aiogram import types

from tgbot.misc.date_function import f_get_month_and_year
from tgbot.data import dictionaries
from tgbot.keyboards.query_cb import CalendarCallback


async def make_ikb_calendar(
    month_num: int,
    year_num: int = None,
    locale: str = 'rus'  # ИЗМЕНЕНИЕ: Добавили параметр языка
):
    year_num, month = f_get_month_and_year(month_num, year_num)

    # ИЗМЕНЕНИЕ: Логика выбора словарей в зависимости от языка
    if locale == 'kaz':
        months_dict = dictionaries.calendar.months_name_kk
        days_list = dictionaries.calendar.day_of_weeks_kk
    else: # По умолчанию используем русский
        months_dict = dictionaries.calendar.months_name_ru
        days_list = dictionaries.calendar.day_of_weeks_ru

    ikb_calendar = InlineKeyboardMarkup(7)
    date_now = datetime.datetime.now()
    ignore_callback = "x"
    
    prev_month = InlineKeyboardButton(text="<<",
                                      callback_data=CalendarCallback.new(id=f"month_prev,{month - 1},{year_num}",
                                                                         action='calendar'))
    next_month = InlineKeyboardButton(text=">>",
                                      callback_data=CalendarCallback.new(id=f"month_next,{month + 1},{year_num}",
                                                                         action='calendar'))
    if date_now.month - 1 == month and date_now.year == year_num:
        next_month.callback_data = ignore_callback
        next_month.text = "x"

    # ИЗМЕНЕНИЕ: Используем выбранный словарь для названия месяца
    month_name = InlineKeyboardButton(text=f"{months_dict.get(month)} {year_num}",
                                      callback_data=CalendarCallback.new(id='month', action="x"))
    
    ikb_calendar.row(prev_month, month_name, next_month)
    ikb_calendar.row()

    # ИЗМЕНЕНИЕ: Используем выбранный список для названий дней недели
    for day_name in days_list:
        ikb_calendar.insert(
            InlineKeyboardButton(day_name, callback_data=ignore_callback)
        )

    month_calendar = calendar.monthcalendar(year=year_num, month=month)
    for week in month_calendar:
        ikb_calendar.row()
        for day in week:
            if day == 0:
                ikb_calendar.insert(InlineKeyboardButton(" ", callback_data="x"))
                continue
            
            callback_id = f"date,{str(day).zfill(2)},{str(month).zfill(2)},{str(year_num)}"
            ikb_calendar.insert(
                InlineKeyboardButton(str(day),
                                     callback_data=CalendarCallback.new(
                                         id=callback_id,
                                         action='mast')
                                     )
            )

    return ikb_calendar


async def make_year_ikb(year):
    ikb_calendar = InlineKeyboardMarkup(3)
    date_now = datetime.datetime.now()
    qr = InlineKeyboardButton(
        text="QR",
        callback_data="x"
    )
    ignore_callback = "x"
    ignore_text = "x"
    prev_year = InlineKeyboardButton(text="<<",
                                     callback_data=CalendarCallback.new(id=f"year_prev, {year - 9}",
                                                                        action='year'))
    next_year = InlineKeyboardButton(text=">>",
                                     callback_data=CalendarCallback.new(id=f"year_next, {year + 9}",
                                                                        action='year'))
    if date_now.year == year:
        next_year.callback_data = ignore_callback
        next_year.text = ignore_text
    ikb_calendar.row(prev_year, qr, next_year)
    for i in range(8, -1, -1):
        btn = InlineKeyboardButton(
            text=year - i,
            callback_data=CalendarCallback.new(id=f"{year - i}",
                                               action="birth_year")
        )
        ikb_calendar.insert(btn)

    return ikb_calendar
