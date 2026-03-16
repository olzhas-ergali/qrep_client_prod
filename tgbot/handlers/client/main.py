import os
import segno
import datetime
import logging

from aiogram.types.message import Message, ContentType
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import Client
from tgbot.models.database.cods import Cods
from tgbot.misc.delete import remove
from tgbot.keyboards.client.faq import get_faq_btns, get_bonus_history_btns
from tgbot.misc.generate import generate_code
from tgbot.models.database.loyalty import ClientBonusPoints
from tgbot.misc.state_helpers import clear_state_but_preserve_locale
import textwrap


async def main_handler(
        m: Message | CallbackQuery
):
    logger = logging.getLogger(__name__)
    logger.info(f"🏠 MAIN_HANDLER: Обрабатываем запрос от пользователя {m.from_user.id}")
    
    _ = m.bot.get("i18n")
    btns = await get_faq_btns('main', _)
    
    try:
        main_text = _("Пожалуйста, выберите одну из опций: ")
        logger.info(f"🏠 MAIN_HANDLER: Перевод главного текста успешен: '{main_text}'")
        
        if isinstance(m, Message):
            logger.info(f"🏠 MAIN_HANDLER: Отправляем новое сообщение (Message)")
            return await m.answer(
                text=main_text,
                reply_markup=btns
            )
        else:  # CallbackQuery
            logger.info(f"🏠 MAIN_HANDLER: Редактируем существующее сообщение (CallbackQuery)")
            # Для CallbackQuery используем edit_text чтобы не создавать новое сообщение
            try:
                return await m.message.edit_text(
                    text=main_text,
                    reply_markup=btns
                )
            except Exception as edit_error:
                logger.warning(f"🏠 MAIN_HANDLER: Не удалось отредактировать сообщение ({edit_error}), отправляем новое")
                # Если не удается отредактировать, отправляем новое
                return await m.message.answer(
                    text=main_text,
                    reply_markup=btns
                )
    except Exception as e:
        logger.error(f"🏠 MAIN_HANDLER: Ошибка перевода: {e}")
        # Fallback на русский текст
        fallback_text = "Пожалуйста, выберите одну из опций: "
        
        if isinstance(m, Message):
            return await m.answer(
                text=fallback_text,
                reply_markup=btns
            )
        else:
            try:
                return await m.message.edit_text(
                    text=fallback_text,
                    reply_markup=btns
                )
            except:
                return await m.message.answer(
                    text=fallback_text,
                    reply_markup=btns
                )


async def start_handler(
        message: Message,
        user: Client,
        session: AsyncSession,
        state: FSMContext,
        is_new_user: bool = False
):
    _ = message.bot.get("i18n")
    
    # Безопасно очищаем состояние, сохраняя язык
    await clear_state_but_preserve_locale(state)
    
    await remove(message, 1)
    await remove(message, 0)
    logging.info(f"Клиент с id: {user.id} авторизовался/зарегался в боте")
    
    # Формируем приветствие в зависимости от того, новый ли это пользователь
    if is_new_user:
        text = _("Спасибо! Регистрация завершена.\nВы стали участником программы QR+ и теперь получаете 5% кэшбэка с каждой покупки.\nВаш персональный QR-код и информация о кэшбэке доступны в меню.\n\nПожалуйста, выберите одну из опций:")
    else:
        text = _("Уважаемый покупатель {name}, вас приветствует Qazaq Republic.\n\nПожалуйста, выберите одну из опций:").format(name=user.name)
    
    btns = await get_faq_btns('main', _, locale=user.local)
    
    await message.answer(
        text=text,
        reply_markup=btns
    )


