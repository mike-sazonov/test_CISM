from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.services.rabbit import RabbitProducer
from app.utils.unitofwork import UnitOfWork

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class MockRabbitProducer(RabbitProducer):
    async def publish(
        self, routing_key: str, message_body: dict[str, Any], priority: int
    ):
        pass


class UnitOfWorkTest(UnitOfWork):
    def __init__(self):
        super().__init__()
        self.session_factory = async_session_maker
