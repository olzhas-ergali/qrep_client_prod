import logging

from aiogram.types.message import Message


async def remove(
        message: Message,
        step: int
):
    try:
        await message.bot.delete_message(message.from_user.id, message.message_id - step)
    except:
        pass


async def delete_message(
        message: Message
):
    try:
        await message.delete()
    except Exception as e:
        logging.exception(e)
