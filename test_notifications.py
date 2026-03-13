#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы дифференцированных уведомлений.
Тестирует:
1. Webhook endpoint для уведомлений о покупках
2. Определение типа пользователя (сотрудник/клиент)
3. Отправку уведомлений в правильные боты
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationTester:
    def __init__(self, webhook_url: str = "http://localhost:8080"):
        self.webhook_url = webhook_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_webhook_health(self) -> bool:
        """Проверка работоспособности webhook сервера"""
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
    
    async def test_purchase_notification(self, phone_number: str, telegram_id: int, purchase_id: str = None) -> bool:
        """Тест отправки уведомления о покупке"""
        payload = {
            "phone_number": phone_number,
            "telegram_id": telegram_id
        }
        
        if purchase_id:
            payload["purchase_id"] = purchase_id
        
        try:
            async with self.session.post(
                f"{self.webhook_url}/purchase-notification",
                json=payload
            ) as response:
                
                response_data = await response.json()
                
                if response.status == 200:
                    logger.info(f"✅ Purchase notification sent successfully for {phone_number}: {response_data}")
                    return True
                else:
                    logger.error(f"❌ Purchase notification failed for {phone_number}: {response.status} - {response_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Purchase notification error for {phone_number}: {e}")
            return False
    
    async def test_invalid_requests(self) -> bool:
        """Тестирование обработки некорректных запросов"""
        test_cases = [
            # Отсутствует phone_number
            {"telegram_id": 123456789},
            # Отсутствует telegram_id
            {"phone_number": "+77001234567"},
            # Некорректный telegram_id
            {"phone_number": "+77001234567", "telegram_id": "invalid_id"},
            # Пустой запрос
            {}
        ]
        
        all_passed = True
        
        for i, payload in enumerate(test_cases):
            try:
                async with self.session.post(
                    f"{self.webhook_url}/purchase-notification",
                    json=payload
                ) as response:
                    
                    if response.status == 400:
                        response_data = await response.json()
                        logger.info(f"✅ Invalid request {i+1} correctly rejected: {response_data.get('error', 'Unknown error')}")
                    else:
                        logger.error(f"❌ Invalid request {i+1} should have been rejected with 400, got {response.status}")
                        all_passed = False
                        
            except Exception as e:
                logger.error(f"❌ Error testing invalid request {i+1}: {e}")
                all_passed = False
        
        return all_passed


async def run_tests():
    """Основная функция запуска тестов"""
    logger.info("🚀 Начинаем тестирование системы уведомлений...")
    
    # Тестовые данные
    test_cases = [
        {
            "description": "Тест для сотрудника",
            "phone_number": "+77001111111",  # Номер который должен быть в таблице User
            "telegram_id": 111111111,
            "purchase_id": "STAFF_PURCHASE_001"
        },
        {
            "description": "Тест для клиента",
            "phone_number": "+77002222222",  # Номер который должен быть в таблице Client
            "telegram_id": 222222222,
            "purchase_id": "CLIENT_PURCHASE_001"
        },
        {
            "description": "Тест для неизвестного пользователя",
            "phone_number": "+77009999999",  # Номер которого нет в БД
            "telegram_id": 999999999,
            "purchase_id": "UNKNOWN_PURCHASE_001"
        }
    ]
    
    async with NotificationTester() as tester:
        # 1. Тест здоровья сервера
        logger.info("📋 Шаг 1: Проверка работоспособности webhook сервера")
        if not await tester.test_webhook_health():
            logger.error("❌ Сервер не отвечает. Убедитесь что webhook сервер запущен.")
            return False
        
        # 2. Тест корректных уведомлений
        logger.info("📋 Шаг 2: Тестирование отправки уведомлений")
        success_count = 0
        for test_case in test_cases:
            logger.info(f"  🔍 {test_case['description']}")
            if await tester.test_purchase_notification(
                phone_number=test_case["phone_number"],
                telegram_id=test_case["telegram_id"],
                purchase_id=test_case["purchase_id"]
            ):
                success_count += 1
        
        logger.info(f"  ✅ Успешно отправлено: {success_count}/{len(test_cases)} уведомлений")
        
        # 3. Тест некорректных запросов
        logger.info("📋 Шаг 3: Тестирование обработки некорректных запросов")
        if await tester.test_invalid_requests():
            logger.info("  ✅ Все некорректные запросы правильно обработаны")
        else:
            logger.error("  ❌ Есть проблемы с обработкой некорректных запросов")
        
        logger.info("🎉 Тестирование завершено!")
        return success_count == len(test_cases)


def print_usage_info():
    """Выводит информацию об использовании"""
    print("""
🔧 Инструкция по тестированию:

1. Запустите webhook сервер:
   python webhook_server.py

2. Убедитесь что в БД есть тестовые данные:
   - User с phone_number = "+77001111111"
   - Client с phone_number = "+77002222222"

3. Запустите тесты:
   python test_notifications.py

4. Проверьте логи и сообщения в тестовых ботах:
   - Client bot: @S04112021_bot
   - Staff bot: @whyareyousomad_bot

📝 Что проверяется:
- ✅ Webhook endpoint доступен
- ✅ Определение типа пользователя по номеру телефона
- ✅ Отправка в правильный бот (client/staff)
- ✅ Обработка некорректных запросов
- ✅ Логирование всех операций
""")


if __name__ == "__main__":
    print_usage_info()
    
    # Запуск тестов
    result = asyncio.run(run_tests())
    
    if result:
        logger.info("🎉 Все тесты прошли успешно!")
        exit(0)
    else:
        logger.error("❌ Некоторые тесты не прошли.")
        exit(1)
