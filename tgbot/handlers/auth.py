from aiogram.types.message import Message
from aiogram.dispatcher.filters.state import State

from tgbot.keyboards.client.client import phone_number_btn


async def phone_handler(
        m: Message,
        state: State,
        text: str = None
):
    _ = m.bot.get("i18n")
    if not text:
        text = _("Поделитесь номером телефона для авторизации")

    await m.answer(
        text=text,
        reply_markup=phone_number_btn(_)
    )

    await state.set()
