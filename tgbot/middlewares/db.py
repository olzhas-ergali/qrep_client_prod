from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.types import Poll, PollAnswer, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from tgbot.models.database.users import Client, RegTemp


class DbMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    async def pre_process(self, obj, data, *args):
        pool = obj.bot.get('pool')
        session: AsyncSession = pool()
        reg = await session.get(RegTemp, obj.from_user.id)
        client = await session.get(Client, obj.from_user.id)
        if not isinstance(obj, (Message, CallbackQuery)):
            data['session'] = session
            return
        if not client:
            client = Client(
                id=obj.from_user.id,
                fullname=obj.from_user.full_name
            )
            session.add(client)

        if not reg and (not client or not client.phone_number):
            reg = RegTemp()
            reg.telegram_id = obj.from_user.id
            reg.state = "start"
            session.add(reg)
        await session.commit()
            # staff = User(
            #    id=obj.from_user.id,
            #    fullname=obj.from_user.full_name
            # )
            # session.add(staff)
            # await session.commit()

        data['session'] = session
        data['reg'] = reg
        client.activity = "telegram"
        data['user'] = client

    async def post_process(self, obj, data, *args):
        if session := data.get("session"):
            await session.close()
            data.pop('session')
