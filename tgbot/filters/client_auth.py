from tracemalloc import BaseFilter

from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from tgbot.models.database.users import Client


class ClientAuthFilter(BoundFilter):
    key = 'is_client_auth'

    def __init__(self, is_client_auth):
        self.is_client_auth = is_client_auth

    async def check(self, *args) -> bool:
        data = ctx_data.get()
        client: Client = data.get('user')
        if not client.is_active and not self.is_client_auth:
            return True

        if client.is_active and self.is_client_auth:
            return True

