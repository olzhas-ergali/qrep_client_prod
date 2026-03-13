import typing

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

_Base = declarative_base()


class Base(_Base):
    __abstract__ = True

    async def save(self, session: AsyncSession):
        session.add(self)
        await session.commit()

        return self


class Database:
    def __init__(self):
        self.pool: typing.Optional[sessionmaker] = None
        self.engine: typing.Optional[AsyncEngine] = None

    async def create_pool(self, connection_uri = "postgresql+asyncpg://postgres:postgres@localhost/postgres",
                          drop_table: bool = False):
        engine = create_async_engine(url=make_url(connection_uri))
        self.engine = engine
        if drop_table:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        pool = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
        self.pool = pool


