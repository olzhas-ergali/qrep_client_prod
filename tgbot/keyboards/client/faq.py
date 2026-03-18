import typing

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.keyboards.query_cb import (
    FaqCallback,
    OperatorCallback,
    AnswerCallback,
    LocalCallback,
    BonusHistoryCallback)
from tgbot.data.faq_new import faq_lvls


async def get_faq_btns(
        current_lvl: str,
        i18n_func: typing.Callable[[str], str],
        locale: str = None
):
    markup = InlineKeyboardMarkup()
    n = len(faq_lvls.get(current_lvl))
    for i in range(n):
        faq_lvls.get(current_lvl)[i].get('callback')
        original_text = faq_lvls.get(current_lvl)[i].get('text')
        translated_text = i18n_func(original_text, locale=locale)
        markup.add(
            InlineKeyboardButton(
                text=translated_text,
                callback_data=FaqCallback.new(
                    chapter=i + 1,
                    lvl=faq_lvls.get(current_lvl)[i].get('callback'),
                    action=faq_lvls.get(current_lvl)[i].get('action', 'faq')
                )
            )
        )
    markup.add(
        InlineKeyboardButton(
            text=i18n_func("Сменить язык", locale=locale),
            callback_data=LocalCallback.new(
                lang="-",
                action="change_local"
            )
        )
    )
    return markup


async def get_times(
        i18n_func: typing.Callable[[str], str]
):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        *[
            #Дәл қазір
            InlineKeyboardButton(
                text=i18n_func("Сейчас"),
                callback_data=OperatorCallback.new(
                    time="0",
                    action='application'
                )
            ),
            #30 минуттан кейін
            InlineKeyboardButton(
                text=i18n_func("Через 30 минут"),
                callback_data=OperatorCallback.new(
                    time="30",
                    action='application'
                )
            ),
            #1 сағаттан кейін
            InlineKeyboardButton(
                text=i18n_func("Через 1 час"),
                callback_data=OperatorCallback.new(
                    time="60",
                    action='application'
                )
            ),
            #2 сағаттан кейін
            InlineKeyboardButton(
                text=i18n_func("Через 2 час"),
                callback_data=OperatorCallback.new(
                    time="120",
                    action='application'
                )
            )
        ]
    )

    return markup


def get_answer(
        i18n_func: typing.Callable[[str], str]
):
    return InlineKeyboardMarkup().add(
        *[
            InlineKeyboardButton(
                text=i18n_func("Да"),
                callback_data=AnswerCallback.new(
                    ans="yes",
                    action='user_answer'
                )
            ),
            InlineKeyboardButton(
                text=i18n_func("Подключить оператора"),
                callback_data=AnswerCallback.new(
                    ans="no",
                    action='user_answer'
                )
            )
        ]
    )


def get_grade_btns():
    return InlineKeyboardMarkup(row_width=1).add(
        *[
            InlineKeyboardButton(
                text="1",
                callback_data=AnswerCallback.new(
                    ans="1",
                    id='620',
                    action='user_grade'
                )
            ),
            InlineKeyboardButton(
                text="2",
                callback_data=AnswerCallback.new(
                    ans="2",
                    id='621',
                    action='user_grade'
                )
            ),
            InlineKeyboardButton(
                text="3",
                callback_data=AnswerCallback.new(
                    ans="3",
                    id='622',
                    action='user_grade'
                )
            ),
            InlineKeyboardButton(
                text="4",
                callback_data=AnswerCallback.new(
                    ans="4",
                    id='623',
                    action='user_grade'
                )
            ),
            InlineKeyboardButton(
                text="5",
                callback_data=AnswerCallback.new(
                    ans="5",
                    id='624',
                    action='user_grade'
                )
            )
        ]
    )


def get_bonus_history_btns(
        current_page: int,
        total_pages: int,
        i18n_func: typing.Callable[[str], str],
        locale: str = None
) -> InlineKeyboardMarkup:
    """Создаёт кнопки пагинации для истории бонусов."""
    markup = InlineKeyboardMarkup(row_width=3)

    buttons = []

    # Кнопка "Назад" (если не первая страница)
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=BonusHistoryCallback.new(
                    page=current_page - 1,
                    action='page'
                )
            )
        )

    # Счётчик страниц
    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data=BonusHistoryCallback.new(
                page=current_page,
                action='current'
            )
        )
    )

    # Кнопка "Вперёд" (если не последняя страница)
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=BonusHistoryCallback.new(
                    page=current_page + 1,
                    action='page'
                )
            )
        )

    if buttons:
        markup.row(*buttons)

    # Кнопка "Главное меню"
    markup.add(
        InlineKeyboardButton(
            text=i18n_func("Главное меню", locale=locale),
            callback_data=FaqCallback.new(
                chapter=0,
                lvl='main',
                action='faq'
            )
        )
    )

    return markup


