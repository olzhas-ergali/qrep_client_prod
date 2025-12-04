from aiogram.dispatcher import FSMContext
import logging

async def clear_state_but_preserve_locale(state: FSMContext):
    """
    Безопасно очищает состояние, сохраняя выбранный язык.
    """
    session_locale = None
    try:
        data = await state.get_data()
        session_locale = data.get("session_locale")
        logging.info(f"Сохраняем session_locale: {session_locale} перед очисткой состояния.")
    except Exception as e:
        logging.error(f"Не удалось получить данные из состояния перед очисткой: {e}")

    # Полностью очищаем состояние, завершая любой предыдущий диалог
    await state.finish()
    
    # Если язык был установлен, восстанавливаем его в новом, чистом состоянии
    if session_locale:
        await state.update_data(session_locale=session_locale)
        logging.info(f"Восстановили session_locale: {session_locale} после очистки состояния.")