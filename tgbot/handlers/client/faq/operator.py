import datetime

from aiogram.types.message import Message, ContentType
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import Client, ClientsApp
from tgbot.keyboards.client.faq import get_times, get_grade_btns
from tgbot.misc.states.client import FaqState
from tgbot.misc.delete import remove
from tgbot.handlers.client.faq.main import faq_lvl_handler
from tgbot.customLib.bitrixAPI.leads import Leads
from tgbot.data.faq import grade_text, grades


async def operator_handler(
        message: Message,
        session: AsyncSession,
        state: FSMContext,
        user: Client,
):
    _ = message.bot.get('i18n')
    await message.delete()
    await remove(message, 1)
    # Сіз операторменн байланысу опциясын белгіледіңіз. Біз операторды қандай уақыт аралығында қосуымыз қажет? Төменде көрсетілген уақытты белгілеуіңізді сұраймыз:
    await message.answer(
        text=_("Вы выбрали опцию подключить оператора. Хотите, чтобы я подключил оператора сейчас или позже? Пожалуйста, выберите подходящий вариант:"),
        reply_markup=await get_times(_)
    )
    await FaqState.waiting_time.set()


async def send_operator_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        state: FSMContext,
        user: Client,
        callback_data: dict
):
    _ = callback.bot.get('i18n')
    waiting_time = callback_data.get('lvl')
    now_date = datetime.datetime.now()
    date = now_date + datetime.timedelta(minutes=int(waiting_time))
    data = await state.get_data()
    if not data.get('tag'):
        data['tag'] = '[LIST][619][VALUE]'
    # Сіз өтініш жібердіңіз, оператор сұрауыңызға жауап бергенше күтіңіз
    text = _("Вы уже подавали заявку, подождите пока оператор ответит на ваш запрос")
    if not (c := await ClientsApp.get_last_app(
        session=session,
        telegram_id=user.id
    )):
        # Таңдағаныңыз үшін рақмет! Оператор сізбен көрсетілген уақытта хабарласады.
        text = _("Спасибо за выбор! Оператор свяжется с вами в указанное время.")
        resp = await Leads(
            user_id=callback.bot.get('config').bitrix.user_id,
            basic_token=callback.bot.get('config').bitrix.token
        ).create(
            fields={
                "FIELDS[TITLE]": "Заявка с Telegram",
                "FIELDS[NAME]": user.name,
                "FIELDS[PHONE][0][VALUE]": user.phone_number,
                "FIELDS[PHONE][0][VALUE_TYPE]": "WORKMOBILE",
                "FIELDS[UF_CRM_1733080465]": user.id,
                "FIELDS[UF_CRM_1733197853]": now_date.strftime("%d.%m.%Y %H:%M:%S"),
                "FIELDS[UF_CRM_1733197875]": date.strftime("%d.%m.%Y %H:%M:%S"),
                "FIELDS[UF_CRM_1731574397751]": data.get('tag'),
                "FIELDS[IM][0][VALUE]": "Telegram",
                "FIELDS[IM][0][VALUE_TYPE]": "Telegram",
                "FIELDS[BIRTHDATE]": user.birthday_date.strftime("%d.%m.%Y %H:%M:%S")
            }
        )
        c = ClientsApp(
            id=resp.get('result'),
            telegram_id=user.id,
            waiting_time=date,
            phone_number=user.phone_number
        )
        session.add(c)
        await session.commit()
    # Сіз басты бетке оралдыңыз. Тағы қандай көмек көрсете аламыз?
    text += _("Вы вернулись к основному меню. Чем еще можем помочь?")
    callback_data['lvl'] = 'main'
    await faq_lvl_handler(
        callback=callback,
        callback_data=callback_data,
        state=state,
        text=text
    )


async def user_wait_answer_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        state: FSMContext,
        user: Client,
        callback_data: dict
):
    # 1. Сохраняем нужные данные из состояния перед его очисткой
    state_data = await state.get_data()
    session_locale = state_data.get("session_locale")
    
    # 2. Очищаем состояние (сбрасываем любые незавершенные диалоги)
    await state.finish()
    
    # 3. Восстанавливаем нужные нам данные обратно в чистое состояние
    if session_locale:
        await state.update_data(session_locale=session_locale)
    
    if callback_data.get('ans') == 'yes':
        await state.update_data(lid_id=callback_data.get('id'))
        return await user_grade_handler(
            callback=callback,
            session=session,
            state=state,
            user=user
        )
    await operator_handler(
        message=callback.message,
        session=session,
        state=state,
        user=user
    )


async def user_grade_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        state: FSMContext,
        user: Client
):
    _ = callback.bot.get('i18n')
    await callback.message.edit_text(
        text=_('Оцените работу оператора от 1 до 5'),
        reply_markup=get_grade_btns()
    )


async def user_graded_handler(
        callback: CallbackQuery,
        session: AsyncSession,
        state: FSMContext,
        user: Client,
        callback_data: dict
):
    _ = callback.bot.get('i18n')
    data = await state.get_data()
    await Leads(
        user_id=callback.bot.get('config').bitrix.user_id,
        basic_token=callback.bot.get('config').bitrix.token
    ).update(
        fields={
            "ID": data.get('lid_id'),
            "FIELDS[UF_CRM_1731932281238]": callback_data.get('id')
        }
    )

    text = grade_text.get(callback_data.get('ans') in ['1', '2', '3'])
    # Сіз басты бетке оралдыңыз. Тағы қандай көмек көрсете аламыз?
    text += _("Вы вернулись к основному меню. Чем еще можем помочь?")
    callback_data['lvl'] = 'main'
    await faq_lvl_handler(
        callback=callback,
        callback_data=callback_data,
        state=state,
        text=text
    )
    
    # 1. Сохраняем нужные данные из состояния перед его очисткой
    state_data = await state.get_data()
    session_locale = state_data.get("session_locale")
    
    # 2. Очищаем состояние (сбрасываем любые незавершенные диалоги)
    await state.finish()
    
    # 3. Восстанавливаем нужные нам данные обратно в чистое состояние
    if session_locale:
        await state.update_data(session_locale=session_locale)
