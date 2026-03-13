from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from tgbot.handlers import client
from tgbot.keyboards import query_cb
from tgbot.misc.states.client import NotificationState
from tgbot.handlers.client.faq.register import register_faq_function


def register_client_function(dp: Dispatcher):
    register_faq_function(dp)

    # dp.register_message_handler(
    #     client.main.get_my_qr_handler,
    #     text='Мой QR',
    #     is_client_auth=True,
    #     state="*"
    # )
    #
    # dp.register_message_handler(
    #     client.main.get_my_bonus_handler,
    #     text='Мои бонусы',
    #     is_client_auth=True,
    #     state="*"
    # )

    # dp.register_message_handler(
    #     client.faq.get_faq_handler,
    #     text='FAQ',
    #     is_client_auth=True,
    #     state="*"
    # )

    dp.register_callback_query_handler(
        client.reveiw.review_handler,
        query_cb.ReviewCallback.filter(action='review'),
        state="*"
    )

    dp.register_message_handler(
        client.reveiw.get_client_review_handler,
        state=NotificationState.waiting_review
    )

    dp.register_message_handler(
        client.show_purchases.purchases_handler,
        text='Мои покупки',
        state="*"
    )

    dp.register_callback_query_handler(
        client.show_purchases.all_purchases_handler,
        query_cb.ChoiceCallback.filter(action='client_purchases', choice='by_all'),
        state="*"
    )

    dp.register_callback_query_handler(
        client.show_purchases.purchases_by_date_handler,
        query_cb.ChoiceCallback.filter(action='client_purchases', choice='by_month'),
        state="*"
    )

