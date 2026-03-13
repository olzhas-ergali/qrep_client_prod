import datetime
import logging
import regex

from aiogram.types.message import Message, ContentType
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import Client, RegTemp, User
from tgbot.handlers.auth import phone_handler
from tgbot.handlers.client.main import start_handler
from tgbot.misc.states.client import AuthClientState
from tgbot.misc.parse import parse_phone, is_mail_valid
from tgbot.misc.delete import remove
from tgbot.keyboards.client.calendar import make_ikb_calendar, make_year_ikb
from tgbot.keyboards.client.client import get_genders_ikb, get_universal_btn


async def auth_phone_handler(
        message: Message,
        state: FSMContext,
        reg: RegTemp,
        user: User | Client,
        session: AsyncSession
):
    logging.info(f"Авторизация клиента -> {user.id}")
    
    # 1. Сохраняем нужные данные из состояния перед его очисткой
    state_data = await state.get_data()
    session_locale = state_data.get("session_locale")
    
    # 2. Очищаем состояние (сбрасываем любые незавершенные диалоги)
    await state.finish()
    
    # 3. Восстанавливаем нужные нам данные обратно в чистое состояние
    if session_locale:
        await state.update_data(session_locale=session_locale)
    if reg:
        reg.state = "AuthClientState:waiting_phone"
        session.add(reg)
        await session.commit()
    await phone_handler(
        m=message,
        state=AuthClientState.waiting_phone
    )


async def auth_fio_handler(
        message: Message,
        user: Client,
        session: AsyncSession,
        state: FSMContext,
        reg: RegTemp
):
    _ = message.bot.get("i18n")
    await message.delete()
    try:
        phone_number = parse_phone(message.contact.phone_number)
    except:
        phone_number = reg.state_data.get('phone')

    # Проверяем, является ли пользователь сотрудником
    # Исключение для тестового номера
    TEST_PHONE_EXCLUDE = "77752415853"
    staff_user = await User.get_by_phone(session=session, phone=phone_number)
    if staff_user and phone_number != TEST_PHONE_EXCLUDE:
        # Получаем язык пользователя из состояния FSM
        state_data = await state.get_data()
        user_locale = state_data.get('session_locale', 'rus')

        if user_locale == 'kaz':
            staff_message = (
                "Сіз <b>Qazaq Republic</b> компаниясының қызметкерісіз. "
                "Тапсырысты рәсімдеуді жалғастыру үшін "
                "<a href='https://t.me/qrep1465bot'>@qrep1465bot</a> ботына өтуді сұраймыз. "
                "Саудаңыз сәтті өтсін!"
            )
        else:
            staff_message = (
                "Вы являетесь сотрудником компании <b>Qazaq Republic</b>. "
                "Просим перейти в бот <a href='https://t.me/qrep1465bot'>@qrep1465bot</a> "
                "для дальнейших шагов по оформлению заказа. Желаем вам приятных покупок!"
            )

        await message.answer(staff_message, parse_mode="HTML")
        await state.finish()
        # Восстанавливаем session_locale после finish
        if user_locale:
            await state.update_data(session_locale=user_locale)
        return

    if client := await Client.get_client_by_phone(
        session=session,
        phone=phone_number
    ):
        if client.id != user.id:
            # try:
            #     user.gender = client.gender.decode("utf-8")
            # except:
            #     user.gender = client.gender
            # user.name = client.name
            # user.birthday_date = client.birthday_date
            user_id = user.id
            await session.delete(user)
            await session.commit()

            #user.phone_number = phone_number
            #await user.save(session)
            client.id = user_id
            await client.save(session)
            await start_handler(
                message=message,
                user=client,
                state=state,
                session=session
            )
        else:
            if user.phone_number != phone_number:
                user.phone_number = phone_number
                user.update_data = datetime.datetime.now()
                await user.save(session=session)

            #await authorization(user=user, bot=message.bot)
            await start_handler(
                message=message,
                user=user,
                state=state,
                session=session
            )
    elif not user.phone_number:
        await state.update_data(phone=phone_number)
        reg.state = "AuthClientState:waiting_name"
        reg.state_time = datetime.datetime.now()
        reg.state_data = await state.get_data()
        session.add(reg)
        await session.commit()
        await remove(message, 1)
        await message.answer(
            _("Чтобы зарегистрироваться в программе лояльности QR+, пожалуйста, "
              "ответьте на несколько вопросов. Это займёт не более минуты 😊")
        )

        await message.answer(
            _("Прежде чем начать, пожалуйста, ознакомьтесь с "
              "политикой конфиденциальности\nhttps://qazaqrepublic.com/ru/privacy и подтвердите согласие."
              "\n\nНажмите «Принять», чтобы продолжить.",),
            reply_markup=await get_universal_btn(_("Принять"), 'confirm')
        )


