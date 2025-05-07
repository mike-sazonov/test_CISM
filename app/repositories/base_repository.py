from abc import ABC, abstractmethod

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):
    @abstractmethod
    async def add_one(self, data: dict):
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict):
        stmt = insert(self.model).values(**data).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def find_one(self, **filter_by):
        stmt = select(self.model).filter_by(**filter_by)
        res = await self.session.execute(stmt)
        res = res.scalar_one_or_none()
        return res

    async def find_all(self):
        res = await self.session.execute(select(self.model))
        return res.scalars().all()

    async def update_one(self, params: dict, **filter_by):
        stmt = update(self.model).values(**params).filter_by(**filter_by).returning(self.model)
        await self.session.execute(stmt)
