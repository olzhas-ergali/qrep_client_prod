from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from tgbot.handlers.client import faq, show_purchases, main
from tgbot.keyboards import query_cb
from tgbot.misc.states.client import FaqState


def register_faq_function(dp: Dispatcher):
    dp.register_callback_query_handler(
        faq.main.faq_lvl_handler,
        query_cb.FaqCallback.filter(action='faq'),
        state="*"
    )

    dp.register_callback_query_handler(
        faq.mailing.mailing_handler,
        query_cb.FaqCallback.filter(action='faq_mailings'),
        state="*"
    )

    # dp.register_message_handler(
    #     faq.operator.operator_handler,
    #     text='55',
    #     state=FaqState.waiting_operator
    # )

    dp.register_callback_query_handler(
        faq.operator.send_operator_handler,
        query_cb.FaqCallback.filter(action='faq_time'),
        state=FaqState.waiting_operator
    )

    dp.register_callback_query_handler(
        faq.operator.user_wait_answer_handler,
        query_cb.AnswerCallback.filter(action='user_answer'),
        state="*"
    )

    dp.register_callback_query_handler(
        faq.operator.user_graded_handler,
        query_cb.AnswerCallback.filter(action='user_grade'),
        state="*"
    )

    dp.register_callback_query_handler(
        main.get_my_bonus_handler,
        query_cb.FaqCallback.filter(action='client', lvl='bonus'),
        state='*'
    )

    dp.register_callback_query_handler(
        main.get_my_qr_handler,
        query_cb.FaqCallback.filter(action='client', lvl='qr'),
        state='*'
    )

    dp.register_callback_query_handler(
        show_purchases.purchases_handler,
        query_cb.FaqCallback.filter(action='client', lvl='purchase'),
        state='*'
    )

    dp.register_callback_query_handler(
        faq.main.choose_locale_handler,
        query_cb.LocalCallback.filter(action='change_local'),
        state='*'
    )

    dp.register_callback_query_handler(
        faq.main.change_locale_handler,
        query_cb.LocalCallback.filter(action='client_locale'),
        state='*'
    )
