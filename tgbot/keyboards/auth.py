from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from tgbot.keyboards.query_cb import AuthCallback, ContinueCallback, LocalCallback


def get_auth_btns(
        _,
        local: str
):
    """Только клиентская авторизация — кнопка «сотрудник» в клиентском боте не показываем."""
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton(
        text=_("Авторизоваться как клиент", locale=local),
        callback_data=AuthCallback.new(
            id='client',
            action='auth'
        )
    )
    markup.add(btn1)
    return markup


def get_continue_btn(
        _
):
    btn_continue = InlineKeyboardButton(
        text=_("Продолжить регистрацию"),
        callback_data=ContinueCallback.new(
            action='continue'
        )
    )
    return InlineKeyboardMarkup().add(btn_continue)


def staff_auth_btns(
        _
):
    btn_back = InlineKeyboardButton(
        text=_("Назад"),
        callback_data="back"
    )
    btn_repeat = InlineKeyboardButton(
        text=_("Повторно написать ИИН"),
        callback_data="repeat"
    )

    return InlineKeyboardMarkup(row_width=1).add(btn_repeat, btn_back)


def get_local_btns():
    btn_kaz = InlineKeyboardButton(
        text="Қазақ тілі",
        callback_data=LocalCallback.new(
            lang="kaz",
            action='local'
        )
    )
    btn_rus = InlineKeyboardButton(
        text="Русский язык",
        callback_data=LocalCallback.new(
            lang="rus",
            action='local'
        )
    )

    return InlineKeyboardMarkup(row_width=1).add(btn_kaz, btn_rus)