import datetime
import typing
from sqlalchemy import (BigInteger, Column, String, select, Date,
                        DateTime, func, Integer, ForeignKey, Boolean, update,
                        desc, not_, VARCHAR, Text, CHAR, JSON, DECIMAL)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from tgbot.models.database.base import Base

from sqlalchemy import UUID


class User(Base):
    __tablename__ = "users"
    # --- Поля, которые есть в БД ---
    id = Column(BigInteger, primary_key=True) # bigserial в SQLAlchemy это BigInteger с autoincrement=True, что по умолчанию для primary_key
    phone_number = Column(String, unique=True, default=None)
    created_at = Column(DateTime, server_default=func.now())
    author = Column(String, default=None)
    local = Column(String, default="rus")
    staff_id = Column(UUID(as_uuid=True), default=None) # uuid
    login_tg = Column(String, default=None)
    update_date = Column(DateTime, default=None, onupdate=datetime.datetime.now) # timestamp

    # --- Поля, которых нет в БД, но могут быть нужны для логики (пока закомментируем) ---
    # name = Column(String)
    # fullname = Column(String)
    # iin = Column(String, unique=True, default=None)
    # date_receipt = Column(DateTime)
    # date_dismissal = Column(DateTime)
    # is_active = Column(Boolean, default=False)
    # is_admin = Column(Boolean, default=False)
    # position_name = Column(String, default=None)
    # position_id = Column(String, default=None)
    # organization_name = Column(String, default=None)
    # organization_bin = Column(String, default=None)
    # organization_id = Column(String, default=None)
    
    # Остальные методы класса User оставляем как есть
    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: int) -> 'User':
        stmt = select(User).where(user_id == User.id)
        return await session.scalar(stmt)

    @classmethod
    async def get_by_phone(cls, session: AsyncSession, phone: str) -> 'User':
        stmt = select(User).where(phone == User.phone_number)
        return await session.scalar(stmt)
        
    # Метод get_by_iin теперь не нужен, так как поля нет
    # @classmethod
    # async def get_by_iin(cls, session: AsyncSession, iin: str) -> 'User':
    #     stmt = select(User).where(iin == User.iin)
    #     return await session.scalar(stmt)

    # Метод get_mention нужно адаптировать, так как поля name больше нет
    def get_mention(self, name=None):
        # Используем login_tg или id, если имени нет
        display_name = name or self.login_tg or str(self.id)
        return f"<a href='tg://user?id={self.id}'>{display_name}</a>"

class UserTemp(Base):
    __tablename__ = "users_temp"
    id_staff = Column(String, primary_key=True, unique=True)
    phone_number = Column(String, default=None)
    iin = Column(String)
    name = Column(String)
    author = Column(String)
    date_receipt = Column(DateTime)
    date_dismissal = Column(DateTime, default=None)
    created_at = Column(DateTime, server_default=func.now())
    update_data = Column(DateTime)
    is_fired = Column(Boolean, default=False)
    position_name = Column(String, default=False)
    position_id = Column(String, default=False)
    organization_name = Column(String, default=False)
    organization_bin = Column(String, default=False)
    organization_id = Column(String, default=False)

    @classmethod
    async def get_user_temp(
            cls,
            session: AsyncSession,
            iin: str,
    ) -> 'UserTemp':

        stmt = select(UserTemp).where(
            (iin == UserTemp.iin) & not_(UserTemp.is_fired)
        ).order_by(desc(UserTemp.created_at)).limit(1)

        return await session.scalar(stmt)


class PositionDiscounts(Base):
    __tablename__ = "position_discounts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    position_id = Column(
        String
    )
    position_name = Column(
        String
    )
    discount_percentage = Column(DECIMAL)
    created_at = Column(DateTime, server_default=func.now())
    update_data = Column(DateTime, default=None)
    is_active = Column(Boolean, default=True)
    description = Column(String, default=None)
    start_date = Column(DateTime, default=None)
    end_date = Column(DateTime, default=None)
    monthly_limit = Column(BigInteger)


class Client(Base):
    __tablename__ = "clients"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # whatsapp_id = Column(VARCHAR(36))
    name = Column(String)
    fullname = Column(String)
    phone_number = Column(String, unique=True, default=None)
    gender = Column(CHAR)
    birthday_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    update_data = Column(DateTime, default=None)
    is_active = Column(Boolean, default=False)
    source = Column(String)
    email = Column(String)
    activity = Column(String, default="telegram")
    local = Column(String, default="rus")

    @classmethod
    async def get_client_by_phone(
            cls,
            session: AsyncSession,
            phone: str
    ) -> 'Client':
        stmt = select(Client).where(
            phone == Client.phone_number
        )

        return await session.scalar(stmt)


class ClientReview(Base):
    __tablename__ = "clients_review"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(
        BigInteger,
        ForeignKey('clients.id', ondelete='CASCADE', onupdate='CASCADE')
    )
    client_review = Column(
        Text
    )
    client_grade = Column(
        Integer
    )
    client_grade_str = Column(
        String
    )
    created_at = Column(DateTime, server_default=func.now())
    clients = relationship(
        'Client',
        foreign_keys=[client_id],
        uselist=True,
        lazy='selectin'
    )

    @classmethod
    async def get_review_by_id(
            cls,
            session: AsyncSession,
            review_id: int
    ) -> 'ClientReview':
        stmt = select(ClientReview).where(
            review_id == ClientReview.id
        )

        return await session.scalar(stmt)


class RegTemp(Base):
    __tablename__ = "reg_temp"
    telegram_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    state = Column(
        String
    )
    state_time = Column(
        DateTime, server_default=func.now()
    )
    state_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class ClientMailing(Base):
    __tablename__ = "clients_mailing"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now())
    telegram_id = Column(
        BigInteger, default=None
    )
    phone = Column(
        String, default=None
    )


class ClientsApp(Base):
    __tablename__ = "clients_app"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now())
    waiting_time = Column(DateTime)
    is_push = Column(Boolean, default=False)
    telegram_id = Column(
        BigInteger,
        default=None
    )
    phone_number = Column(
        String,
        default=None
    )

    @classmethod
    async def get_last_app(
            cls,
            session: AsyncSession,
            telegram_id: int
    ):
        stmt = select(ClientsApp).where((telegram_id == ClientsApp.telegram_id) & (ClientsApp.is_push != True))

        return await session.scalar(stmt)

    @classmethod
    async def get_last_app_by_phone(
            cls,
            session: AsyncSession,
            phone: str
    ):
        stmt = select(ClientsApp).where((phone == ClientsApp.phone_number) & (ClientsApp.is_push != True))

        return await session.scalar(stmt)
