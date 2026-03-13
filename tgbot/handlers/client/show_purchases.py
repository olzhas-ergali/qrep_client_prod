import os
import segno
import datetime
import logging

from aiogram.types.message import Message, ContentTypes
from aiogram.types.callback_query import CallbackQuery
from aiogram.types import ParseMode
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import User
from tgbot.keyboards.client.client import period_btns
from tgbot.misc.delete import remove
from tgbot.misc.client.show_purchases import show_purchases
from tgbot.handlers.client.main import main_handler
from tgbot.misc.state_helpers import clear_state_but_preserve_locale

logger = logging.getLogger(__name__)


async def purchases_handler(
        callback: CallbackQuery,
        state: FSMContext
):
    logger.info(f"🛒 PURCHASES_HANDLER: Пользователь {callback.from_user.id} выбрал раздел покупок")
    await clear_state_but_preserve_locale(state)
    
    _ = callback.bot.get('i18n')
    logger.info(f"🛒 PURCHASES_HANDLER: Функция перевода получена: {type(_)}")
    
    try:
        translated_text = _("Выберите:")
        logger.info(f"🛒 PURCHASES_HANDLER: Перевод успешен: '{translated_text}'")
        
        await callback.message.edit_text(
            text=translated_text,
            reply_markup=await period_btns(_)
        )
        logger.info(f"🛒 PURCHASES_HANDLER: Сообщение успешно отправлено")
    except Exception as e:
        logger.error(f"🛒 PURCHASES_HANDLER: Ошибка: {e}")
        # Fallback на русский
        await callback.message.edit_text(
            text="Выберите:",
            reply_markup=await period_btns(_)
        )


async def all_purchases_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        callback_data: dict,
        state: FSMContext
):
    logger.info(f"🛒 ALL_PURCHASES_HANDLER: Пользователь {callback.from_user.id} запросил все покупки")
    
    _ = callback.bot.get('i18n')
    logger.info(f"🛒 ALL_PURCHASES_HANDLER: Функция перевода получена: {type(_)}")
    
    try:
        await callback.message.delete()
        logger.info(f"🛒 ALL_PURCHASES_HANDLER: Сообщение удалено")
    except Exception as e:
        logger.warning(f"🛒 ALL_PURCHASES_HANDLER: Не удалось удалить сообщение: {e}")
    
    texts = await show_purchases(
        session=session,
        user_id=callback.from_user.id
    )
    
    if texts:
        logger.info(f"🛒 ALL_PURCHASES_HANDLER: Получено {len(texts)} текстов для отправки")
        for i, text in enumerate(texts):
            try:
                logger.info(f"🛒 ALL_PURCHASES_HANDLER: Отправляем текст {i+1}/{len(texts)} (длина: {len(text)})")
                await callback.message.answer(
                    text=text,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"🛒 ALL_PURCHASES_HANDLER: Текст {i+1} успешно отправлен")
            except Exception as e:
                logger.error(f"🛒 ALL_PURCHASES_HANDLER: Ошибка отправки текста {i+1}: {e}")
    else:
        logger.info(f"🛒 ALL_PURCHASES_HANDLER: Покупки не найдены, отправляем сообщение об отсутствии")
        try:
            no_purchases_text = _("Вы пока не совершали покупки в нашем магазине.\nПредлагаем вам просмотреть ассортимент на сайте - qazaqrepublic.com")
            await callback.message.answer(text=no_purchases_text)
            logger.info(f"🛒 ALL_PURCHASES_HANDLER: Сообщение об отсутствии покупок отправлено")
        except Exception as e:
            logger.error(f"🛒 ALL_PURCHASES_HANDLER: Ошибка отправки сообщения об отсутствии: {e}")
            await callback.message.answer(
                text="Вы пока не совершали покупки в нашем магазине.\nПредлагаем вам просмотреть ассортимент на сайте - qazaqrepublic.com"
            )
    
    logger.info(f"🛒 ALL_PURCHASES_HANDLER: Переходим к главному меню")
    await main_handler(callback)


async def purchases_by_date_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        callback_data: dict,
        state: FSMContext
):
    logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Пользователь {callback.from_user.id} запросил покупки по дате")
    
    _ = callback.bot.get('i18n')
    logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Функция перевода получена: {type(_)}")
    
    try:
        await callback.message.delete()
        logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Сообщение удалено")
    except Exception as e:
        logger.warning(f"🛒 PURCHASES_BY_DATE_HANDLER: Не удалось удалить сообщение: {e}")
    
    texts = await show_purchases(
        session=session,
        date=datetime.datetime.now(),
        user_id=callback.from_user.id
    )
    
    if texts:
        logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Получено {len(texts)} текстов для отправки")
        for i, text in enumerate(texts):
            try:
                logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Отправляем текст {i+1}/{len(texts)} (длина: {len(text)})")
                await callback.message.answer(
                    text=text,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Текст {i+1} успешно отправлен")
            except Exception as e:
                logger.error(f"🛒 PURCHASES_BY_DATE_HANDLER: Ошибка отправки текста {i+1}: {e}")
    else:
        logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Покупки за месяц не найдены")
        try:
            no_purchases_text = _("Вы пока не совершали покупки за этот месяц.\nПредлагаем вам просмотреть ассортимент на сайте - qazaqrepublic.com")
            await callback.message.answer(text=no_purchases_text)
            logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Сообщение об отсутствии покупок за месяц отправлено")
        except Exception as e:
            logger.error(f"🛒 PURCHASES_BY_DATE_HANDLER: Ошибка отправки сообщения об отсутствии: {e}")
            await callback.message.answer(
                text="Вы пока не совершали покупки за этот месяц.\nПредлагаем вам просмотреть ассортимент на сайте - qazaqrepublic.com"
            )
    
    logger.info(f"🛒 PURCHASES_BY_DATE_HANDLER: Переходим к главному меню")
    await main_handler(callback)

