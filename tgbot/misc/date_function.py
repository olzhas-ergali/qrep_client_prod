import calendar
import datetime
import math
import typing


def f_get_month_and_year(
        months: int,
        year: int = None
) -> tuple:
    """Получаем год и айди месяца"""
    date_now = datetime.datetime.now()
    max_months = 12
    month = months
    if not year:
        year = date_now.year

    if months > max_months:
        month = months % max_months
        if not month:  # если будет ноль
            month = 12
        year_num = math.ceil(months / max_months)
        year += year_num - 1

    return year, month
