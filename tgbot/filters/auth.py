from tracemalloc import BaseFilter

from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from tgbot.models.database.users import User, Client


class AuthFilter(BoundFilter):
    key = 'is_auth'

    def __init__(self, is_auth):
        self.is_auth = is_auth

    async def check(self, *args) -> bool:
        data = ctx_data.get()
        user: User = data.get('user')
        is_active = False
        if isinstance(user, User):
            is_active = user.is_active

        if not is_active and not self.is_auth:
            return True

        if is_active and self.is_auth:
            return True