async def get_fio_handler(
        callback: CallbackQuery
        # user: Client,
        # session: AsyncSession,
        # state: FSMContext,
        # reg: RegTemp
):
    _ = callback.message.bot.get("i18n")
    await callback.message.delete()
    await callback.message.answer(
        _("Пожалуйста, укажите ваше ФИО:")
    )
    await AuthClientState.waiting_name.set()


async def get_years_handler(
        message: Message,
        user: Client,
        session: AsyncSession,
        state: FSMContext,
        reg: RegTemp
):
    _ = message.bot.get("i18n")
    await remove(message, 1)
    await message.delete()
    if not regex.fullmatch(r'^[\p{L}\s]+$', message.text):
        return await message.answer(
            text=_("ФИО не должно содержать цифры и символы, напишите ваше ФИО без цифр и символов")
        )
    if not reg.state_data.get('name'):
        await state.update_data(name=message.text)

    year = datetime.datetime.now().year
    await message.answer(
        text=_("Благодарим! Укажите дату рождения:"),
        reply_markup=await make_year_ikb(year)
    )
    await AuthClientState.waiting_birthday_date.set()
    reg.state = "AuthClientState:waiting_birthday_date"
    reg.state_time = datetime.datetime.now()
    reg.state_data = await state.get_data()
    session.add(reg)
    await session.commit()


async def auth_get_other_year_handler(
        query: CallbackQuery,
        user: Client,
        session: AsyncSession,
        state: FSMContext,
        callback_data: dict
):
    year = int(callback_data.get('id').split(',')[1])
    kb = await make_year_ikb(year)
    await query.message.edit_reply_markup(reply_markup=kb)


async def auth_birthday_date_handler(
        query: CallbackQuery,
        user: Client,
        session: AsyncSession,
        state: FSMContext,
        callback_data: dict
):
    _ = query.bot.get("i18n")
    year = int(callback_data.get('id'))
    month = datetime.datetime.now().month
    
    # ИЗМЕНЕНИЕ: Получаем язык из состояния FSM
    state_data = await state.get_data()
    user_locale = state_data.get('session_locale', 'rus') # 'rus' как запасной вариант
    
    await query.message.edit_text(
        text=_("Выберите вашу дату рождения"),
        reply_markup=await make_ikb_calendar(
            month_num=month,
            year_num=year,
            locale=user_locale  # ИЗМЕНЕНИЕ: Передаем язык в функцию
        )
    )


async def auth_get_other_month_handler(
        query: CallbackQuery,
        user: Client,
        session: AsyncSession,
        callback_data: dict,
        state: FSMContext # ИЗМЕНЕНИЕ: Добавляем state
):
    month = int(callback_data.get('id').split(',')[1])
    year = int(callback_data.get('id').split(',')[2])
    if not month:
        year -= 1
        month = 12
        
    # ИЗМЕНЕНИЕ: Получаем язык из состояния FSM
    state_data = await state.get_data()
    user_locale = state_data.get('session_locale', 'rus')
    
    kb = await make_ikb_calendar(
        month_num=month,
        year_num=year,
        locale=user_locale # ИЗМЕНЕНИЕ: Передаем язык в функцию
    )
    await query.message.edit_reply_markup(reply_markup=kb)


