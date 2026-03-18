import datetime
import typing
import uuid

from sqlalchemy import (Column, Integer, BigInteger, ForeignKey, Text, DateTime,
                        func, String, Boolean, select, UUID, DECIMAL, True_, desc, asc, Date, and_, or_)
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.base import Base
from sqlalchemy.orm import relationship
from tgbot.models.database.purchases import ClientPurchase, ClientPurchaseReturn


class ClientBonusPoints(Base):
    __tablename__ = 'client_bonus_points'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    client_id = Column(
        BigInteger,
        ForeignKey("clients.id", onupdate='CASCADE', ondelete='CASCADE')
    )
    loyalty_program = Column(String)
    loyalty_program_id = Column(UUID(as_uuid=True))
    operation_date = Column(DateTime, default=func.now())
    source = Column(String)
    document_id = Column(UUID(as_uuid=True))
    document_type = Column(String)
    row_number = Column(BigInteger)
    accrued_points = Column(DECIMAL)
    write_off_points = Column(DECIMAL)
    created_at = Column(DateTime, default=func.now())
    update_at = Column(DateTime, default=func.now())
    activation_date: Column[datetime.datetime] = Column(DateTime,
                                                        default=datetime.datetime.now() + datetime.timedelta(days=14))
    expiration_date: Column[datetime.datetime] = Column(DateTime,
                                                        default=datetime.datetime.now() + datetime.timedelta(days=365))
    client_purchases_id = Column(
        String,
        ForeignKey("client_purchases.id", ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    client_purchases_return_id = Column(
        String,
        # ForeignKey("client_purchases_return.return_id", ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    #is_active = Column(Boolean)

    @classmethod
    async def get_by_client_id(
            cls,
            session: AsyncSession,
            client_id: int
    ) -> typing.Sequence['ClientBonusPoints']:
        stmt = select(ClientBonusPoints).where(
            (client_id == ClientBonusPoints.client_id) &
            (datetime.datetime.now().date() >= func.cast(ClientBonusPoints.activation_date, Date))
        ).order_by(asc(ClientBonusPoints.expiration_date))
        response = await session.execute(stmt)

        return response.scalars().all()

    @classmethod
    async def get_bonuses(
            cls,
            session: AsyncSession
    ) -> typing.Sequence['ClientBonusPoints']:
        stmt = select(ClientBonusPoints).where(
            (datetime.datetime.now().date() >= func.cast(ClientBonusPoints.activation_date, Date))
        ).order_by(asc(ClientBonusPoints.expiration_date))

        response = await session.execute(stmt)
        return response.scalars().all()

    @classmethod
    async def get_all_by_client_id(
            cls,
            session: AsyncSession,
            client_id: int
    ) -> typing.Sequence['ClientBonusPoints']:
        stmt = select(ClientBonusPoints).where(
            and_(
                client_id == ClientBonusPoints.client_id
                #datetime.datetime.now().date() <= func.cast(ClientBonusPoints.expiration_date, Date)
            )
        ).order_by(asc(ClientBonusPoints.expiration_date))
        response = await session.execute(stmt)

        return response.scalars().all()

    @classmethod
    async def get_history_with_details(
            cls,
            session: AsyncSession,
            client_id: int,
            limit: int = 5,
            offset: int = 0
    ):
        """
        Получает историю бонусов (только покупки, без возвратов).
        """
        stmt = select(
            ClientBonusPoints,
            ClientPurchase.ticket_print_url.label('purchase_ticket'),
            ClientPurchase.created_date.label('purchase_date')
        ).outerjoin(
            ClientPurchase,
            ClientBonusPoints.client_purchases_id == ClientPurchase.id
        ).where(
            and_(
                ClientBonusPoints.client_id == client_id,
                ClientBonusPoints.client_purchases_return_id.is_(None),  # Исключаем возвраты
                or_(
                    (ClientBonusPoints.accrued_points.isnot(None)) & (ClientBonusPoints.accrued_points > 0),
                    (ClientBonusPoints.write_off_points.isnot(None)) & (ClientBonusPoints.write_off_points > 0)
                )
            )
        ).order_by(
            desc(ClientBonusPoints.operation_date)
        ).limit(limit).offset(offset)

        response = await session.execute(stmt)
        return response.all()

    @classmethod
    async def get_history_count(
            cls,
            session: AsyncSession,
            client_id: int
    ) -> int:
        """Получает количество записей истории бонусов (без возвратов)."""
        from sqlalchemy import func as sql_func
        stmt = select(sql_func.count()).select_from(ClientBonusPoints).where(
            and_(
                ClientBonusPoints.client_id == client_id,
                ClientBonusPoints.client_purchases_return_id.is_(None),
                or_(
                    (ClientBonusPoints.accrued_points.isnot(None)) & (ClientBonusPoints.accrued_points > 0),
                    (ClientBonusPoints.write_off_points.isnot(None)) & (ClientBonusPoints.write_off_points > 0)
                )
            )
        )
        response = await session.execute(stmt)
        return response.scalar() or 0
    

class BonusExpirationNotifications(Base):
    __tablename__ = 'bonus_expiration_notifications'
    id = Column(UUID(as_uuid=True), primary_key=True)
    loyalty_program = Column(String)
    loyalty_program_id = Column(
        UUID(as_uuid=True)
    )
    notify_before_days = Column(BigInteger)
    message_template = Column(String)
    created_at = Column(DateTime, default=func.now())
    update_at = Column(DateTime, default=func.now())
