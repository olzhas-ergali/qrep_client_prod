from aiogram.types.message import Message
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext

from tgbot.keyboards.client.faq import get_faq_btns
from tgbot.keyboards.client.client import change_locale
from tgbot.data.faq_new import faq_texts_update, tags
from tgbot.misc.states.client import FaqState
from tgbot.models.database.users import Client
from sqlalchemy.ext.asyncio import AsyncSession
from tgbot.misc.state_helpers import clear_state_but_preserve_locale


async def get_faq_main_handler(
        message: Message,
        state: FSMContext
):
    _ = message.bot.get("i18n")
    
    await clear_state_but_preserve_locale(state)

    btns = await get_faq_btns('main', _)
    await message.answer(
        text=_("Пожалуйста, выберите одну из опций:"),
        reply_markup=btns
    )


async def faq_lvl_handler(
        callback: CallbackQuery,
        callback_data: dict,
        state: FSMContext,
        text: str = None
):
    _ = callback.bot.get("i18n")

    await clear_state_but_preserve_locale(state)

    if not text:
        lvl = callback_data.get('lvl').replace('*', callback_data.get('chapter'))
        
        # --- ИСПРАВЛЕННАЯ ЛОГИКА ---
        # 1. Получаем оригинальный текст-ключ из словаря
        original_text = faq_texts_update.get(lvl)
        
        # 2. Переводим текст прямо здесь, если он найден. Иначе - текст по умолчанию.
        if original_text:
            text = _(original_text)
        else:
            text = _("Пожалуйста, выберите одну из опций:")
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
            
        if 'operator' in callback_data.get('lvl'):
            # Текст для оператора берется так же, но из другого ключа
            text = _(faq_texts_update.get('operator'))
            await state.update_data(tag=tags.get(callback_data.get('chapter')))
            await FaqState.waiting_operator.set()

    await callback.message.edit_text(
        text=text,
        reply_markup=await get_faq_btns(callback_data.get('lvl'), _)
    )


async def choose_locale_handler(
        callback: CallbackQuery,
        user: Client,
        state: FSMContext
):
    _ = callback.bot.get('i18n')
    text = _("Выберите язык:")

    await callback.message.edit_text(
        text=text,
        reply_markup=await change_locale('client_locale')
    )


async def change_locale_handler(
        query: CallbackQuery,
        user: Client,
        session: AsyncSession,
        callback_data: dict,
        state: FSMContext
):
    import logging
    logger = logging.getLogger(__name__)
    
    # 1. Получаем новый язык из кнопки
    local = callback_data.get('lang')
    _ = query.bot.get('i18n')
    
    logger.info(f"🔄 ЯЗЫК: Пользователь {user.id} нажал смену языка на: {local}")
    
    # 2. МОМЕНТАЛЬНО сохраняем в Базу Данных (Вечное хранение)
    # Если пользователь уйдет и вернется, мы возьмем язык отсюда
    user.local = local
    await user.save(session)
    logger.info(f"💾 ЯЗЫК: Сохранено в БД (user.local = {local})")
    
    # 3. Обновляем текущую сессию FSM (Быстрое хранение)
    # Это нужно, чтобы язык сменился прямо сейчас без лишних запросов в БД
    await state.update_data(session_locale=local)
    logger.info(f"⚡ ЯЗЫК: Обновлено в FSM (session_locale = {local})")
    
    # 4. Отправляем ответ пользователю уже на новом языке
    # Важно: locale=local передаем явно, так как middleware мог еще не переключиться
    text = _('Вы сменили язык', locale=local)
    await query.message.delete()
    
    btns = await get_faq_btns('main', _, locale=local)
    await query.message.answer(
        text=text,
        reply_markup=btns
    )
