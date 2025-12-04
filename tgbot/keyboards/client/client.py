import typing

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from tgbot.keyboards.query_cb import GenderCallback, UniversalCallback, LocalCallback
from tgbot.keyboards import generate
from tgbot.keyboards.query_cb import ChoiceCallback
from tgbot.keyboards.query_cb import ReviewCallback

def phone_number_btn(
        _
):
    markup = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    markup.add(
        KeyboardButton(_("Поделиться телефоном"), request_contact=True)
    )
    return markup


async def main_btns(
        _: typing.Callable[[str], str]
):
    markup = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True
    )
    btns = [_('Мои бонусы'),
            _('Мой QR'),
            _('Мои покупки')]
            #'FAQ']
    for btn in btns:
        markup.add(btn)

    return markup


async def get_genders_ikb(
        _: typing.Callable[[str], str]
):
    markup = InlineKeyboardMarkup(1)

    man = InlineKeyboardButton(text=_("Муж"),
                               callback_data=GenderCallback.new(gender='M',
                                                                action='gender'))

    women = InlineKeyboardButton(text=_("Жен"),
                                 callback_data=GenderCallback.new(gender='F',
                                                                  action='gender'))

    markup.add(man)
    markup.add(women)
    return markup


async def get_universal_btn(
        text: str,
        action: str
):
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton(
        text=text,
        callback_data=UniversalCallback.new(
            action=action
        )
    )
    markup.add(btn)
    return markup


async def period_btns(
        _: typing.Callable[[str], str]
):
    markup = InlineKeyboardMarkup()
    btns = {
        _("За весь период"): ChoiceCallback.new(
            choice="by_all",
            action="client_purchases"
        ),
        _("За текущий месяц"): ChoiceCallback.new(
            choice="by_month",
            action="client_purchases"
        )
    }

    return generate.GenerateMarkupButtons(
        laylout=1,
        markup=markup,
        keyboards=[
            InlineKeyboardButton(
                text=t,
                callback_data=c
            ) for t, c in btns.items()
        ]
    ).get()


async def change_locale(
        action: str = "change_local"
):
    markup = InlineKeyboardMarkup()
    btns = {
        "Қазақ тілі": LocalCallback.new(
            lang="kaz",
            action=action
        ),
        "Русский": LocalCallback.new(
            lang="rus",
            action=action
        )
    }

    return generate.GenerateMarkupButtons(
        laylout=1,
        markup=markup,
        keyboards=[
            InlineKeyboardButton(
                text=t,
                callback_data=c
            ) for t, c in btns.items()
        ]
    ).get()


async def get_review_keyboard(_: typing.Callable) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для оценки качества сервиса.
    """
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Тексты кнопок, как в старом проекте
    buttons = {
        5: _('Отлично'),
        4: _('Хорошо'),
        3: _('Удовлетворительно'),
        2: _('Плохо'),
        1: _('Очень плохо'),
    }

    for grade, text in buttons.items():
        markup.add(
            InlineKeyboardButton(
                text=text,
                callback_data=ReviewCallback.new(
                    grade=grade,
                    action='review'
                )
            )
        )
    
    return markup