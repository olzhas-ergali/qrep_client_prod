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

ACCRUAL_MERGE_WINDOW_SEC = 5.0


class DBListener:
    def __init__(self, config: Config, pool: sessionmaker):
        self.config = config
        self.session_pool = pool
        self.notification_service = NotificationService(config)
        self.db_config = config.db
        # Объединение начислений: client_id -> (сумма баллов, таймер отложенной отправки)
        self._pending_accruals: dict = {}  # int -> (points_sum, timer_handle)
        self._accrual_lock = asyncio.Lock()

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

    async def _schedule_accrual_notification(
        self, client_id: int, points: float, client: Client, user_info: UserInfo, locale: str
    ):
        """Объединяет несколько начислений по одному client_id в одно сообщение (устраняет дубли)."""
        async with self._accrual_lock:
            if client_id in self._pending_accruals:
                entry = self._pending_accruals[client_id]
                entry["points"] += points
                if entry["timer"] is not None:
                    entry["timer"].cancel()
            else:
                self._pending_accruals[client_id] = {
                    "points": points,
                    "timer": None,
                    "locale": locale,
                    "telegram_id": client.id,
                    "user_info": user_info,
                }
            entry = self._pending_accruals[client_id]
            loop = asyncio.get_event_loop()
            entry["timer"] = loop.call_later(
                ACCRUAL_MERGE_WINDOW_SEC,
                lambda cid=client_id: asyncio.create_task(self._flush_accrual(cid)),
            )

    async def _flush_accrual(self, client_id: int):
        """Отправляет одно сообщение о начислении и снимает клиента с отложенной отправки."""
        async with self._accrual_lock:
            entry = self._pending_accruals.pop(client_id, None)
        if not entry:
            return
        points = int(entry["points"])
        locale = entry["locale"]
        telegram_id = entry["telegram_id"]
        user_info = entry["user_info"]
        texts = {
            "rus": (
                "<b>Вам начислены новые бонусы!</b>\n"
                f"На ваш бонусный счёт добавлено {points} бонусов за последнюю покупку.\n"
                "Спасибо, что выбираете Qazaq Republic!"
            ),
            "kaz": (
                "<b>Сізге жаңа бонус есептелді!</b>\n"
                f"Соңғы сатып алуыңыз үшін бонус шотыңызға {points} бонус қосылды.\n"
                "Qazaq Republic-ті таңдағаныңызға рақмет!"
            ),
        }
        message_text = texts.get(locale, texts["rus"])
        success = await self.notification_service.send_notification(
            user_info=user_info,
            telegram_id=telegram_id,
            message=message_text,
        )
        if success:
            logger.info(f"Bonus accrual notification sent to client {client_id}, total points={points}")
        else:
            logger.error(f"Failed to send bonus notification to client {client_id}")

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
                    # Начисление: объединяем несколько NOTIFY за одну покупку в одно сообщение
                    await self._schedule_accrual_notification(int(client_id), points, client, user_info, locale)

        except Exception as e:
            logger.exception(f"Error processing DB trigger payload: {e}")
