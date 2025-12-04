import typing
from datetime import datetime
from typing import Sequence, Optional
from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.purchases import ClientPurchase, ClientPurchaseReturn


async def get_all_purchases(
        session: AsyncSession,
        user_id: int
) -> Sequence['ClientPurchase']:
    stmt = select(ClientPurchase).where(
        user_id == ClientPurchase.user_id
    )
    response = await session.execute(stmt)

    return response.scalars().all()


async def get_purchases_by_month(
        session: AsyncSession,
        date: Optional[datetime],
        user_id: int
) -> Sequence['ClientPurchase']:
    stmt = select(ClientPurchase).where(
        (date.month == extract('month', ClientPurchase.created_date)) &
        (user_id == ClientPurchase.user_id)
    )
    response = await session.execute(stmt)

    return response.scalars().all()


async def is_return_purchases(
        session: AsyncSession,
        purchase_id: str,
        product_id: str,
        price: int
) -> bool:
    stmt = select(ClientPurchaseReturn).where(
        ClientPurchaseReturn.purchase_id == purchase_id
    )
    response = await session.execute(stmt)
    purchases = response.scalars().all()

    for purchase in purchases:
        products = purchase.products
        for product in products:
            if product['id'] == product_id and product['price'] == price:
                return True

    return False


async def get_return_client_purchases(
        session: AsyncSession,
        purchase_id: str
) -> typing.Sequence[ClientPurchaseReturn]:
    stmt = select(ClientPurchaseReturn).where(
        ClientPurchaseReturn.purchase_id == purchase_id
    )
    response = await session.execute(stmt)
    purchases = response.scalars().all()

    return purchases
