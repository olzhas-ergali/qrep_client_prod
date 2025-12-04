from datetime import datetime
from typing import Sequence, Optional
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from service.tgbot.models.database.purchases import Purchase, PurchaseReturn


async def get_all_purchases(
        session: AsyncSession,
        user_id: int
) -> Sequence['Purchase']:
    stmt = select(Purchase).where(
        user_id == Purchase.user_id
    )
    response = await session.execute(stmt)

    return response.scalars().all()


async def get_purchases_by_month(
        session: AsyncSession,
        date: Optional[datetime],
        user_id: int
) -> Sequence['Purchase']:
    stmt = select(Purchase).where(
        (date.month == extract('month', Purchase.created_date)) &
        (date.year == extract('year', Purchase.created_date)) &
        (user_id == Purchase.user_id)
    )
    response = await session.execute(stmt)

    return response.scalars().all()


async def is_return_purchases(
        session: AsyncSession,
        purchase_id: str,
        product_id: str,
        price: int
) -> bool:
    stmt = select(PurchaseReturn).where(
        PurchaseReturn.purchase_id == purchase_id
    )
    response = await session.execute(stmt)
    purchases = response.scalars().all()

    for purchase in purchases:
        products = purchase.products
        for product in products:
            if product['id'] == product_id and product['price'] == price:
                return True

    return False
