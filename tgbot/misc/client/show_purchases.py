import logging
from datetime import datetime
from typing import List
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.comands.client_purchases import (get_all_purchases,
                                                           get_purchases_by_month, is_return_purchases, get_return_client_purchases)

logger = logging.getLogger(__name__)

async def show_purchases(
        session: AsyncSession,
        user_id: int,
        date: datetime = None,
) -> List[str]:
    bot = Bot.get_current()
    _ = bot.get('i18n')  # Получаем функцию перевода напрямую
    
    logger.info(f"🛒 SHOW_PURCHASES: Начинаем формирование покупок для пользователя {user_id}")
    logger.info(f"🛒 SHOW_PURCHASES: Функция перевода получена: {type(_)}")
    
    all_text = []
    text = ""  # Инициализируем переменную text
    if date is not None:
        purchases = await get_purchases_by_month(
            session=session,
            date=date,
            user_id=user_id
        )
    else:
        purchases = await get_all_purchases(
            session=session,
            user_id=user_id
        )

    if purchases:
        logger.info(f"🛒 SHOW_PURCHASES: Найдено {len(purchases)} покупок")
        for purchase in purchases:
            products = purchase.products
            logger.info(f"🛒 SHOW_PURCHASES: Обрабатываем покупку {purchase.id} с {len(products)} товарами")
            
            purchase_return = await get_return_client_purchases(
                session=session,
                purchase_id=purchase.id
            )
            return_products = []
            dates = []
            if purchase_return:
                for r in purchase_return:
                    for product in r.products:
                        return_products.append(product.get('id'))
                        dates.append(r.created_date)
            for product in products:
                # is_return = await is_return_purchases(
                #     session=session,
                #     purchase_id=purchase.id,
                #     product_id=product['id'],
                #     price=product.get('price') - product.get('discountPrice')
                # )
                #if not is_return:

                if len(text) > 3500:
                    logger.info(f"🛒 SHOW_PURCHASES: Текст превысил лимит, добавляем в список (длина: {len(text)})")
                    all_text.append(text)
                    text = ""
                    
                # Тестируем функцию перевода
                try:
                    translated_text = _("Название товара: {name}\nКоличество: {count}\n").format(
                        name=product['name'], 
                        count=product['count']
                    )
                    logger.info(f"🛒 SHOW_PURCHASES: Перевод успешен для товара {product['name']}")
                    text += translated_text
                except Exception as e:
                    logger.error(f"🛒 SHOW_PURCHASES: Ошибка перевода: {e}")
                    # Fallback на русский текст
                    text += f"Название товара: {product['name']}\nКоличество: {product['count']}\n"
                if product['discount']:
                    total = int(product['price'] - (product['price'] * (product['discountPercent'] / 100)))
                    text += _(
                        "Цена: {price}\n"
                        "Скидка: {discountPercent}%\n"
                        "Итог скидки: {total}\n"
                        "Итого с учетом скидки: {totalDiscount}"
                    ).format(
                        price=product['price'],
                        discountPercent=product['discountPercent'],
                        total=product['price'] - total,
                        totalDiscount=int(product['price'] - (product['price'] * (product['discountPercent'] / 100)))
                    )
                else:
                    text += _("Цена: {price}\n").format(price=product['price'])
                if product['id'] not in return_products:
                    text += _("Дата покупки: {created_date}\nСсылка на чек: {ticket_print_url}\n\n").format(
                        created_date=str(purchase.created_date).split(' ')[0],
                        ticket_print_url=purchase.ticket_print_url
                    )
                else:
                    index = return_products.index(product['id'])
                    text += _("Дата покупки: {created_date}\nДата возврата: {return_date}\n\n").format(
                        created_date=str(purchase.created_date).split(' ')[0],
                        return_date=str(dates[index]).split(' ')[0]
                    )
                    return_products.pop(index)
                    dates.pop(index)

    else:
        logger.info("🛒 SHOW_PURCHASES: Покупки не найдены")
        
    if text != "":
        logger.info(f"🛒 SHOW_PURCHASES: Добавляем финальный текст (длина: {len(text)})")
        all_text.append(text)
        
    logger.info(f"🛒 SHOW_PURCHASES: Возвращаем {len(all_text)} текстовых блоков")
    return all_text
