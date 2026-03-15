import asyncio
import json
import logging
import asyncpg
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from tgbot.config import Config
from tgbot.services.notification_service import NotificationService, UserInfo, UserType
from tgbot.models.database.users import Client

logger = logging.getLogger(__name__)

class DBListener:
    def __init__(self, config: Config, pool: sessionmaker):
        self.config = config
        self.session_pool = pool
        self.notification_service = NotificationService(config)
        self.db_config = config.db

    async def start(self):
        """Запускает процесс прослушивания в бесконечном цикле (с реконнектом)"""
        logger.info("DB Listener: Запуск сервиса прослушивания триггеров...")
        while True:
            try:
                # Создаем прямое соединение через asyncpg (SQLAlchemy тут не подходит для LISTEN)
                conn = await asyncpg.connect(
                    user=self.db_config.user,
                    password=self.db_config.password,
                    database=self.db_config.database,
                    host=self.db_config.host
                )

                # Добавляем колбэк функцию
                await conn.add_listener('bonus_updates', self._handle_notification)
                logger.info(" DB Listener: Подключено к каналу 'bonus_updates'")

                # Бесконечное ожидание, чтобы соединение не закрылось
                # Мы просто спим и пингуем базу раз в час, чтобы соединение жило
                while True:
                    await asyncio.sleep(3600)
                    await conn.execute("SELECT 1")

            except Exception as e:
                logger.error(f"DB Listener Error: {e}. Переподключение через 5 сек...")
                await asyncio.sleep(5)

    def _handle_notification(self, connection, pid, channel, payload):
        """Этот метод вызывается автоматически, когда срабатывает триггер в БД"""
        logger.info(f"DB Event received: {payload}")
        
        # Обработку запускаем в фоне, чтобы не блокировать слушателя
        asyncio.create_task(self._process_event(payload))

    async def _process_event(self, raw_payload: str):
        """
        Ожидаемый payload (JSON):
        - Начисление: {"client_id": int, "points": number}
        - Списание:   {"client_id": int, "points": number, "operation_type": "write_off"}
        """
        try:
            data = json.loads(raw_payload)
            client_id = data.get('client_id')
            points = int(float(data.get('points', 0)))  # float на случай если Decimal
            operation_type = (data.get('operation_type') or 'accrual').lower()

            if not client_id:
                return

            async with self.session_pool() as session:
                client = await session.get(Client, int(client_id))

                if not client:
                    logger.warning(f"Client {client_id} not found for bonus notification")
                    return

                locale = client.local if client.local in ['kaz', 'rus'] else 'rus'
                user_info = UserInfo(
                    user_type=UserType.CLIENT,
                    phone_number=client.phone_number,
                    locale=locale
                )

                if operation_type == 'write_off':
                    # П.12 ТЗ: сообщение о списании бонусов в бот
                    # RU: С вашего бонусного счёта списано *___* кэшбэка.
                    # KZ: Сіздің бонустық шотыңыздан ___ кэшбэк есептен шығарылды.
                    texts = {
                        'rus': f"С вашего бонусного счёта списано <b>{points}</b> кэшбэка.",
                        'kaz': f"Сіздің бонустық шотыңыздан {points} кэшбэк есептен шығарылды."
                    }
                    message_text = texts[locale]
                    success = await self.notification_service.send_notification(
                        user_info=user_info,
                        telegram_id=client.id,
                        message=message_text
                    )
                    if success:
                        logger.info(f"Write-off notification sent to client {client.id}, amount={points}")
                    else:
                        logger.error(f"Failed to send write-off notification to client {client.id}")
                else:
                    # Начисление (как раньше)
                    texts = {
                        'rus': (
                            "<b>Вам начислены новые бонусы!</b>\n"
                            f"На ваш бонусный счёт добавлено {points} бонусов за последнюю покупку.\n"
                            "Спасибо, что выбираете Qazaq Republic!"
                        ),
                        'kaz': (
                            "<b>Сізге жаңа бонус есептелді!</b>\n"
                            f"Соңғы сатып алуыңыз үшін бонус шотыңызға {points} бонус қосылды.\n"
                            "Qazaq Republic-ті таңдағаныңызға рақмет!"
                        )
                    }
                    message_text = texts[locale]
                    success = await self.notification_service.send_notification(
                        user_info=user_info,
                        telegram_id=client.id,
                        message=message_text
                    )
                    if success:
                        logger.info(f"Bonus accrual notification sent to client {client.id}")
                    else:
                        logger.error(f"Failed to send bonus notification to client {client.id}")

        except Exception as e:
            logger.exception(f"Error processing DB trigger payload: {e}")
