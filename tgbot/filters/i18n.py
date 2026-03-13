from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message


class I18nTextFilter(BoundFilter):
    key = 'i18n_text'

    def __init__(self, i18n_text: str):
        self.i18n_text = i18n_text

    async def check(self, message: Message) -> bool:
        _ = message.bot.get("i18n")  # Получаем объект i18n
        translated_text = _(self.i18n_text)  # Получаем переведённый текст
        return message.text == translated_text