async def auth_gender_handler(
        query: CallbackQuery,
        user: Client,
        session: AsyncSession,
        state: FSMContext,
        callback_data: dict,
        reg: RegTemp
):
    _ = query.bot.get("i18n")
    if not reg.state_data.get('birthday'):
        birthday = callback_data.get('id').replace('date,', "")
        await state.update_data(birthday=birthday.replace(",", "."))
    # Текст на русском с переводом через .po файл
    await query.message.edit_text(
        text=_("Отлично! Пожалуйста, укажите пол:"),
        reply_markup=await get_genders_ikb(_)
    )
    await AuthClientState.waiting_gender.set()
    reg.state = "AuthClientState:waiting_gender"
    reg.state_time = datetime.datetime.now()
    reg.state_data = await state.get_data()
    session.add(reg)
    await session.commit()


async def auth_email_handler(
        query: CallbackQuery,
        user: Client,
        state: FSMContext,
        session: AsyncSession,
        callback_data: dict,
        reg: RegTemp
):
    _ = query.bot.get("i18n")
    await state.update_data(gender=callback_data.get('gender'))
    await query.message.delete()
    await query.message.answer(
        _("Остался последний шаг — укажите e-mail, чтобы получать напоминания о кэшбэке."),
        reply_markup=await get_universal_btn(_("Пропустить"), 'email')
    )
    await AuthClientState.waiting_email.set()
    reg.state = "AuthClientState.waiting_email"
    reg.state_time = datetime.datetime.now()
    reg.state_data = await state.get_data()
    session.add(reg)
    await session.commit()


async def auth_client_handler(
        message: Message | CallbackQuery,
        user: Client,
        state: FSMContext,
        session: AsyncSession,
        reg: RegTemp
):
    _ = message.bot.get("i18n")
    data = reg.state_data if reg and reg.state_data else {}
    
    # Логика для сообщения (ввод email)
    if isinstance(message, Message):
        await message.delete()
        if not is_mail_valid(message.text):
            await message.answer(
                _("📧 Похоже, email указан с ошибкой. Пример корректного адреса: test@example.com"),
                reply_markup=await get_universal_btn(_("Пропустить"), 'email')
            )
            return  # Прерываем выполнение, ждем следующего ввода
        user.email = message.text
    
    # Логика для кнопки (пропустить)
    if isinstance(message, CallbackQuery):
        user.email = "test@example.com"
        # Удаляем сообщение с кнопкой, чтобы не висело
        try:
            await message.message.delete()
        except:
            pass
        # Обновляем переменную message для передачи в start_handler
        message = message.message 

    # Безопасное получение данных
    user.phone_number = data.get('phone')
    user.name = data.get('name')
    user.gender = data.get('gender')
    
    # Безопасная обработка даты рождения
    birthday_str = data.get('birthday')
    if birthday_str:
        try:
            user.birthday_date = datetime.datetime.strptime(birthday_str, "%d.%m.%Y")
        except ValueError:
            logging.error(f"Ошибка формата даты рождения: {birthday_str}")
            user.birthday_date = datetime.datetime.now() # Fallback или обработка ошибки
    
    user.is_active = True
    user.activity = "telegram"
    
    # Сохраняем пользователя
    await user.save(session=session)
    
    # Удаляем временные данные регистрации
    if reg:
        await session.delete(reg)
    await session.commit()
    
    logging.info(f"Registration finished for user {user.id}. Sending welcome message via start_handler.")

    # Вызываем start_handler, который отправит Welcome message
    await start_handler(
        message=message,
        user=user,
        state=state,
        session=session,
        is_new_user=True  # Флаг, который отвечает за текст "Спасибо! Регистрация завершена..."
    )
