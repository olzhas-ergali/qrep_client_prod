import asyncio
import logging
import os
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from tgbot.config import load_config
from tgbot.webhooks.purchase_webhook import PurchaseWebhookHandler, setup_webhook_routes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def create_app():
    """Создание и настройка aiohttp приложения"""
    
    # Загружаем конфигурацию
    config = load_config(".env")
    
    # Создаем движок для БД
    engine = create_async_engine(
        f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}",
        echo=False
    )
    
    # Создаем фабрику сессий
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    # Создаем приложение
    app = web.Application()
    
    # Создаем обработчик webhook'ов
    webhook_handler = PurchaseWebhookHandler(config, session_factory)
    
    # Настраиваем маршруты
    setup_webhook_routes(app, webhook_handler)
    
    # Сохраняем зависимости в app для использования в middleware
    app['config'] = config
    app['db_engine'] = engine
    app['session_factory'] = session_factory
    
    return app


async def init_app():
    """Инициализация приложения"""
    app = await create_app()
    return app


def main():
    """Основная функция запуска сервера"""
    logger.info("Starting webhook server...")
    
    app = asyncio.get_event_loop().run_until_complete(init_app())
    port = int(os.getenv("WEBHOOK_PORT", "8080"))
    logger.info("Webhook server will listen on port %s", port)
    
    # Запускаем сервер
    web.run_app(
        app,
        host='0.0.0.0',
        port=port,
        access_log=logger
    )


if __name__ == '__main__':
    main()
