import typing
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, extract, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, joinedload

# Добавили импорт Client
from tgbot.models.database.users import RegTemp, ClientsApp, Client
from tgbot.keyboards.auth import get_continue_btn
from tgbot.keyboards.client.faq import get_answer
from tgbot.models.database.loyalty import BonusExpirationNotifications, ClientBonusPoints
from tgbot.services.notification_service import NotificationService, UserIdentificationService
from tgbot.config import Config


async def push_client_authorization(
        pool: sessionmaker,
        config: Config,
        _: typing.Callable,
):
    logging.info("TASK: Уведомление о незавершенной регистрации (строгая проверка)")
    session: AsyncSession = pool()
    notification_service = NotificationService(config)
    
    # Ищем тех, кто "висит" больше 3 минут
    now = datetime.now() - timedelta(minutes=3)
    
    response = await session.execute(select(RegTemp).where(
        (RegTemp.state_time < now) & (RegTemp.state != 'start'))
    )
    users: typing.Optional[typing.List[RegTemp], None] = response.scalars().all()

    for u in users:
        # Получаем данные из JSON (чтобы достать телефон и флаг отправки)
        current_data = dict(u.state_data) if u.state_data else {}
        phone_in_temp = current_data.get('phone')

        # --- ЭТАП 1: ЖЕСТКАЯ ПРОВЕРКА НА УЖЕ ЗАРЕГИСТРИРОВАННЫХ ---
        
        # 1.1 Проверка по Telegram ID
        exist_client_by_id = await session.get(Client, u.telegram_id)
        if exist_client_by_id and exist_client_by_id.is_active:
            logging.info(f"User {u.telegram_id} уже есть в базе (по ID). Удаляем мусор из RegTemp.")
            await session.delete(u)
            continue

        # 1.2 Проверка по Телефону (если он был введен)
        if phone_in_temp:
            # Используем существующий метод модели Client
            exist_client_by_phone = await Client.get_client_by_phone(session, phone_in_temp)
            if exist_client_by_phone and exist_client_by_phone.is_active:
                logging.info(f"User {u.telegram_id} (phone: {phone_in_temp}) уже есть в базе. Удаляем мусор из RegTemp.")
                await session.delete(u)
                continue

        # --- ЭТАП 2: ОТПРАВКА УВЕДОМЛЕНИЯ (ТОЛЬКО 1 РАЗ) ---

        # Если мы уже отправляли уведомление этому юзеру — пропускаем его
        if current_data.get('is_notified') is True:
            continue

        try:
            from tgbot.services.notification_service import UserInfo, UserType
            user_info = UserInfo(user_type=UserType.CLIENT)
            
            # Отправляем сообщение
            success = await notification_service.send_notification(
                user_info=user_info,
                telegram_id=u.telegram_id,
                message="Вы не закончили регистрацию",
                reply_markup=get_continue_btn(_)
            )
            
            # Если отправилось успешно — ставим метку
            if success:
                current_data['is_notified'] = True
                u.state_data = current_data
                session.add(u)
                logging.info(f"Напоминание отправлено {u.telegram_id}. Ставим флаг и забиваем.")
            
        except Exception as e:
            logging.error(f"Error sending auth push to {u.telegram_id}: {e}")

    await session.commit()
    await session.close()


async def push_client_answer_operator(
        pool: sessionmaker,
        config: Config,
        _: typing.Callable,
):
    logging.info("TASK STARTED: push_client_answer_operator - Уведомление для клиентов по оценке работе оператора")
    session: AsyncSession = pool()
    notification_service = NotificationService(config)

    now = datetime.now()
    logging.info(f" Searching for ClientsApp records with waiting_time < {now}")
    
    response = await session.execute(select(ClientsApp).where(
        (ClientsApp.waiting_time < now) & (ClientsApp.is_push == False))
    )
    users: typing.Optional[typing.List, None] = response.scalars().all()
    
    logging.info(f" Found {len(users)} ClientsApp records to process")
    
    for u in users:
        try:
            logging.info(f" Processing user: telegram_id={u.telegram_id}, phone={u.phone_number}, waiting_time={u.waiting_time}")
            
            # Определяем тип пользователя по номеру телефона если он есть
            if u.phone_number:
                identifier = UserIdentificationService(session)
                user_info = await identifier.identify_user(u.phone_number)
                logging.info(f" User type identified: {user_info.user_type.value} for phone {u.phone_number}")
            else:
                # Если номера нет, считаем клиентом
                logging.info(f" No phone number for telegram_id {u.telegram_id}, defaulting to CLIENT type")
                from tgbot.services.notification_service import UserInfo, UserType
                user_info = UserInfo(user_type=UserType.CLIENT)
            
            logging.info(f" Sending notification to telegram_id {u.telegram_id} via {user_info.user_type.value} bot")
            
            # Используем правильную функцию для отправки уведомления об оценке покупки
            success = await notification_service.send_purchase_review_notification(
                session=session,
                phone_number=u.phone_number or "unknown",
                telegram_id=u.telegram_id,
                purchase_id=None
            )
            u.is_push = True
            session.add(u)
            logging.info(f" Successfully processed user {u.telegram_id}")
            
        except Exception as e:
            logging.error(f" Failed to send operator answer notification to {u.telegram_id}: {e}")
            
    await session.commit()
    logging.info(f" TASK COMPLETED: push_client_answer_operator - Processed {len(users)} records")
    await session.close()


async def push_client_about_bonus(
        pool: sessionmaker,
        config: Config,
):
    logging.info("Уведомление для клиентов по сгоранию бонусов")
    session: AsyncSession = pool()
    notification_service = NotificationService(config)
    
    date_now = datetime.now().date()
    bonuses = await ClientBonusPoints.get_bonuses(session)
    if bonuses:
        texts = {
            30: "Через 30 дней сгорят ваши бонусы. Используйте их, пока не поздно.",
            7: "Вы можете потратить бонусы до истечения срока действия. Осталось 7 дней.",
            1: "Завтра ваши бонусы станут недоступны. Успейте их использовать сегодня!"
        }
        logging.info(f"Date Now: {date_now}")
        for bonus in bonuses:
            try:
                logging.info(f"Expiration Date {bonus.expiration_date.date()}")
                logging.info(f"Days -> {(bonus.expiration_date.date() - date_now).days}")
                
                # Бонусы обычно для клиентов, но проверим если есть связанная информация
                from tgbot.services.notification_service import UserInfo, UserType
                user_info = UserInfo(user_type=UserType.CLIENT)
                
                message = texts.get((bonus.expiration_date.date() - date_now).days)
                if message:
                    await notification_service.send_notification(
                        user_info=user_info,
                        telegram_id=bonus.client_id,
                        message=message
                    )
            except Exception as ex:
                logging.error(f"Failed to send bonus notification to {bonus.client_id}: {ex}")
    await session.close()