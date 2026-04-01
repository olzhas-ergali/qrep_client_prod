import logging
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.engine import URL

from tgbot.data import I18N_DOMAIN, LOCALES_DIR
from tgbot.models.database.base import Database
from tgbot.config import load_config
from tgbot.filters.client_auth import ClientAuthFilter
from tgbot.filters.i18n import I18nTextFilter
from tgbot.middlewares.db import DbMiddleware
from tgbot.middlewares.locale import ACLMiddleware
from tgbot.misc.job import tasks
from tgbot import handlers

# --- ИМПОРТ НОВОГО СЛУШАТЕЛЯ ---
from tgbot.services.db_listener import DBListener
# -------------------------------

logger = logging.getLogger(__name__)


def register_all_middlewares(dp):
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR, 'rus')
    dp.setup_middleware(DbMiddleware())
    dp.setup_middleware(i18n)
    return i18n


def register_all_filters(dp):
    dp.filters_factory.bind(ClientAuthFilter)
    dp.filters_factory.bind(I18nTextFilter)


def register_all_handlers(dp):
    handlers.register.register_staff(dp)
    handlers.client.register.register_client_function(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    env_path = os.getenv("ENV_FILE", ".env")
    logger.info("Using env file: %s", env_path)
    config = load_config(env_path)
    
    if config.tg_bot.use_redis:
        storage = RedisStorage2(config.tg_bot.redis_host)
    else:
        storage = MemoryStorage()

    bot_token_override = os.getenv("BOT_TOKEN_OVERRIDE", "").strip()
    bot_token = bot_token_override or config.tg_bot.client_token
    bot = Bot(token=bot_token, parse_mode='HTML')
    db = Database()

    scheduler = AsyncIOScheduler(
        timezone='Asia/Aqtobe'
    )
    
    await db.create_pool(
        URL(
            drivername="postgresql+asyncpg",
            username=config.db.user,
            password=config.db.password,
            host=config.db.host,
            database=config.db.database,
            query={},
            port=5432
        )
    )

    dp = Dispatcher(bot, storage=storage)

    i18n = register_all_middlewares(dp)
    bot['i18n'] = i18n.gettext
    bot['storage'] = storage
    bot['config'] = config
    bot['pool'] = db.pool

    # --- ЗАПУСК DB LISTENER (ТРИГГЕРЫ) ---
    # Создаем экземпляр слушателя и запускаем его в фоновой задаче
    # Это обеспечит мгновенную реакцию на изменения в базе
    db_listener = DBListener(config, db.pool)
    asyncio.create_task(db_listener.start())
    # -------------------------------------

    scheduler.add_job(
        tasks.push_client_authorization,
        'cron',
        hour=15,
        minute=00,
        args=(db.pool, config, i18n.gettext)
    )

    # Добавляем задачу для уведомлений об оценке качества покупок
    scheduler.add_job(
        tasks.push_client_answer_operator,
        'interval',
        minutes=5,
        args=(db.pool, config, i18n.gettext)
    )

    register_all_filters(dp)
    register_all_handlers(dp)

    bot_me = await bot.me
    logging.info(
        f'starting bot: @{bot_me.username}'
    )

    try:
        scheduler.start()
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")