import os
import segno
import datetime

from aiogram.types.message import Message, ContentType
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import Client, ClientReview
from tgbot.misc.states.client import NotificationState
from tgbot.keyboards.client.client import main_btns
from tgbot.misc.delete import remove
from tgbot.misc.state_helpers import clear_state_but_preserve_locale


async def review_handler(
        callback_query: CallbackQuery,
        user: Client,
        state: FSMContext,
        session: AsyncSession,
        callback_data: dict
):
    _ = callback_query.bot.get('i18n')
    
    await clear_state_but_preserve_locale(state)

    grade = int(callback_data.get('grade'))
    text = _("Рахмет! Расскажите, пожалуйста, почему поставили такую оценку? "
             "Что нам стоит улучшить? Если обратной связи нет, просто ответьте '-'")
    grades = {
        1: _('Очень плохо'),
        2: _('Плохо'),
        3: _('Удовлетворительно'),
        4: _('Хорошо'),
        5: _('Отлично'),
    }

    c = ClientReview()
    c.client_id = user.id
    c.client_review = "-"
    c.client_grade = grade
    c.client_grade_str = grades.get(grade)
    session.add(c)
    await session.commit()
    await state.update_data(review_id=c.id)
    await callback_query.message.edit_text(
        text=text,
    )
    await NotificationState.waiting_review.set()


async def get_client_review_handler(
        message: Message,
        session: AsyncSession,
        state: FSMContext
):
    _ = message.bot.get('i18n')
    data = await state.get_data()

    c = await ClientReview.get_review_by_id(
        session=session,
        review_id=int(data.get('review_id'))
    )
    c.client_review = message.text
    session.add(c)
    await session.commit()
    await message.delete()
    await remove(message, 1)
    
    await message.answer(
        text=_('''Спасибо за покупку! Ваши отзывы важны для улучшения нашей команды Qazaq Republic.
В случае если ваш отзыв требует ответа, мы свяжемся с вами в ближайшее время.'''),
        reply_markup=await main_btns()
    )
    
    await clear_state_but_preserve_locale(state)

