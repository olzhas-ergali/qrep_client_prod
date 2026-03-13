#!/usr/bin/env python3
"""
Продакшн тесты для webhook сервиса.
Проверяет реальную работу с БД и Telegram API.
"""

import asyncio
import aiohttp
import json
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from tgbot.config import load_config
from tgbot.models.database.users import User, Client

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionTester:
    def __init__(self, webhook_url: str = "http://127.0.0.1:8080"):
        self.webhook_url = webhook_url
        self.session = None
        self.config = None
        self.db_session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.config = load_config(".env")
        
        # Подключение к БД
        engine = create_async_engine(
            f"postgresql+asyncpg://{self.config.db.user}:{self.config.db.password}@{self.config.db.host}/{self.config.db.database}",
            echo=False
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        self.db_session = session_factory()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.db_session:
            await self.db_session.close()
    
    async def test_database_connection(self) -> bool:
        """Тест подключения к БД"""
        try:
            # Проверяем подключение к БД
            result = await self.db_session.execute("SELECT 1")
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def test_find_real_users(self):
        """Находим реальных пользователей в БД для тестов"""
        try:
            # Ищем реального сотрудника
            staff_user = await self.db_session.execute(
                "SELECT id, name, phone_number FROM users WHERE phone_number IS NOT NULL LIMIT 1"
            )
            staff_result = staff_user.fetchone()
            
            # Ищем реального клиента
            client_user = await self.db_session.execute(
                "SELECT id, name, phone_number FROM clients WHERE phone_number IS NOT NULL LIMIT 1"
            )
            client_result = client_user.fetchone()
            
            logger.info("📋 Найденные пользователи в БД:")
            if staff_result:
                logger.info(f"  👨‍💼 Сотрудник: ID={staff_result[0]}, Name={staff_result[1]}, Phone={staff_result[2]}")
            else:
                logger.warning("  ⚠️ Сотрудники с номерами телефонов не найдены")
            
            if client_result:
                logger.info(f"  👤 Клиент: ID={client_result[0]}, Name={client_result[1]}, Phone={client_result[2]}")
            else:
                logger.warning("  ⚠️ Клиенты с номерами телефонов не найдены")
            
            return staff_result, client_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска пользователей: {e}")
            return None, None
    
    async def test_webhook_health(self) -> bool:
        """Проверка health endpoint"""
        try:
            async with self.session.get(f"{self.webhook_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    async def test_webhook_with_fake_telegram_id(self, phone_number: str) -> bool:
        """Тест webhook с фейковым telegram_id (не будет отправлять в Telegram)"""
        payload = {
            "phone_number": phone_number,
            "telegram_id": 999999999,  # Фейковый ID для теста логики
            "purchase_id": "PROD_TEST_001"
        }
        
        try:
            async with self.session.post(
                f"{self.webhook_url}/purchase-notification",
                json=payload
            ) as response:
                
                response_data = await response.json()
                
                if response.status == 500 and "Failed to send notification" in response_data.get('message', ''):
                    logger.info(f"✅ Webhook логика работает для {phone_number} (ошибка Telegram ожидаема)")
                    return True
                elif response.status == 200:
                    logger.info(f"✅ Webhook успешно отправил уведомление для {phone_number}")
                    return True
                else:
                    logger.error(f"❌ Неожиданный ответ для {phone_number}: {response.status} - {response_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Ошибка webhook теста для {phone_number}: {e}")
            return False
    
    async def test_bot_tokens(self) -> bool:
        """Проверка валидности токенов ботов"""
        tokens = {
            "Client Bot": self.config.tg_bot.client_token,
            "Staff Bot": self.config.tg_bot.staff_token
        }
        
        all_valid = True
        
        for bot_name, token in tokens.items():
            try:
                url = f"https://api.telegram.org/bot{token}/getMe"
                async with self.session.get(url) as response:
                    data = await response.json()
                    
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        logger.info(f"✅ {bot_name} токен валиден: @{bot_info.get('username', 'unknown')}")
                    else:
                        logger.error(f"❌ {bot_name} токен невалиден: {data}")
                        all_valid = False
                        
            except Exception as e:
                logger.error(f"❌ Ошибка проверки {bot_name}: {e}")
                all_valid = False
        
        return all_valid


async def run_production_tests():
    """Запуск продакшн тестов"""
    logger.info("🚀 Запуск продакшн тестов webhook сервиса...")
    
    async with ProductionTester() as tester:
        success_count = 0
        total_tests = 5
        
        # 1. Тест подключения к БД
        logger.info("📋 Шаг 1: Проверка подключения к БД")
        if await tester.test_database_connection():
            success_count += 1
        
        # 2. Поиск реальных пользователей
        logger.info("📋 Шаг 2: Поиск пользователей в БД")
        staff_user, client_user = await tester.test_find_real_users()
        if staff_user or client_user:
            success_count += 1
        
        # 3. Проверка health endpoint
        logger.info("📋 Шаг 3: Проверка health endpoint")
        if await tester.test_webhook_health():
            success_count += 1
        
        # 4. Проверка токенов ботов
        logger.info("📋 Шаг 4: Проверка токенов ботов")
        if await tester.test_bot_tokens():
            success_count += 1
        
        # 5. Тест webhook логики
        logger.info("📋 Шаг 5: Тест webhook логики")
        webhook_success = False
        
        if staff_user:
            if await tester.test_webhook_with_fake_telegram_id(staff_user[2]):
                webhook_success = True
        
        if client_user and not webhook_success:
            if await tester.test_webhook_with_fake_telegram_id(client_user[2]):
                webhook_success = True
        
        if not staff_user and not client_user:
            # Тест с несуществующим номером
            if await tester.test_webhook_with_fake_telegram_id("+77009999999"):
                webhook_success = True
        
        if webhook_success:
            success_count += 1
        
        # Результаты
        logger.info(f"🎉 Тестирование завершено: {success_count}/{total_tests} тестов прошли успешно")
        
        if success_count == total_tests:
            logger.info("✅ Все продакшн тесты прошли успешно!")
            return True
        else:
            logger.error("❌ Некоторые тесты не прошли.")
            return False


def print_production_info():
    """Информация о продакшн тестах"""
    print("""
🔧 Продакшн тесты webhook сервиса:

📝 Что проверяется:
- ✅ Подключение к PostgreSQL БД
- ✅ Наличие реальных пользователей в БД
- ✅ Работоспособность webhook endpoints
- ✅ Валидность токенов Telegram ботов
- ✅ Логика определения типа пользователя

⚠️ Важно:
- Тесты НЕ отправляют реальные сообщения в Telegram
- Используются фейковые telegram_id для проверки логики
- Проверяется только серверная часть webhook'а

🚀 Для запуска:
python test_production.py
""")


if __name__ == "__main__":
    print_production_info()
    
    # Запуск тестов
    result = asyncio.run(run_production_tests())
    
    if result:
        logger.info("🎉 Продакшн тесты завершены успешно!")
        exit(0)
    else:
        logger.error("❌ Продакшн тесты завершены с ошибками.")
        exit(1)
