import typing

from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from tgbot.models.database.users import User


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin: typing.Optional[bool] = None):
        self.is_admin = is_admin

    async def check(self, *args):
        data = ctx_data.get()
        user: User = data.get('user')
        if not self.is_admin and not user.is_admin:
            return True

        if self.is_admin and user.is_admin:
            return True
