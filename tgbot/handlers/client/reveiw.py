import logging
import os
import segno
import datetime

from aiogram.types.message import Message, ContentType
from aiogram.types.callback_query import CallbackQuery
from aiogram.dispatcher.storage import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.users import Client, ClientReview, StaffReview
from tgbot.misc.states.client import NotificationState
from tgbot.keyboards.client.client import main_btns
from tgbot.misc.delete import remove
from tgbot.misc.state_helpers import clear_state_but_preserve_locale

logger = logging.getLogger(__name__)


async def review_handler(
        callback_query: CallbackQuery,
        user: Client,
        state: FSMContext,
        session: AsyncSession,
        callback_data: dict
):
    try:
        await callback_query.answer()
    except Exception:
        logger.exception("[review] callback_query.answer failed")

    _ = callback_query.bot.get('i18n')

    try:
        await clear_state_but_preserve_locale(state)
    except Exception:
        logger.exception("[review] clear_state failed")

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

    active_bot_type = callback_query.bot.get('active_bot_type', 'client')
    if active_bot_type == "staff":
        review = StaffReview()
        review.staff_id = user.id
        review.staff_review = "-"
        review.staff_grade = grade
        review.staff_grade_str = grades.get(grade)
        review_table = "staff"
    else:
        review = ClientReview()
        review.client_id = user.id
        review.client_review = "-"
        review.client_grade = grade
        review.client_grade_str = grades.get(grade)
        review_table = "client"

    session.add(review)
    await session.commit()
    await state.update_data(review_id=review.id, review_table=review_table)
    try:
        await callback_query.message.edit_text(text=text)
    except Exception:
        logger.exception("[review] edit_text failed, sending new message")
        await callback_query.message.answer(text=text)
    await NotificationState.waiting_review.set()


async def get_client_review_handler(
        message: Message,
        session: AsyncSession,
        state: FSMContext
):
    _ = message.bot.get('i18n')
    data = await state.get_data()

    review_table = data.get('review_table', 'client')
    review_id = int(data.get('review_id'))

    if review_table == "staff":
        review = await StaffReview.get_review_by_id(
            session=session,
            review_id=review_id
        )
        if review:
            review.staff_review = message.text
            session.add(review)
    else:
        review = await ClientReview.get_review_by_id(
            session=session,
            review_id=review_id
        )
        if review:
            review.client_review = message.text
            session.add(review)
    await session.commit()
    await message.delete()
    await remove(message, 1)
    
    await message.answer(
        text=_('''Спасибо за покупку! Ваши отзывы важны для улучшения нашей команды Qazaq Republic.
В случае если ваш отзыв требует ответа, мы свяжемся с вами в ближайшее время.'''),
        reply_markup=await main_btns(_)
    )
    
    await clear_state_but_preserve_locale(state)