async def get_my_qr_handler(
        callback: CallbackQuery,
        user: Client,
        session: AsyncSession,
        state: FSMContext
):
    _ = callback.bot.get('i18n')
    
    # 1. Сохраняем нужные данные из состояния перед его очисткой
    await clear_state_but_preserve_locale(state)
    
    text = _("Вы уже сгенерировали QR, дождитесь 15 минут, чтобы сгенерировать QR")
    qrcode = None
    code = await Cods.get_cody_by_phone(user.phone_number, session)
    if not code or (code and code.is_active) or (datetime.datetime.now() - code.created_at).total_seconds()/60 > 15:
        text = _(
            "\n"
            "Это ваш персональный QR-код для начисления и списания кэшбэка.\n"
            "Обязательно покажите его кассиру перед оплатой, чтобы получить кэшбэк или использовать накопленный.\n"
            "\n"
        )
        code = await generate_code(session, phone_number=user.phone_number)
        qrcode = segno.make(code.code, micro=False)
        qrcode.save(user.phone_number + ".png", border=4, scale=7)

    await callback.message.delete()
    if qrcode:
        await callback.message.answer_photo(
            photo=open(user.phone_number + ".png", "rb"),
            caption=text,
        )
        try:
            os.remove(user.phone_number + ".png")
        except:
            pass
    else:
        await callback.message.answer(
            text=text
        )
    # Вызываем main_handler только один раз - он сам отправит меню
    await main_handler(callback)


async def get_my_bonus_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        user: Client,
        state: FSMContext
):
    _ = callback.bot.get('i18n')
    
    # ВРЕМЕННАЯ ДИАГНОСТИКА
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"💰 BONUS_HANDLER: Пользователь {callback.from_user.id} запросил баланс")
    
    # 1. Сохраняем нужные данные из состояния перед его очисткой
    await clear_state_but_preserve_locale(state)
    
    client_bonuses = await ClientBonusPoints.get_all_by_client_id(session=session, client_id=user.id)
    available_bonus = 0
    future_bonus = 0
    if client_bonuses:
        total_earned = 0
        total_spent = 0
        total_future_spent = 0
        total_future_earned = 0
        for bonus in client_bonuses:
            logging.info(f"accrued_points: {bonus.accrued_points}")
            logging.info(f"write_off_points: {bonus.write_off_points}")
            if bonus.expiration_date and bonus.expiration_date.date() < datetime.datetime.now().date():
                continue
            if datetime.datetime.now().date() >= bonus.activation_date.date() or bonus.expiration_date.date() is None:
                total_earned += bonus.accrued_points if bonus.accrued_points else 0
                total_spent += bonus.write_off_points if bonus.write_off_points else 0
            else:
                total_future_earned += bonus.accrued_points if bonus.accrued_points else 0
                total_future_spent += bonus.write_off_points if bonus.write_off_points else 0
        if total_earned > 0:
            available_bonus += total_earned
        if total_spent > 0:
            available_bonus -= total_spent
        if total_future_earned > 0:
            future_bonus += total_future_earned
        if total_future_spent > 0:
            future_bonus -= total_future_spent

    text_template = _(
        "\n"
        "Ваш баланс кэшбэка: {cashback} \n"
        "Если сумма равна 0 , это может означать, что:\n"
        "• вы ещё не совершали покупок, или\n"
        "• кэшбэк по вашему заказу ещё не начислен — он будет зачислен на бонусный счёт через 14 дней после покупки.\n\n"
        "Ожидаемая сумма начисления: {future_bonus}\n"
        "\n"
    )
    
    logger.info(f"💰 BONUS_HANDLER: Шаблон сообщения: {text_template[:100]}...")

    text = text_template.format(cashback=available_bonus if available_bonus > 0 else 0, future_bonus=future_bonus)
    btns = await get_faq_btns('main', _, locale=user.local)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=btns
    )
#     res, msg = await get_balance(
#         user=user,
#         bot=callback.bot
#     )
#     await callback.message.delete()
#     if res == 0:
#         await callback.message.answer(
#             text=_('''У вас пока нет накопленных бонусов.
# Совершайте покупки и участвуйте в наших акциях,
# чтобы начать зарабатывать баллы!''')
#         )
#     else:
#         await callback.message.answer(
#             text=_("У вас: {res} бонусов {msg}").format(res=res, msg=msg),
#         )



BONUS_HISTORY_PER_PAGE = 5


