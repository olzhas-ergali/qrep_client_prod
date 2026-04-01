# qrep_client/tgbot/services/notification_service.py

import logging
from enum import Enum
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import User, Client
from tgbot.config import Config
from tgbot.misc.parse import parse_phone
# Импортируем генератор клавиатуры
from tgbot.keyboards.client.client import get_review_keyboard 

logger = logging.getLogger(__name__)


class UserType(Enum):
    STAFF = "staff"
    CLIENT = "client"
    UNKNOWN = "unknown"


@dataclass
class UserInfo:
    user_type: UserType
    telegram_id: Optional[int] = None
    phone_number: Optional[str] = None
    name: Optional[str] = None
    user_id: Optional[int] = None
    locale: str = 'rus'  # Добавили поле для языка, по умолчанию 'rus'


class UserIdentificationService:
    """Сервис для определения типа пользователя по номеру телефона"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def identify_user(self, phone_number: str) -> UserInfo:
        """
        Определяет тип пользователя.
        ПРИОРИТЕТ ИЗМЕНЕН: Сначала ищем Клиента, так как это уведомления о покупках.
        1. Client table by phone
        2. Staff table by phone
        3. Unknown user
        """
        logger.info(f"Identifying user for phone: {phone_number}")
        
        normalized_phone = parse_phone(phone_number)
        
        # 1. СНАЧАЛА ищем в таблице КЛИЕНТОВ
        client_user = await Client.get_client_by_phone(self.session, normalized_phone)
        if client_user:
            logger.info(f"✅ Found CLIENT user: {client_user.name} (ID: {client_user.id}, Local: {client_user.local})")
            return UserInfo(
                user_type=UserType.CLIENT,
                phone_number=phone_number,
                name=client_user.name,
                user_id=client_user.id,
                locale=client_user.local or 'rus'
            )
        
        # 2. Если не нашли, ищем в таблице СОТРУДНИКОВ
        staff_user = await User.get_by_phone(self.session, normalized_phone)
        if staff_user:
            display_name = staff_user.login_tg or f"User_{staff_user.id}" 
            logger.info(f"Found STAFF user (fallback): {display_name} (ID: {staff_user.id}, Local: {staff_user.local})")
            return UserInfo(
                user_type=UserType.STAFF,
                phone_number=phone_number,
                name=display_name,
                user_id=staff_user.id,
                locale=staff_user.local or 'rus'
            )
        
        # 3. Пользователь не найден
        logger.warning(f"User NOT FOUND for phone: {phone_number} - will use UNKNOWN type")
        return UserInfo(
            user_type=UserType.UNKNOWN,
            phone_number=phone_number,
            locale='rus'
        )

class NotificationService:
    """Сервис для отправки уведомлений в соответствующие боты"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def _get_bot_token(self, user_type: UserType) -> str:
        token = ""
        if user_type == UserType.STAFF:
            token = self.config.tg_bot.staff_token
            logger.info(f"Using STAFF bot token for user_type={user_type.value}")
        elif user_type == UserType.CLIENT:
            token = self.config.tg_bot.client_token
            logger.info(f"Using CLIENT bot token for user_type={user_type.value}")
        else:
            # Для UNKNOWN используем client_token, так как purchase-notification
            # предназначен для клиентов, а не для сотрудников
            token = self.config.tg_bot.client_token
            logger.info(f"Using CLIENT bot token (fallback) for user_type={user_type.value}")

        return token

    def _get_fallback_bot_token(self, user_type: UserType) -> Optional[str]:
        """Возвращает запасной токен, если первичный бот не видит chat_id."""
        if user_type == UserType.STAFF:
            return self.config.tg_bot.client_token
        if user_type == UserType.CLIENT:
            return self.config.tg_bot.staff_token
        return None
    
    async def send_notification(
        self,
        user_info: UserInfo,
        telegram_id: int,
        message: str,
        reply_markup: Optional[Union[Dict, Any]] = None, # Добавили поддержку кнопок
        parse_mode: str = "HTML",
        allow_cross_bot_fallback: bool = True
    ) -> bool:
        """Отправляет уведомление в соответствующий бот"""
        
        payload = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": parse_mode
        }

        # Если передана клавиатура, добавляем её в запрос
        if reply_markup:
            # Если это объект клавиатуры aiogram, преобразуем в dict
            if hasattr(reply_markup, 'to_python'):
                 payload["reply_markup"] = reply_markup.to_python()
            else:
                 payload["reply_markup"] = reply_markup
        
        async def _send_with_token(bot_token: str) -> tuple[bool, int, str]:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    body = await response.text()
                    return response.status == 200, response.status, body

        primary_token = self._get_bot_token(user_info.user_type)
        try:
            ok, status, body = await _send_with_token(primary_token)
            if ok:
                logger.info(
                    f"Notification sent successfully to {user_info.user_type.value} "
                    f"user {telegram_id} (phone: {user_info.phone_number})"
                )
                return True

            error_text = body.lower()
            need_fallback = (
                status == 400 and ("chat not found" in error_text or "bot was blocked by the user" in error_text)
            )

            if need_fallback and allow_cross_bot_fallback:
                fallback_token = self._get_fallback_bot_token(user_info.user_type)
                if fallback_token and fallback_token != primary_token:
                    logger.warning(
                        f"Primary bot token failed for {user_info.user_type.value} user {telegram_id}, "
                        "trying fallback token"
                    )
                    ok2, status2, body2 = await _send_with_token(fallback_token)
                    if ok2:
                        logger.info(
                            f"Notification delivered with fallback token for {user_info.user_type.value} "
                            f"user {telegram_id} (phone: {user_info.phone_number})"
                        )
                        return True
                    logger.error(
                        f"Fallback token also failed for {user_info.user_type.value} "
                        f"user {telegram_id}: {status2} - {body2}"
                    )
                    return False

            logger.error(
                f"Failed to send notification to {user_info.user_type.value} "
                f"user {telegram_id}: {status} - {body}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Exception while sending notification to {user_info.user_type.value} "
                f"user {telegram_id}: {str(e)}"
            )
            return False

    # Хелпер для перевода (эмуляция gettext)
    def _get_translator(self, locale: str):
        # Простой словарь для текстов кнопок и сообщений уведомления
        translations = {
            'kaz': {
                'Отлично': 'Өте жақсы',
                'Хорошо': 'Жақсы',
                'Удовлетворительно': 'Қанағаттанарлық',
                'Плохо': 'Нашар',
                'Очень плохо': 'Өте нашар',
                'Greeting_Client': 'Сәлеметсіз бе, {name}!',
                'Greeting_Staff': 'Сәлеметсіз бе, {name}!',
                'Body': 'Бізді таңдағаныңыз үшін рахмет! Қызмет көрсету мен тауарлардың сапасын бағалауыңызды сұраймыз.',
                'ID': '\n\nСатып алу ID: {id}'
            },
            'rus': {
                'Отлично': 'Отлично',
                'Хорошо': 'Хорошо',
                'Удовлетворительно': 'Удовлетворительно',
                'Плохо': 'Плохо',
                'Очень плохо': 'Очень плохо',
                'Greeting_Client': 'Здравствуйте, {name}!',
                'Greeting_Staff': 'Здравствуйте, {name}!',
                'Body': 'Благодарим за покупку! Пожалуйста, оцените качество обслуживания и товаров.',
                'ID': '\n\nID покупки: {id}'
            }
        }

        target_dict = translations.get(locale, translations['rus'])

        def translator(text: str, locale: str = None) -> str:
            return target_dict.get(text, text)
        
        return translator
    
    async def send_purchase_review_notification(
        self,
        session: AsyncSession,
        phone_number: str,
        telegram_id: int,
        purchase_id: Optional[str] = None
    ) -> bool:
        """Отправляет уведомление об оценке покупки с кнопками и на нужном языке"""
        
        # 1. Определяем пользователя и его ЯЗЫК
        identifier = UserIdentificationService(session)
        user_info = await identifier.identify_user(phone_number)
        
        # 2. Получаем переводчик для этого языка
        _ = self._get_translator(user_info.locale)
        
        # 3. Формируем сообщение по ТЗ (рус.: Здравствуйте, {ФИО}! Благодарим за покупку! ... / каз.: Сәлеметсіз бе, {ФИО}! Бізді таңдағаныңыз үшін рахмет! ...)
        name_to_use = (user_info.name or "").strip()
        
        if user_info.user_type == UserType.STAFF:
            greeting = _('Greeting_Staff').format(name=name_to_use or 'қызметкер/сотрудник')
        else:
            greeting = _('Greeting_Client').format(name=name_to_use or 'клиент')

        message = f"{greeting}\n\n{_('Body')}"
        
        if purchase_id:
            id_text = _('ID').format(id=purchase_id)
            message += id_text

        # 4. Генерируем клавиатуру с переведенными кнопками
        keyboard = await get_review_keyboard(_)
        
        # 5. Отправляем с клавиатурой
        return await self.send_notification(
            user_info=user_info, 
            telegram_id=telegram_id, 
            message=message,
            reply_markup=keyboard, # Передаем кнопки!
            # Для review-кнопок нужен именно client bot:
            # callback_query обрабатывается его polling-процессом.
            allow_cross_bot_fallback=False
        )