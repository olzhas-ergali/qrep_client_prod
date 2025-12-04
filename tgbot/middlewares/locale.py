# qrep_client/tgbot/middlewares/locale.py

from typing import Tuple, Any, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.dispatcher import FSMContext

from tgbot.models.database.users import Client

logger = logging.getLogger(__name__)


class ACLMiddleware(I18nMiddleware):

    async def get_user_locale(self, action: str, args: Tuple[Any]) -> Optional[str]:
        obj = args[0]
        
        # --- 1. Пытаемся достать FSM State (Текущая сессия) ---
        state: Optional[FSMContext] = None
        session_locale = None
        try:
            from aiogram import Dispatcher
            current_dispatcher = Dispatcher.get_current()
            if current_dispatcher:
                state = current_dispatcher.current_state()
                state_data = await state.get_data()
                session_locale = state_data.get('session_locale')
        except Exception:
            pass

        # Если в текущей быстрой памяти есть язык - используем его (это быстро)
        if session_locale:
            return session_locale

        # --- 2. Если сессия пуста (клиент перезашел), идем в БД ---
        db_locale = await self._get_locale_from_db(obj)
        
        if db_locale:
            # Нашли язык в БД! Значит клиент когда-то его выбрал.
            # Восстанавливаем его в сессию, чтобы в следующий раз не дергать БД.
            if state:
                await state.update_data(session_locale=db_locale)
            return db_locale
        
        # --- 3. Если нигде нет - дефолтный ---
        return 'rus'

    async def _get_locale_from_db(self, obj) -> Optional[str]:
        """Безопасно достаем язык из базы"""
        pool = obj.bot.get('pool')
        if not pool:
            return None
            
        session: AsyncSession = pool()
        try:
            # Ищем клиента по ID
            user = await session.get(Client, obj.from_user.id)
            if user and user.local:
                return user.local
        except Exception as e:
            logger.error(f"Ошибка получения языка из БД: {e}")
        finally:
            await session.close()
            
        return None