async def get_bonus_history_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        user: Client,
        state: FSMContext,
        page: int = 1
):
    """Хендлер истории бонусов с пагинацией."""
    _ = callback.bot.get('i18n')

    await clear_state_but_preserve_locale(state)

    # 1. Считаем баланс
    client_bonuses = await ClientBonusPoints.get_all_by_client_id(session=session, client_id=user.id)
    available_bonus = 0
    if client_bonuses:
        total_earned = sum(float(b.accrued_points or 0) for b in client_bonuses if b.activation_date.date() <= datetime.datetime.now().date())
        total_spent = sum(float(b.write_off_points or 0) for b in client_bonuses)
        available_bonus = int(total_earned - total_spent)

    # 2. Получаем общее количество и историю с пагинацией
    try:
        total_count = await ClientBonusPoints.get_history_count(session, user.id)
        total_pages = max(1, (total_count + BONUS_HISTORY_PER_PAGE - 1) // BONUS_HISTORY_PER_PAGE)

        # Проверяем границы страницы
        page = max(1, min(page, total_pages))
        offset = (page - 1) * BONUS_HISTORY_PER_PAGE

        history = await ClientBonusPoints.get_history_with_details(
            session, user.id, limit=BONUS_HISTORY_PER_PAGE, offset=offset
        )
    except Exception as e:
        logging.error(f"Ошибка получения истории бонусов: {e}")
        return await callback.answer("Ошибка при получении истории")

    # 3. Формируем текст
    is_kaz = (user.local == 'kaz')

    if is_kaz:
        text = f"Сіздегі қазіргі бонус балансы: {available_bonus} бонус\n\nОперациялар:\n\n"
    else:
        text = f"Ваш текущий бонусный баланс: {available_bonus} бонусов\n\nИстория:\n\n"

    if not history:
        text += "Тарих бос." if is_kaz else "История пуста."

    for row in history:
        bonus = row.ClientBonusPoints
        ticket_url = (row.purchase_ticket or "").strip()
        raw_date = row.purchase_date or bonus.operation_date
        op_date = raw_date.strftime('%Y-%m-%d') if raw_date else "—"
        # Кликабельная ссылка, если пришла из API; иначе — пояснение
        if ticket_url and (ticket_url.startswith("http://") or ticket_url.startswith("https://")):
            ticket_display = f'<a href="{ticket_url}">Чек</a>'
        elif ticket_url:
            ticket_display = ticket_url
        else:
            ticket_display = "Не указана"

        if not is_kaz:
            text += f"Дата покупки: {op_date}\n"
            if bonus.write_off_points and bonus.write_off_points > 0:
                text += f"Бонусы списаны: {int(bonus.write_off_points)}\n"
            if bonus.accrued_points and bonus.accrued_points > 0:
                text += f"Бонусы начислены: {int(bonus.accrued_points)}\n"
            text += f"Ссылка на чек: {ticket_display}\n\n"
        else:
            text += f"Сатып алу күні: {op_date}\n"
            if bonus.write_off_points and bonus.write_off_points > 0:
                text += f"• Бонустар қолданылды: {int(bonus.write_off_points)}\n"
            if bonus.accrued_points and bonus.accrued_points > 0:
                text += f"• Бонустар қосылды: {int(bonus.accrued_points)}\n"
            text += f"• Түбіртек сілтемесі: {ticket_display}\n\n"

    # 4. Кнопки с пагинацией
    btns = get_bonus_history_btns(page, total_pages, _, locale=user.local)

    try:
        await callback.message.edit_text(
            text=text, reply_markup=btns, disable_web_page_preview=True, parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text=text, reply_markup=btns, disable_web_page_preview=True, parse_mode="HTML"
        )


async def bonus_history_page_handler(
        callback: CallbackQuery,
        callback_data: dict,
        session: AsyncSession,
        user: Client,
        state: FSMContext
):
    """Хендлер переключения страниц истории бонусов."""
    action = callback_data.get('action')

    if action == 'current':
        # Просто нажали на счётчик страниц - ничего не делаем
        return await callback.answer()

    page = int(callback_data.get('page', 1))
    await get_bonus_history_handler(callback, session, user, state, page=page)